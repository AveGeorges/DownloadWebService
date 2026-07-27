import httpx
import pytest

from app.domain.exceptions import (
    CatalogBlockedError,
    CatalogRequestError,
    CatalogTransientError,
)
from app.infrastructure.external.catalog_client import ExternalCatalogClient


def _client_with_handler(handler: httpx.MockTransport) -> ExternalCatalogClient:
    return ExternalCatalogClient(
        base_url="https://catalog.test",
        candidate_id="candidate-1",
        max_attempts=3,
        transport=handler,
    )


def test_list_names_parses_list_payload() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/files/names"
        assert request.headers["X-Candidate-Id"] == "candidate-1"
        return httpx.Response(200, json=["a.txt", "b.txt"])

    with _client_with_handler(httpx.MockTransport(handler)) as client:
        assert client.list_names() == ["a.txt", "b.txt"]


def test_list_names_parses_object_payload_and_empty() -> None:
    payloads = [{"names": ["one.txt"]}, {"names": []}]

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
        return httpx.Response(200, json={"files": ["x.txt"]})

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
        assert b"a.txt" in request.content
        return httpx.Response(200, content=b"PK\x03\x04zip")

    with _client_with_handler(httpx.MockTransport(handler)) as client:
        assert client.download(["a.txt", "b.txt"]) == b"PK\x03\x04zip"
        with pytest.raises(CatalogRequestError, match="at most 3"):
            client.download(["1", "2", "3", "4"])


def test_mark_downloaded_posts_names() -> None:
    seen: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["body"] = request.content
        return httpx.Response(204)

    with _client_with_handler(httpx.MockTransport(handler)) as client:
        client.mark_downloaded(["a.txt"])
    assert seen["path"] == "/api/files/downloaded"
    assert b"a.txt" in seen["body"]  # type: ignore[operator]


def test_server_error_retries_then_fails() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="unavailable")

    with (
        _client_with_handler(httpx.MockTransport(handler)) as client,
        pytest.raises(CatalogTransientError, match="Retries exhausted"),
    ):
        client.list_names()
