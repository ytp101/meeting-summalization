import os
import pytest
from pathlib import Path
from unittest.mock import AsyncMock

from httpx import AsyncClient, ASGITransport
from fastapi import status

# Ensure HF_HOME is writable before any imports that mkdir it
os.environ.setdefault("HF_HOME", "/tmp/huggingface")

from whisper.config.settings import MODEL_ID
from whisper.main import app


@pytest.fixture
def transport():
    """
    HTTPX ASGI transport wrapping the FastAPI app.
    """
    return ASGITransport(app=app)


@pytest.mark.asyncio
async def test_root_status(transport):
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/")
    assert r.status_code == status.HTTP_200_OK
    # Root returns {"status":"running","model":<MODEL_ID>}
    assert r.json() == {"status": "running", "model": MODEL_ID}


@pytest.mark.asyncio
async def test_healthcheck_status(mocker, transport):
    # Patch the *imports in the healthcheck router module*:
    mocker.patch("whisper.routers.healthcheck.is_model_loaded", return_value=True)
    mocker.patch("whisper.routers.healthcheck.DEVICE", "cuda:0")

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/healthcheck")
    assert r.status_code == status.HTTP_200_OK
    assert r.json() == {"model_loaded": True, "gpu_available": "cuda:0"}


@pytest.mark.asyncio
async def test_whisper_transcription_mock(mocker, tmp_path, transport):
    # 1) Touch a fake WAV file so the existence check passes
    fake_wav = tmp_path / "audio.wav"
    fake_wav.write_bytes(b"")  # empty but exists

    # 2) Patch the transcribe fn *imported by the whisper router* to skip audio I/O
    fake_lines = ["[0.00-1.00] Speaker: Test"]
    mock_transcribe = AsyncMock(return_value=([], fake_lines))
    mocker.patch("whisper.routers.whisper.transcribe", mock_transcribe)

    payload = {
        "filename": str(fake_wav),
        "output_dir": str(tmp_path),
        "segments": None
    }
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post("/whisper/", json=payload)

    assert r.status_code == status.HTTP_200_OK
    body = r.json()
    assert "transcription_file_path" in body

    out_path = Path(body["transcription_file_path"])
    assert out_path.exists()
    content = out_path.read_text(encoding="utf-8")
    # Ensure our fake line made it into the .txt
    assert "Speaker: Test" in content
