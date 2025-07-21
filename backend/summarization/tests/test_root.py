import pytest
from httpx import AsyncClient
from httpx._transports.asgi import ASGITransport
from summarization.main import app

@pytest.mark.asyncio
async def test_liveness_check():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "summarization running"
    assert "model" in data
