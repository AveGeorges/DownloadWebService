from __future__ import annotations

import redis

from app.config import Settings, get_settings


def build_redis_client(settings: Settings | None = None) -> redis.Redis:
    cfg = settings or get_settings()
    return redis.Redis.from_url(cfg.redis_url, decode_responses=False)
