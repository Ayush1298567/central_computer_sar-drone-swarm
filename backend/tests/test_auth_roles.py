import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_viewer_cannot_start_mission():
    client = AsyncClient(app=app, base_url="http://test")

    # Register viewer
    r = await client.post("/api/v1/auth/register", json={
        "username": "v1",
        "email": "v1@example.com",
        "password": "Password123!",
        "roles": ["viewer"],
    })
    assert r.status_code == 200

    # Login
    r = await client.post("/api/v1/auth/login", json={
        "username": "v1",
        "password": "Password123!",
    })
    assert r.status_code == 200
    access = r.json()["access_token"]

    # Create a mission first with operator (setup)
    r = await client.post("/api/v1/auth/register", json={
        "username": "op2",
        "email": "op2@example.com",
        "password": "Password123!",
        "roles": ["operator"],
    })
    assert r.status_code == 200
    r = await client.post("/api/v1/auth/login", json={
        "username": "op2",
        "password": "Password123!",
    })
    op_access = r.json()["access_token"]
    rh = {"Authorization": f"Bearer {op_access}"}
    r = await client.post("/api/v1/missions/", json={
        "name": "M2",
        "center": {"lat": 0, "lng": 0},
        "search_area": {"type": "Polygon", "coordinates": [[[0,0],[1,0],[1,1],[0,1],[0,0]]]},
    }, headers=rh)
    assert r.status_code in (200, 201)
    mid = r.json()["mission_id"]

    # Attempt to start mission as viewer
    headers = {"Authorization": f"Bearer {access}"}
    r = await client.put(f"/api/v1/missions/{mid}/start", headers=headers)
    assert r.status_code == 403

    await client.aclose()

