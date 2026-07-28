from uuid import uuid4

import fakeredis

from app.application.dto.job_progress import JobProgressView
from app.infrastructure.redis.job_lock import RedisDownloadJobLock
from app.infrastructure.redis.progress_store import RedisJobProgressStore


def test_redis_lock_acquire_release_and_holder() -> None:
    client = fakeredis.FakeRedis()
    lock = RedisDownloadJobLock(client)
    first = uuid4()
    second = uuid4()

    assert lock.acquire(first) is True
    assert lock.get_holder() == first
    assert lock.acquire(second) is False

    lock.refresh(first, ttl_seconds=120)
    lock.release(second)  # no-op for other holder
    assert lock.get_holder() == first

    lock.release(first)
    assert lock.get_holder() is None


def test_redis_progress_store_roundtrip() -> None:
    client = fakeredis.FakeRedis()
    store = RedisJobProgressStore(client, ttl_seconds=60)
    job_id = uuid4()

    assert store.get(job_id) is None

    view = JobProgressView(
        job_id=str(job_id),
        status="running",
        names_received=9,
        downloaded_count=3,
        started_at="2026-07-28T00:00:00+00:00",
        error=None,
    )
    store.save(view)
    loaded = store.get(job_id)
    assert loaded is not None
    assert loaded.status == "running"
    assert loaded.names_received == 9
    assert loaded.downloaded_count == 3
