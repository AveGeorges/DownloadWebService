from __future__ import annotations

import logging
import time
from collections.abc import Callable, Sequence
from typing import Any

import httpx

from app.application.services.chunking import MAX_DOWNLOAD_BATCH
from app.domain.exceptions import (
    CatalogBlockedError,
    CatalogRateLimitedError,
    CatalogRequestError,
    CatalogTransientError,
)
from app.infrastructure.external.retry import (
    parse_blocked_retry_after,
    parse_retry_after,
    with_retries,
)

logger = logging.getLogger(__name__)


class ExternalCatalogClient:
    """HTTP adapter for the external file catalog API."""

    def __init__(
        self,
        *,
        base_url: str,
        candidate_id: str,
        timeout_seconds: float = 30.0,
        max_attempts: int = 5,
        min_interval_seconds: float = 1.5,
        transport: httpx.BaseTransport | None = None,
        client: httpx.Client | None = None,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._candidate_id = candidate_id
        self._max_attempts = max_attempts
        self._base_min_interval_seconds = max(0.0, min_interval_seconds)
        self._min_interval_seconds = self._base_min_interval_seconds
        self._sleep = sleep
        self._clock = clock
        self._last_request_at = 0.0
        self._cooldown_until = 0.0
        self._owns_client = client is None
        self._client = client or httpx.Client(
            base_url=self._base_url,
            timeout=timeout_seconds,
            headers={"X-Candidate-Id": candidate_id, "Accept": "application/json"},
            transport=transport,
        )

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> ExternalCatalogClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def list_names(self) -> list[str]:
        def _call() -> list[str]:
            response = self._request("GET", "/api/files/names")
            self._raise_for_status(response)
            return self._parse_names_payload(response.json())

        return with_retries(_call, max_attempts=self._max_attempts, sleep=self._sleep)

    def download(self, names: Sequence[str]) -> bytes:
        batch = list(names)
        if not batch:
            raise CatalogRequestError("download requires at least one filename")
        if len(batch) > MAX_DOWNLOAD_BATCH:
            raise CatalogRequestError(
                f"download accepts at most {MAX_DOWNLOAD_BATCH} names, got {len(batch)}"
            )

        def _call() -> bytes:
            response = self._request(
                "POST",
                "/api/files/download",
                json={"file_names": batch},
                headers={"Accept": "application/zip, application/octet-stream"},
            )
            self._raise_for_status(response)
            return response.content

        return with_retries(_call, max_attempts=self._max_attempts, sleep=self._sleep)

    def mark_downloaded(self, names: Sequence[str]) -> None:
        batch = list(names)
        if not batch:
            raise CatalogRequestError("mark_downloaded requires at least one filename")

        def _call() -> None:
            response = self._request(
                "POST",
                "/api/files/downloaded",
                json={"file_names": batch},
            )
            self._raise_for_status(response)

        with_retries(_call, max_attempts=self._max_attempts, sleep=self._sleep)

    def _pace(self) -> None:
        """Space out calls so the external API is less likely to return 429/403."""
        now = self._clock()
        earliest = max(self._cooldown_until, self._last_request_at + self._min_interval_seconds)
        delay = earliest - now
        if delay > 0:
            self._sleep(delay)
            now = self._clock()
        self._last_request_at = now

    def _request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        self._pace()
        try:
            return self._client.request(method, url, **kwargs)
        except httpx.TimeoutException as exc:
            raise CatalogTransientError(f"Catalog API timeout: {exc}") from exc
        except httpx.TransportError as exc:
            raise CatalogTransientError(f"Catalog API transport error: {exc}") from exc

    def _raise_for_status(self, response: httpx.Response) -> None:
        if response.status_code < 400:
            return

        if response.status_code == 429:
            delay = parse_retry_after(response.headers.get("Retry-After"), fallback_seconds=1.0)
            # Keep pacing quiet after a rate-limit window ends.
            self._cooldown_until = max(self._cooldown_until, self._clock() + delay)
            # Temporarily slow down further successful traffic.
            self._min_interval_seconds = max(
                self._base_min_interval_seconds,
                min(max(delay, self._min_interval_seconds), 5.0),
            )
            logger.warning(
                "Catalog rate limited (429)",
                extra={"retry_after_seconds": delay, "status_code": 429},
            )
            raise CatalogRateLimitedError(
                "Catalog API rate limited",
                retry_after_seconds=delay,
            )

        if response.status_code == 403:
            delay = parse_blocked_retry_after(response, default_seconds=1800.0)
            logger.error(
                "Catalog blocked (403)",
                extra={"retry_after_seconds": delay, "status_code": 403},
            )
            raise CatalogBlockedError(
                "Catalog API blocked the client",
                retry_after_seconds=delay,
            )

        if response.status_code >= 500:
            raise CatalogTransientError(f"Catalog API server error: HTTP {response.status_code}")

        if response.status_code in {408, 425}:
            raise CatalogTransientError(
                f"Catalog API transient client error: HTTP {response.status_code}"
            )

        raise CatalogRequestError(
            f"Catalog API request failed: HTTP {response.status_code}: {response.text[:300]}"
        )

    @staticmethod
    def _parse_names_payload(payload: Any) -> list[str]:
        """Parse FileNamesResponse; keep a few legacy shapes for tests/mocks."""
        if payload is None:
            return []
        if isinstance(payload, list):
            return [str(item) for item in payload]
        if isinstance(payload, dict):
            for key in ("file_names", "names", "files", "data"):
                value = payload.get(key)
                if value is None:
                    continue
                if isinstance(value, list):
                    return [str(item) for item in value]
            raise CatalogRequestError(f"Unexpected names payload keys: {sorted(payload)}")
        raise CatalogRequestError(f"Unexpected names payload type: {type(payload)!r}")
