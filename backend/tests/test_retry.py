from datetime import UTC, datetime, timedelta

import httpx
import pytest

from app.domain.exceptions import (
    CatalogBlockedError,
    CatalogRateLimitedError,
    CatalogRequestError,
    CatalogTransientError,
)
from app.infrastructure.external.retry import (
    compute_backoff_seconds,
    parse_blocked_retry_after,
    parse_retry_after,
    with_retries,
)


def test_parse_retry_after_seconds() -> None:
    assert parse_retry_after("3") == 3.0


def test_parse_retry_after_http_date() -> None:
    future = datetime.now(UTC) + timedelta(seconds=5)
    header = future.strftime("%a, %d %b %Y %H:%M:%S GMT")
    delay = parse_retry_after(header)
    assert 0.0 <= delay <= 6.0


def test_parse_blocked_retry_after_from_json_body() -> None:
    response = httpx.Response(403, json={"retry_after": 120})
    assert parse_blocked_retry_after(response) == 120.0


def test_compute_backoff_increases() -> None:
    first = compute_backoff_seconds(0, base_seconds=1.0, max_seconds=100.0, jitter_ratio=0.0)
    second = compute_backoff_seconds(1, base_seconds=1.0, max_seconds=100.0, jitter_ratio=0.0)
    assert first == 1.0
    assert second == 2.0


def test_with_retries_respects_rate_limit() -> None:
    sleeps: list[float] = []
    calls = {"n": 0}

    def operation() -> str:
        calls["n"] += 1
        if calls["n"] == 1:
            raise CatalogRateLimitedError("slow down", retry_after_seconds=2.5)
        return "ok"

    result = with_retries(operation, max_attempts=3, sleep=sleeps.append)
    assert result == "ok"
    assert sleeps == [2.5]


def test_with_retries_does_not_retry_blocked() -> None:
    def operation() -> None:
        raise CatalogBlockedError("blocked", retry_after_seconds=30)

    with pytest.raises(CatalogBlockedError):
        with_retries(operation, max_attempts=5, sleep=lambda _: None)


def test_with_retries_does_not_retry_request_error() -> None:
    def operation() -> None:
        raise CatalogRequestError("bad request")

    with pytest.raises(CatalogRequestError):
        with_retries(operation, max_attempts=5, sleep=lambda _: None)


def test_with_retries_exhausts_transient() -> None:
    def operation() -> None:
        raise CatalogTransientError("boom")

    with pytest.raises(CatalogTransientError, match="Retries exhausted"):
        with_retries(operation, max_attempts=2, sleep=lambda _: None)
