from fastapi.testclient import TestClient

from app.main import create_app


def test_health() -> None:
    client = TestClient(create_app())
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["version"] == "0.1.0"


def test_ready() -> None:
    client = TestClient(create_app())
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_ping() -> None:
    client = TestClient(create_app())
    response = client.get("/api/v1/ping")
    assert response.status_code == 200
    assert response.json() == {"message": "pong"}
