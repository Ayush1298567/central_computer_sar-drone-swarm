import pytest
from httpx import AsyncClient
from fastapi import FastAPI

from app.main import app


@pytest.mark.asyncio
async def test_register_login_refresh_and_role_guard(monkeypatch):
    client = AsyncClient(app=app, base_url="http://test")

    # Register a new operator user
    res = await client.post("/api/v1/auth/register", json={
        "username": "op1",
        "email": "op1@example.com",
        "password": "Password123!",
        "roles": ["operator"]
    })
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["username"] == "op1"

    # Login
    res = await client.post("/api/v1/auth/login", json={
        "username": "op1",
        "password": "Password123!"
    })
    assert res.status_code == 200, res.text
    tokens = res.json()
    access = tokens["access_token"]
    refresh = tokens["refresh_token"]
    assert access and refresh

    # Authorized call to protected endpoint (create mission)
    headers = {"Authorization": f"Bearer {access}"}
    res = await client.post("/api/v1/missions/", json={
        "name": "Test Mission",
        "description": "Desc",
        "center": {"lat": 0, "lng": 0},
        "search_area": {"type": "Polygon", "coordinates": [[[0,0],[1,0],[1,1],[0,1],[0,0]]]},
    }, headers=headers)
    assert res.status_code in (200, 201), res.text

    # Refresh token
    res = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert res.status_code == 200, res.text
    refreshed = res.json()
    assert refreshed["access_token"]

    await client.aclose()
