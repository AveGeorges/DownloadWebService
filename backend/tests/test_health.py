from fastapi.testclient import TestClient

from app.main import create_app


def test_health() -> None:
    client = TestClient(create_app())
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["version"] == "0.1.0"


def test_ready_ok(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.presentation.api.v1.health.check_database_connection",
        lambda: None,
    )
    monkeypatch.setattr(
        "app.presentation.api.v1.health.check_redis",
        lambda: None,
    )
    monkeypatch.setattr(
        "app.presentation.api.v1.health.check_rabbitmq",
        lambda: None,
    )
    client = TestClient(create_app())
    response = client.get("/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["checks"]["database"] == "ok"
    assert body["checks"]["redis"] == "ok"
    assert body["checks"]["rabbitmq"] == "ok"


def test_ready_db_fail(monkeypatch) -> None:
    def _fail() -> None:
        raise RuntimeError("db down")

    monkeypatch.setattr(
        "app.presentation.api.v1.health.check_database_connection",
        _fail,
    )
    monkeypatch.setattr(
        "app.presentation.api.v1.health.check_redis",
        lambda: None,
    )
    monkeypatch.setattr(
        "app.presentation.api.v1.health.check_rabbitmq",
        lambda: None,
    )
    client = TestClient(create_app())
    response = client.get("/ready")
    assert response.status_code == 503
    assert response.json()["status"] == "not_ready"
    assert response.json()["checks"]["database"] == "fail"


def test_ping() -> None:
    client = TestClient(create_app())
    response = client.get("/api/v1/ping")
    assert response.status_code == 200
    assert response.json() == {"message": "pong"}
