from app.config import get_settings
from app.infrastructure.db.session import check_database
from app.infrastructure.redis.client import build_redis_client


def check_redis() -> None:
    client = build_redis_client()
    try:
        if not client.ping():
            raise RuntimeError("Redis ping returned false")
    finally:
        client.close()


def check_rabbitmq() -> None:
    from kombu import Connection

    settings = get_settings()
    with Connection(settings.celery_broker_url, connect_timeout=2) as connection:
        connection.ensure_connection(max_retries=1, timeout=2)


def check_database_connection() -> None:
    check_database()
