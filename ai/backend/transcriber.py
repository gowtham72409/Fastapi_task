import whisper
import os

model = whisper.load_model("base")


def transcribe(file_path: str):
    try:
        if not os.path.exists(file_path):
            return "Audio file not found"

        result = model.transcribe(
            file_path,
            language="en",  
            fp16=False       
        )

        text = result.get("text", "").strip()

        if not text:
            return "No speech detected"

        return text

    except Exception as e:
        return f"Transcription error: {str(e)}"


