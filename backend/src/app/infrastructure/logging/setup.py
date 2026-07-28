from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

from app.infrastructure.logging.context import get_job_id, get_request_id

_CONFIGURED = False

_EXTRA_KEYS = (
    "job_id",
    "request_id",
    "method",
    "path",
    "status_code",
    "duration_ms",
    "retry_after_seconds",
    "downloaded_filename",
    "downloaded_count",
    "names_received",
    "size_bytes",
    "content_path",
    "app_env",
)


class JsonFormatter(logging.Formatter):
    """Emit one JSON object per log line for container-friendly aggregation."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        request_id = get_request_id() or getattr(record, "request_id", None)
        job_id = get_job_id() or getattr(record, "job_id", None)
        if request_id:
            payload["request_id"] = request_id
        if job_id:
            payload["job_id"] = job_id

        for key in _EXTRA_KEYS:
            if key in payload:
                continue
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value

        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False, default=str)


class TextFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        base = super().format(record)
        parts: list[str] = []
        request_id = get_request_id() or getattr(record, "request_id", None)
        job_id = get_job_id() or getattr(record, "job_id", None)
        if request_id:
            parts.append(f"request_id={request_id}")
        if job_id:
            parts.append(f"job_id={job_id}")
        if not parts:
            return base
        return f"{base} [{' '.join(parts)}]"


def configure_logging(*, level: str = "INFO", log_format: str = "json") -> None:
    """Configure root logging once for API and Celery worker processes."""
    global _CONFIGURED
    if _CONFIGURED:
        root = logging.getLogger()
        root.setLevel(level.upper())
        return

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level.upper())

    handler = logging.StreamHandler(sys.stdout)
    if log_format.strip().lower() == "text":
        handler.setFormatter(TextFormatter("%(asctime)s %(levelname)s [%(name)s] %(message)s"))
    else:
        handler.setFormatter(JsonFormatter())

    root.addHandler(handler)

    # Keep noisy libraries quieter; app loggers inherit root level.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("celery").setLevel(logging.INFO)

    _CONFIGURED = True


def reset_logging_for_tests() -> None:
    """Allow tests to reconfigure logging."""
    global _CONFIGURED
    _CONFIGURED = False
    root = logging.getLogger()
    root.handlers.clear()
