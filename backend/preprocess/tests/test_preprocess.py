# preprocess/tests/test_preprocess.py

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from pathlib import Path

from preprocess.main import app
import preprocess.routers.preprocess as preprocess_router  # patch point

client = TestClient(app)

VALID_INPUT = Path("/tmp/test_input.mp4")
OUTPUT_DIR  = Path("/tmp/test_output")

@pytest.fixture(scope="module", autouse=True)
def setup_files(tmp_path_factory):
    """
    Create dummy input file and ensure output dir exists.
    """
    base = tmp_path_factory.mktemp("data")
    global VALID_INPUT, OUTPUT_DIR
    VALID_INPUT = base / "input.mp4"
    OUTPUT_DIR  = base / "out"
    OUTPUT_DIR.mkdir()
    VALID_INPUT.write_bytes(b"\x00")  # placeholder content
    yield
    # pytest tmp_path_factory will clean up automatically

@pytest.fixture(autouse=True)
def mock_run_preprocess(monkeypatch):
    """
    Monkey‑patch the router’s run_preprocess so no real FFmpeg runs.
    The fake writes a minimal WAV header so the endpoint sees a valid file.
    """
    async def fake_preprocess(input_file: Path, output_file: Path) -> None:
        wav_header = (
            b"RIFF$\x00\x00\x00WAVEfmt "
            b"\x10\x00\x00\x00\x01\x00\x01\x00"
            b"\x40\x1f\x00\x00\x80>\x00\x00"
            b"\x02\x00\x10\x00data\x00\x00\x00\x00"
        )
        output_file.write_bytes(wav_header)

    # Patch the name that the router imported
    monkeypatch.setattr(preprocess_router, "run_preprocess", fake_preprocess)
    yield

def test_preprocess_success():
    """
    Posting a valid input should return 200 and produce a .opus via our fake service.
    """
    resp = client.post(
        "/preprocess/",
        json={"input_path": str(VALID_INPUT), "output_dir": str(OUTPUT_DIR)},
    )
    assert resp.status_code == status.HTTP_200_OK

    data = resp.json()
    assert isinstance(data, list)
    out_path = Path(data[0]["preprocessed_file_path"]) 
    assert out_path.exists() and out_path.suffix == ".opus"

def test_preprocess_file_not_found():
    """
    Non-existent input path should yield 404.
    """
    resp = client.post(
        "/preprocess/",
        json={
            "input_path": "/does/not/exist.mp4",
            "output_dir": str(OUTPUT_DIR),
        },
    )
    assert resp.status_code == status.HTTP_404_NOT_FOUND
    assert resp.json()["detail"] == "Input file not found"
