import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import status
from file_server.main import app

@pytest.mark.asyncio
async def test_root_service_live_check():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"message": "Meeting Summary File Server is live"}
