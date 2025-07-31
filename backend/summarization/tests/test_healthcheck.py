import pytest
from httpx import AsyncClient
from httpx._transports.asgi import ASGITransport
from summarization.main import app

@pytest.mark.asyncio
async def test_healthcheck():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/healthcheck")
    assert resp.status_code == 200
    assert "status" in resp.json()
