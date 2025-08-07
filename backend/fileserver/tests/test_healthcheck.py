import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import status
from file_server.main import app

@pytest.mark.asyncio
async def test_healthcheck_file_server():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/health")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"status": "ok"}
