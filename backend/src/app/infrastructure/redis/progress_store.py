from __future__ import annotations

import json
from uuid import UUID

import redis

from app.application.dto.job_progress import JobProgressView


class RedisJobProgressStore:
    def __init__(
        self,
        client: redis.Redis,
        *,
        key_prefix: str = "job",
        ttl_seconds: int = 86400,
    ) -> None:
        self._client = client
        self._key_prefix = key_prefix
        self._ttl_seconds = ttl_seconds

    def _key(self, job_id: UUID | str) -> str:
        return f"{self._key_prefix}:{job_id}:progress"

    def save(self, progress: JobProgressView) -> None:
        payload = {
            "job_id": progress.job_id,
            "status": progress.status,
            "names_received": progress.names_received,
            "downloaded_count": progress.downloaded_count,
            "started_at": progress.started_at,
            "error": progress.error,
        }
        self._client.set(self._key(progress.job_id), json.dumps(payload), ex=self._ttl_seconds)

    def get(self, job_id: UUID) -> JobProgressView | None:
        raw = self._client.get(self._key(job_id))
        if raw is None:
            return None
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        data = json.loads(raw)
        return JobProgressView(
            job_id=str(data["job_id"]),
            status=str(data["status"]),
            names_received=int(data["names_received"]),
            downloaded_count=int(data["downloaded_count"]),
            started_at=data.get("started_at"),
            error=data.get("error"),
        )
