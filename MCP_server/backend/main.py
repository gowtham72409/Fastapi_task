import os
import asyncio
import uuid
import json

from fastapi import FastAPI, WebSocket, UploadFile, File, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# ── Agents ──────────────────────────────────────────────────────────────────
from backend.agents.planner import planner_agent
from backend.agents.research import research_agent
from backend.agents.code import code_agent
from backend.agents.audio import audio_agent
from backend.agents.video import video_agent
from backend.agents.evaluation import evaluation_agent
from backend.agents.memory import save_task_memory
from backend.agents.chat import chat_agent

# ── DB / MCP ────────────────────────────────────────────────────────────────
from backend.db import get_db_pool
from backend.mcp.mcp_client import resolve_tool_from_intent, call_mcp_tool

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import tempfile

UPLOAD_DIR = os.path.join(tempfile.gettempdir(), "multi_ai_agent_uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)



@app.on_event("startup")
async def startup():
    app.state.db_pool = await get_db_pool()



async def process_task(user_input: str, pool) -> dict:
    task_id = str(uuid.uuid4())

    mcp_tool = await resolve_tool_from_intent(user_input)
    mcp_result = None
    if mcp_tool:
        mcp_result = await call_mcp_tool(mcp_tool["tool"], mcp_tool["params"])

    agents = await planner_agent(user_input)
    results = {}

    tasks = []
    if "research" in agents:
        tasks.append(("research", research_agent(user_input)))
    if "code" in agents:
        tasks.append(("code", code_agent(user_input)))

    if tasks:
        responses = await asyncio.gather(*[t[1] for t in tasks], return_exceptions=True)
        for i, (name, _) in enumerate(tasks):
            results[name] = str(responses[i])

    if mcp_result:
        results["mcp"] = json.dumps(mcp_result)

    evaluation = await evaluation_agent(results)
    chat      = await chat_agent(user_input, results)

    await save_task_memory(pool, task_id, user_input, agents, results, evaluation, chat)

    return {
        "task_id":    task_id,
        "results":    results,
        "evaluation": evaluation,
        "chat":       chat,
        "mcp":        mcp_result,
    }



@app.websocket("/ws")
async def websocket_text(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            text   = await ws.receive_text()
            result = await process_task(text, ws.app.state.db_pool)
            await ws.send_json(result)
    except WebSocketDisconnect:
        print("Client disconnected (text WS)")
    except Exception as e:
        print(f"WebSocket error: {e}")



@app.websocket("/ws/mic")
async def websocket_mic(ws: WebSocket):
    """
    Receives raw audio bytes from the browser's MediaRecorder (webm/opus).
    Saves to a temp file, transcribes, runs agents, sends back result.
    File is always deleted — even on disconnect.
    """
    await ws.accept()
    tmp_path: str | None = None

    try:
        while True:
            data = await ws.receive_bytes()
            tmp_path = f"{UPLOAD_DIR}/mic_{uuid.uuid4()}.webm"

            with open(tmp_path, "wb") as f:
                f.write(data)

            try:
                transcript = await audio_agent(tmp_path)
                await ws.send_json({"type": "transcript", "text": transcript})

                result = await process_task(transcript, ws.app.state.db_pool)
                await ws.send_json({**result, "type": "agent_result"})
            finally:
                _delete(tmp_path)
                tmp_path = None

    except WebSocketDisconnect:
        print("Client disconnected (mic WS)")
    except Exception as e:
        print(f"Mic WebSocket error: {e}")
    finally:
        if tmp_path:
            _delete(tmp_path)



@app.post("/upload-audio")
async def upload_audio(file: UploadFile = File(...)):
    path = _tmp_path(file.filename)
    await _save_upload(file, path)

    try:
        text       = await audio_agent(path)
        result     = await process_task(text, app.state.db_pool)

        return {"type": "audio", "transcript": text, **result}
    finally:
        _delete(path)   


@app.post("/upload-video")
async def upload_video(file: UploadFile = File(...)):
    path = _tmp_path(file.filename)
    await _save_upload(file, path)

    try:
        text    = await video_agent(path)
        result  = await process_task(text, app.state.db_pool)

        return {"type": "video", "transcript": text, **result}
    finally:
        _delete(path)   



def _tmp_path(filename: str) -> str:
    return f"{UPLOAD_DIR}/{uuid.uuid4()}_{filename}"

async def _save_upload(file: UploadFile, path: str):
    content = await file.read()
    with open(path, "wb") as f:
        f.write(content)

def _delete(path: str):
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except Exception as e:
        print(f"Could not delete {path}: {e}")