import os
import uuid
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from backend.db import init_db, conn
from backend.agent.graph import execute_plan
from backend.agent.planner import create_plan
from backend.agent.responder import generate_answer
from backend.agent.tools import BrowserTools
from backend.agent.audio import transcribe_audio

app = FastAPI()
browser_manager = BrowserTools()


AUDIO_DIR = "stored_recordings"
if not os.path.exists(AUDIO_DIR):
    os.makedirs(AUDIO_DIR)

@app.on_event("startup")
async def startup():
    init_db()
    await browser_manager.start()


@app.websocket("/chat")
async def chat(ws: WebSocket):
    await ws.accept()
    browser_manager = BrowserTools()
    await browser_manager.start() 
    
    try:
        while True:
            data = await ws.receive_json() 
            user_text = ""

           
            if data.get("type") == "text":
                user_text = data.get("text")
            
            
            elif data.get("type") == "audio":
                import base64
                import tempfile
                audio_bytes = base64.b64decode(data.get("audio"))
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                    tmp.write(audio_bytes)
                    temp_path = tmp.name
                try:
                    user_text = transcribe_audio(temp_path)
                    await ws.send_json({"type": "transcription", "text": user_text})
                finally:
                    os.remove(temp_path)       
            if user_text:
                plan = create_plan(user_text)
                response = generate_answer(user_text)
                await ws.send_json({"type": "answer", "text": response})

    except WebSocketDisconnect:
        print("Client disconnected")
    finally:
        await browser_manager.close()