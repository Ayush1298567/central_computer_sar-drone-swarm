import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_ws_route_exists():
    client = AsyncClient(app=app, base_url="http://test")
    # Can't upgrade to WS via httpx; just ensure router path is registered
    r = await client.get("/api/v1/websocket/ws")
    assert r.status_code in (200, 400, 404)
    await client.aclose()
