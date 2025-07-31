import pytest
from httpx import AsyncClient
from httpx._transports.asgi import ASGITransport
from unittest.mock import AsyncMock, patch
from summarization.main import app
from pathlib import Path
import tempfile

@pytest.mark.asyncio
@patch("summarization.routers.summarize.call_ollama", new_callable=AsyncMock)
async def test_summarize_endpoint(mock_call_ollama):
    mock_call_ollama.return_value = "This is a mock summary."

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "test_transcript.txt"
        output_dir = Path(tmpdir) / "output"
        input_path.write_text("This is a dummy transcript.")

        payload = {
            "transcript_path": str(input_path),
            "output_dir": str(output_dir)
        }

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post("/summarization/", json=payload)

        assert resp.status_code == 200
        result = resp.json()
        assert "summary_path" in result
        assert Path(result["summary_path"]).exists()
        assert Path(result["summary_path"]).read_text() == "This is a mock summary."
