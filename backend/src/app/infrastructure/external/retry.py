from __future__ import annotations

import email.utils
import random
import time
from collections.abc import Callable
from datetime import UTC, datetime

import httpx

from app.domain.exceptions import (
    CatalogBlockedError,
    CatalogRateLimitedError,
    CatalogRequestError,
    CatalogTransientError,
)


def parse_retry_after(value: str | None, *, fallback_seconds: float = 1.0) -> float:
    """Parse Retry-After header as seconds (int) or HTTP-date."""
    if value is None or not value.strip():
        return max(fallback_seconds, 0.0)

    raw = value.strip()
    if raw.isdigit():
        return max(float(raw), 0.0)

    try:
        parsed = email.utils.parsedate_to_datetime(raw)
    except (TypeError, ValueError, IndexError):
        return max(fallback_seconds, 0.0)

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    delay = (parsed - datetime.now(UTC)).total_seconds()
    return max(delay, 0.0)


def parse_blocked_retry_after(
    response: httpx.Response, *, default_seconds: float = 1800.0
) -> float:
    """Resolve unblock delay from Retry-After header or known JSON body fields."""
    header_value = response.headers.get("Retry-After")
    if header_value:
        return parse_retry_after(header_value, fallback_seconds=default_seconds)

    try:
        payload = response.json()
    except ValueError:
        return default_seconds

    if not isinstance(payload, dict):
        return default_seconds

    for key in ("retry_after", "retryAfter", "unblock_in", "blocked_for"):
        if key in payload:
            try:
                return max(float(payload[key]), 0.0)
            except (TypeError, ValueError):
                continue

    for key in ("unblock_at", "blocked_until", "unblockAt", "blockedUntil"):
        if key not in payload:
            continue
        raw = payload[key]
        if isinstance(raw, (int, float)):
            # Unix timestamp
            delay = float(raw) - time.time()
            return max(delay, 0.0)
        if isinstance(raw, str):
            try:
                parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            except ValueError:
                delay = parse_retry_after(raw, fallback_seconds=default_seconds)
                return delay
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=UTC)
            return max((parsed - datetime.now(UTC)).total_seconds(), 0.0)

    return default_seconds


def compute_backoff_seconds(
    attempt: int,
    *,
    base_seconds: float = 0.5,
    max_seconds: float = 30.0,
    jitter_ratio: float = 0.2,
) -> float:
    """Exponential backoff with jitter for transient errors."""
    delay = min(max_seconds, base_seconds * (2**attempt))
    jitter = delay * jitter_ratio * random.random()  # noqa: S311 - non-crypto jitter
    return delay + jitter


def with_retries[T](
    operation: Callable[[], T],
    *,
    max_attempts: int,
    sleep: Callable[[float], None] = time.sleep,
    on_rate_limit: Callable[[float], None] | None = None,
) -> T:
    """
    Execute ``operation`` with retries.

    - CatalogRateLimitedError: sleep Retry-After and retry
    - CatalogTransientError / httpx transport errors wrapped by operation: backoff + retry
    - CatalogBlockedError / CatalogRequestError: propagate immediately
    """
    if max_attempts < 1:
        raise ValueError("max_attempts must be >= 1")

    last_error: Exception | None = None
    for attempt in range(max_attempts):
        try:
            return operation()
        except CatalogBlockedError:
            raise
        except CatalogRequestError:
            raise
        except CatalogRateLimitedError as exc:
            last_error = exc
            if attempt >= max_attempts - 1:
                break
            if on_rate_limit is not None:
                on_rate_limit(exc.retry_after_seconds)
            sleep(exc.retry_after_seconds)
        except CatalogTransientError as exc:
            last_error = exc
            if attempt >= max_attempts - 1:
                break
            sleep(compute_backoff_seconds(attempt))

    assert last_error is not None
    raise CatalogTransientError(
        f"Retries exhausted after {max_attempts} attempts: {last_error}"
    ) from last_error
