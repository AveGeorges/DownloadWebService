import json
import logging

import pytest
from fastapi.testclient import TestClient

from app.infrastructure.logging.context import bind_log_context, get_job_id, get_request_id
from app.infrastructure.logging.setup import (
    JsonFormatter,
    configure_logging,
    reset_logging_for_tests,
)
from app.main import create_app


@pytest.fixture(autouse=True)
def _reset_logging() -> None:
    reset_logging_for_tests()
    yield
    reset_logging_for_tests()


def test_json_formatter_includes_context_and_extras() -> None:
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="test.logger",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="hello",
        args=(),
        exc_info=None,
    )
    record.downloaded_count = 3

    with bind_log_context(request_id="req-1", job_id="job-1"):
        payload = json.loads(formatter.format(record))

    assert payload["message"] == "hello"
    assert payload["level"] == "INFO"
    assert payload["request_id"] == "req-1"
    assert payload["job_id"] == "job-1"
    assert payload["downloaded_count"] == 3
    assert "timestamp" in payload


def test_bind_log_context_resets() -> None:
    assert get_request_id() is None
    assert get_job_id() is None
    with bind_log_context(request_id="r", job_id="j"):
        assert get_request_id() == "r"
        assert get_job_id() == "j"
    assert get_request_id() is None
    assert get_job_id() is None


def test_configure_logging_json_emits_to_stdout(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging(level="INFO", log_format="json")
    logging.getLogger("app.test").info("structured", extra={"job_id": "abc"})
    captured = capsys.readouterr().out.strip().splitlines()[-1]
    payload = json.loads(captured)
    assert payload["message"] == "structured"
    assert payload["job_id"] == "abc"


def test_request_middleware_sets_request_id_header() -> None:
    configure_logging(level="WARNING", log_format="json")
    client = TestClient(create_app())
    response = client.get("/health", headers={"X-Request-ID": "client-req"})
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "client-req"
