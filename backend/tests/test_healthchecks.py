from app.infrastructure.healthchecks import (
    check_database_connection,
    check_rabbitmq,
    check_redis,
)


def test_healthchecks_delegate(monkeypatch) -> None:
    flags = {"db": 0, "mq": 0}

    monkeypatch.setattr(
        "app.infrastructure.healthchecks.check_database",
        lambda: flags.__setitem__("db", flags["db"] + 1),
    )

    class _Redis:
        def ping(self) -> bool:
            return True

        def close(self) -> None:
            return None

    monkeypatch.setattr(
        "app.infrastructure.healthchecks.build_redis_client",
        lambda: _Redis(),
    )
    monkeypatch.setattr(
        "app.infrastructure.healthchecks.get_settings",
        lambda: type("S", (), {"celery_broker_url": "amqp://guest:guest@localhost:5672//"})(),
    )

    class _Conn:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def ensure_connection(self, **kwargs):
            flags["mq"] += 1

    monkeypatch.setattr("kombu.Connection", lambda *a, **k: _Conn())

    check_database_connection()
    check_redis()
    check_rabbitmq()

    assert flags["db"] == 1
    assert flags["mq"] == 1
