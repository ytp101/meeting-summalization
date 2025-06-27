from pyannote.audio import Pipeline  
import torch 
import torchaudio
import os 

HF_TOKEN= os.getenv("HF_TOKEN")

pipeline = Pipeline.from_pretrained(
    "pyannote/speaker-diarization-3.1",
    use_auth_token=HF_TOKEN,
)

BASE_DIR_WAV = os.getenv('BASE_DIR_WAV', '/usr/local/app/data/wav/')
BASE_DIR_TXT = os.getenv('BASE_DIR_TXT', '/usr/local/app/data/txt/')

device = "cuda" if torch.cuda.is_available() else "cpu"
pipeline.to(torch.device(device))

filename = "/home/yodsran/meeting-summalization/backend/diarization/tests/test_sound.wav"

waveform, sample_rate = torchaudio.load(filename)

diarization = pipeline({
        "waveform": waveform,
        "sample_rate": sample_rate
    })

with open("/home/yodsran/meeting-summalization/backend/diarization/tests/diarization.rttm", "w") as rttm:
    diarization.write_rttm(rttm)