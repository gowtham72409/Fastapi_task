import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("GROQ_API_KEY") 
)

def transcribe_audio(audio_file_path):
    """Converts speech to text using Whisper on Groq."""
    try:
        with open(audio_file_path, "rb") as file:
            transcription = client.audio.transcriptions.create(
                file=(audio_file_path, file.read()),
                model="distil-whisper-large-v3-en",
                response_format="text",
            )
        return transcription
    except Exception as e:
        print(f"Transcription Error: {e}")
        return None