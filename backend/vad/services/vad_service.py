import asyncio
from pyannote.audio import Pipeline as PyannotePipeline
from config.settings import HF_TOKEN

vad_pipeline = None  # Global

async def load_vad_model():
    global vad_pipeline
    vad_pipeline = await asyncio.to_thread(
        PyannotePipeline.from_pretrained,
        "pyannote/voice-activity-detection",
        use_auth_token=HF_TOKEN
    )

async def run_vad_on_file(file_path: str):
    if vad_pipeline is None:
        raise RuntimeError("VAD pipeline not loaded.")
    return await asyncio.to_thread(vad_pipeline, file_path)
