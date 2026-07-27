from __future__ import annotations

from uuid import UUID

import redis


class RedisDownloadJobLock:
    KEY = "download:active_job"

    def __init__(self, client: redis.Redis) -> None:
        self._client = client

    def acquire(self, job_id: UUID, *, ttl_seconds: int = 3600) -> bool:
        return bool(self._client.set(self.KEY, str(job_id), nx=True, ex=ttl_seconds))

    def release(self, job_id: UUID) -> None:
        current = self._client.get(self.KEY)
        if current is None:
            return
        if isinstance(current, bytes):
            current = current.decode("utf-8")
        if current == str(job_id):
            self._client.delete(self.KEY)

    def get_holder(self) -> UUID | None:
        current = self._client.get(self.KEY)
        if current is None:
            return None
        if isinstance(current, bytes):
            current = current.decode("utf-8")
        return UUID(current)

    def refresh(self, job_id: UUID, *, ttl_seconds: int = 3600) -> None:
        current = self.get_holder()
        if current == job_id:
            self._client.expire(self.KEY, ttl_seconds)
