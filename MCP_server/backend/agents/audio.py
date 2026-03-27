from faster_whisper import WhisperModel

model = WhisperModel("base", compute_type="int8")

async def audio_agent(file_path: str):
    segments, _ = model.transcribe(file_path)
    return " ".join([seg.text for seg in segments]).strip()