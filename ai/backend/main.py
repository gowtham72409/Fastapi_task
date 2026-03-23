from fastapi import FastAPI, WebSocket
import tempfile, os

from backend.transcriber import transcribe
from backend.graph import graph
from backend.memory import save_message, get_recent_history, get_relevant_context

from pydub import AudioSegment   

app = FastAPI()

from pydub import AudioSegment
import os

ffmpeg_bin_path = r"C:\Users\gowsi\Downloads\ffmpeg-2026-03-18-git-106616f13d-full_build\ffmpeg-2026-03-18-git-106616f13d-full_build\bin" 
os.environ["PATH"] += os.pathsep + ffmpeg_bin_path

AudioSegment.converter = os.path.join(ffmpeg_bin_path, "ffmpeg.exe")
AudioSegment.ffprobe = os.path.join(ffmpeg_bin_path, "ffprobe.exe")

@app.websocket("/ws/audio")
async def websocket_audio(ws: WebSocket):
    await ws.accept()
    print("WebSocket Connected")

    while True:

        try:
            audio_bytes = await ws.receive_bytes()

            with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as f:
                f.write(audio_bytes)
                temp_path = f.name


            audio = AudioSegment.from_file(temp_path, format="webm")
            wav_path = temp_path + ".wav"
            audio.export(wav_path, format="wav")
            text = transcribe(wav_path)

            if not text or text.strip() in [".", ""]:
                await ws.send_json({"text": "...", "result": "No speech detected"})
                continue

            history = get_recent_history()
            context = get_relevant_context(text)

            save_message("user", text)

            result = graph.invoke({
                "input": text,
                "history": history,
                "context": context,
                "plan": [],
                "result": [],
                "status": ""
            })

            save_message("assistant", str(result))
            await ws.send_json({
                "text": text,
                "context": context,
                "result": result
            })


            os.remove(temp_path)
            os.remove(wav_path)

        except Exception as e:
            try:
                await ws.send_json({"error": str(e)})
            except:
                pass 
    
