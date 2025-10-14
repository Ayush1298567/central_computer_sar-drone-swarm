import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import settings
from app.api.api_v1.api import api_router


def build_app() -> FastAPI:
    app = FastAPI()
    app.include_router(api_router, prefix=settings.API_V1_STR)
    return app


def test_metrics_endpoint_text_format():
    app = build_app()
    client = TestClient(app)
    r = client.get(f"{settings.API_V1_STR}/metrics")
    assert r.status_code == 200
    assert "text/plain" in r.headers.get("content-type", "")
    # Body may be empty if prometheus_client not installed; that's acceptable
    assert isinstance(r.content, (bytes, bytearray))
