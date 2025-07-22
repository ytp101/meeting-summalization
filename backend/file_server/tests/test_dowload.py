import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import status
from pathlib import Path
from file_server.main import app
from file_server.utils import files  # ✅ FIXED: now imported

@pytest.mark.asyncio
async def test_download_existing_file(tmp_path):
    work_id = "test123"
    category = "transcript"

    # Create dummy .mp3 in raw/
    raw_dir = tmp_path / work_id / "raw"
    raw_dir.mkdir(parents=True)
    audio_file = raw_dir / "testfile.mp3"
    audio_file.write_text("dummy audio")

    # Create matching transcript file
    transcript_dir = tmp_path / work_id / "transcript"
    transcript_dir.mkdir(parents=True)
    transcript_file = transcript_dir / "testfile.txt"
    transcript_file.write_text("dummy transcript")

    # Patch DATA_ROOT
    files.DATA_ROOT = tmp_path

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get(f"/download/{work_id}/{category}")
        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-disposition"].startswith("attachment")
        assert b"dummy transcript" in response.content


@pytest.mark.asyncio
async def test_download_invalid_category():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/download/anyid/invalidcat")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["detail"] == "Invalid category"


@pytest.mark.asyncio
async def test_download_missing_file(tmp_path):
    work_id = "nofile"
    category = "summary"

    (tmp_path / work_id / "summary").mkdir(parents=True)
    files.DATA_ROOT = tmp_path

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get(f"/download/{work_id}/{category}")
        assert response.status_code == status.HTTP_404_NOT_FOUND
