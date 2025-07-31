# vad/tests/test_vad.py
import pytest
import tempfile
import torch
import torchaudio
import numpy as np
from unittest.mock import patch

from vad.services.vad_service import run_vad_on_file, load_vad_model

# Helper: generate a fake .wav file
@pytest.fixture
def fake_wav_file():
    sr = 16000
    duration = 2
    wav = torch.from_numpy(np.random.randn(1, sr * duration).astype(np.float32))
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        torchaudio.save(tmp.name, wav, sr)
        yield tmp.name
    # (Optionally) os.remove(tmp.name)

# Test loading the VAD model (mocking the HF call)
@pytest.mark.asyncio
@patch("vad.services.vad_service.PyannotePipeline.from_pretrained")
async def test_load_vad_model(mock_from_pretrained):
    # Make from_pretrained a simple sync stub
    mock_from_pretrained.return_value = object()
    await load_vad_model()
    mock_from_pretrained.assert_called_once()

# Test run_vad_on_file using a **sync** mock for vad_pipeline
@pytest.mark.asyncio
@patch("vad.services.vad_service.vad_pipeline")
async def test_run_vad_on_file(mock_pipeline, fake_wav_file):
    # Dummy result mimicking pyannote output
    class DummySegment:
        def __init__(self, s, e):
            self.start = s
            self.end = e

    class DummyResult:
        def get_timeline(self):
            return type("T", (), {
                "support": lambda self: [DummySegment(0.0, 1.2), DummySegment(1.5, 2.0)]
            })()

    # Make vad_pipeline a simple sync function returning DummyResult
    mock_pipeline.return_value = DummyResult()

    # Now run_vad_on_file will call to_thread(mock_pipeline, ...),
    # which returns DummyResult synchronously, so await gives DummyResult
    result = await run_vad_on_file(fake_wav_file)
    segments = result.get_timeline().support()

    assert isinstance(segments, list)
    assert len(segments) == 2
    assert segments[0].start == 0.0 and segments[0].end == 1.2
