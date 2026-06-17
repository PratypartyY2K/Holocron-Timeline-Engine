import logging
from time import sleep

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.observability.request_middleware import add_request_logging_middleware


def test_request_logging_emits_completion_log(caplog) -> None:
    app = FastAPI()
    add_request_logging_middleware(app, slow_request_threshold_ms=1000.0)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    client = TestClient(app)
    with caplog.at_level(logging.INFO, logger="app.observability.http"):
        response = client.get("/health")

    assert response.status_code == 200
    assert "request_completed" in caplog.text
    assert "path=/health" in caplog.text


def test_request_logging_emits_slow_warning(caplog) -> None:
    app = FastAPI()
    add_request_logging_middleware(app, slow_request_threshold_ms=0.01)

    @app.get("/slow")
    def slow() -> dict[str, str]:
        sleep(0.01)
        return {"status": "slow"}

    client = TestClient(app)
    with caplog.at_level(logging.WARNING, logger="app.observability.http"):
        response = client.get("/slow")

    assert response.status_code == 200
    assert "request_slow" in caplog.text
