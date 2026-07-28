import json

import httpx
import pytest

from app.domain.exceptions import (
    CatalogBlockedError,
    CatalogRequestError,
    CatalogTransientError,
)
from app.infrastructure.external.catalog_client import ExternalCatalogClient


def _client_with_handler(
    handler: httpx.MockTransport,
    *,
    min_interval_seconds: float = 0.0,
    sleep=None,
    clock=None,
) -> ExternalCatalogClient:
    kwargs: dict = {
        "base_url": "https://catalog.test",
        "candidate_id": "candidate-1",
        "max_attempts": 3,
        "min_interval_seconds": min_interval_seconds,
        "transport": handler,
    }
    if sleep is not None:
        kwargs["sleep"] = sleep
    if clock is not None:
        kwargs["clock"] = clock
    return ExternalCatalogClient(**kwargs)


def test_list_names_parses_list_payload() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/files/names"
        assert request.headers["X-Candidate-Id"] == "candidate-1"
        return httpx.Response(200, json=["a.txt", "b.txt"])

    with _client_with_handler(httpx.MockTransport(handler)) as client:
        assert client.list_names() == ["a.txt", "b.txt"]


def test_list_names_parses_file_names_response_and_empty() -> None:
    payloads = [{"file_names": ["one.txt"]}, {"file_names": []}]

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payloads.pop(0))

    with _client_with_handler(httpx.MockTransport(handler)) as client:
        assert client.list_names() == ["one.txt"]
        assert client.list_names() == []


def test_list_names_retries_on_429_then_succeeds() -> None:
    calls = {"n": 0}

    def handler(_request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(429, headers={"Retry-After": "0"})
        return httpx.Response(200, json={"file_names": ["x.txt"]})

    with _client_with_handler(httpx.MockTransport(handler)) as client:
        assert client.list_names() == ["x.txt"]
    assert calls["n"] == 2


def test_list_names_raises_blocked_on_403() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            403,
            headers={"Retry-After": "60"},
            json={"detail": "blocked"},
        )

    with (
        _client_with_handler(httpx.MockTransport(handler)) as client,
        pytest.raises(CatalogBlockedError) as exc_info,
    ):
        client.list_names()
    assert exc_info.value.retry_after_seconds == 60.0


def test_download_returns_zip_bytes_and_validates_batch() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/files/download"
        body = json.loads(request.content.decode())
        assert body == {"file_names": ["a.txt", "b.txt"]}
        return httpx.Response(200, content=b"PK\x03\x04zip")

    with _client_with_handler(httpx.MockTransport(handler)) as client:
        assert client.download(["a.txt", "b.txt"]) == b"PK\x03\x04zip"
        with pytest.raises(CatalogRequestError, match="at most 3"):
            client.download(["1", "2", "3", "4"])


def test_mark_downloaded_posts_file_names() -> None:
    seen: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["body"] = json.loads(request.content.decode())
        return httpx.Response(200, json={"marked_now": 1, "already_marked": 0})

    with _client_with_handler(httpx.MockTransport(handler)) as client:
        client.mark_downloaded(["a.txt"])
    assert seen["path"] == "/api/files/downloaded"
    assert seen["body"] == {"file_names": ["a.txt"]}


def test_server_error_retries_then_fails() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="unavailable")

    with (
        _client_with_handler(httpx.MockTransport(handler)) as client,
        pytest.raises(CatalogTransientError, match="Retries exhausted"),
    ):
        client.list_names()


def test_client_paces_requests_by_min_interval() -> None:
    sleeps: list[float] = []
    now = {"t": 100.0}

    def clock() -> float:
        return now["t"]

    def sleep(seconds: float) -> None:
        sleeps.append(seconds)
        now["t"] += seconds

    def handler(_request: httpx.Request) -> httpx.Response:
        now["t"] += 0.01
        return httpx.Response(200, json={"file_names": ["a.txt"]})

    with _client_with_handler(
        httpx.MockTransport(handler),
        min_interval_seconds=1.5,
        sleep=sleep,
        clock=clock,
    ) as client:
        client.list_names()
        client.list_names()

    assert len(sleeps) == 1
    assert sleeps[0] == pytest.approx(1.5, abs=0.02)
