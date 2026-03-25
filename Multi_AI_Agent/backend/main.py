import os
from fastapi import FastAPI, WebSocket,UploadFile,File,WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from backend.agents.planner import planner_agent
from backend.agents.research import research_agent
from backend.agents.code import code_agent
from backend.agents.audio import audio_agent
from backend.agents.video import video_agent
from backend.agents.evaluation import evaluation_agent
from backend.agents.memory import save_task_memory
from backend.agents.chat import chat_agent
from backend.db import get_db_pool
import asyncio
import uuid

app = FastAPI()

#connect the websocket and frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
 
#upload folder for upload the audio/video file
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.on_event("startup")
async def startup():
    app.state.db_pool = await get_db_pool()

# audio/video convert to text again the process task to agent
async def process_task(user_input: str):
    task_id = str(uuid.uuid4())

    # audio/video convert to text perform the planner agent
    agents = await planner_agent(user_input)
    results = {}

    tasks = []

    if "research" in agents:
        tasks.append(("research", research_agent(user_input)))
    if "code" in agents:
        tasks.append(("code", code_agent(user_input)))

    responses = await asyncio.gather(*[t[1] for t in tasks], return_exceptions=True)

    for i, (name, _) in enumerate(tasks):
        results[name] = str(responses[i])

    evaluation = await evaluation_agent(results)
    chat = await chat_agent(user_input, results)

    # audio/video convert to text  store in db
    await save_task_memory(
        app.state.db_pool,
        task_id,
        user_input,
        agents,
        results,
        evaluation,
        chat
    )

    return {"task_id": task_id, "results": results, "evaluation": evaluation, "chat": chat}

# Call agents independently

# @app.websocket("/ws")
# async def websocket_endpoint(ws: WebSocket):
#     await ws.accept()

#     while True:
#         user_input = await ws.receive_text()
#         task_id = str(uuid.uuid4())

#         # Planner decides which agents to run
#         agents = await planner_agent(user_input)

#         results = {}

#         
#         if "research" in agents:
#             results["research"] = await research_agent(user_input)

#         if "code" in agents:
#             results["code"] = await code_agent(user_input)

#         if "audio" in agents:
#             results["audio"] = await audio_agent(user_input)

#         if "video" in agents:
#             results["video"] = await video_agent(user_input)

#         if "chat" in agents:
#             results["chat"] = await chat_agent(user_input, {})

#         evaluation = await evaluation_agent(results)

#         chat_response = await chat_agent(user_input, results)

#         # Save to database
#         await save_task_memory(
#             app.state.db_pool,
#             task_id,
#             user_input,
#             agents,
#             results,
#             evaluation,
#             chat_response
#         )

#         await ws.send_json({
#             "task_id": task_id,
#             "results": results,
#             "evaluation": evaluation,
#             "chat": chat_response
#         })


@app.websocket("/ws")
async def websocket(ws: WebSocket):
    await ws.accept()

    try:
        while True:
            text = await ws.receive_text()
            result = await process_task(text)
            await ws.send_json(result)

    except WebSocketDisconnect:
        print("Client disconnected")

    except Exception as e:
        print("WebSocket error:", str(e))

@app.post("/upload-audio")
async def upload_audio(file: UploadFile = File(...)):
    # Save temporarily
    path = f"{UPLOAD_DIR}/{uuid.uuid4()}_{file.filename}"
    with open(path, "wb") as f:
        f.write(await file.read())

    try:
        # Convert audio → text
        text = await audio_agent(path)
        result = await process_task(text)

        # Store in DB only (no chat display)
        task_id = str(uuid.uuid4())
        await save_task_memory(
            app.state.db_pool,
            task_id,
            user_input=text,
            subtasks=["audio"],
            results={"audio": text},
            evaluation=None,
            chat=None  
            # chat = None, so nothing displays
        )

    finally:
        if os.path.exists(path):
            os.remove(path)

    # Return only minimal response
    return {"type": "audio", "task_id": task_id, "status": "stored"}

@app.post("/upload-video")
async def upload_video(file: UploadFile = File(...)):
    path = f"{UPLOAD_DIR}/{uuid.uuid4()}_{file.filename}"
    with open(path, "wb") as f:
        f.write(await file.read())

    try:
        # Video → Audio → Text
        text = await video_agent(path)
        result = await process_task(text)

        # Store in DB only
        task_id = str(uuid.uuid4())
        await save_task_memory(
            app.state.db_pool,
            task_id,
            user_input=text,
            subtasks=["video", "audio"],
            results={"video": text},
            evaluation=None,
            chat=None  # chat = None
        )

    finally:
        if os.path.exists(path):
            os.remove(path)

    # Return minimal response
    return {"type": "video", "task_id": task_id, "status": "stored"}