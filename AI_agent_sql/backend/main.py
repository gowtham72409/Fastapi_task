from fastapi import FastAPI, WebSocket,WebSocketDisconnect
from backend.db import init_db, conn
from backend.agent.graph import graph,execute_plan
from backend.agent.planner import create_plan
from backend.agent.responder import generate_answer
from backend.agent.tools import BrowserTools


app = FastAPI()

@app.on_event("startup")
def startup():
    init_db()

@app.websocket("/chat")
async def chat(ws: WebSocket):
    await ws.accept()

    session_id = "user1"
    browser = BrowserTools()

    try:
        while True:
            msg = await ws.receive_text()

            # Save user message
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO chat_history (session_id, role, message) VALUES (%s,%s,%s)",
                (session_id, "user", msg)
            )
            conn.commit()

            print("USER:", msg)

            # ✅ 1. PLAN
            plan = create_plan(msg)
            print("PLAN:", plan)


            for step in plan:
                try:
                    exec_result = await execute_plan(browser.page,step)
                    print("EXEC RESULT:", exec_result)
                except Exception as e:
                    print("EXEC ERROR:", e)
            response = generate_answer(msg)

            # Save assistant response
            cur.execute(
                "INSERT INTO chat_history (session_id, role, message) VALUES (%s,%s,%s)",
                (session_id, "assistant", response)
            )
            conn.commit()

            # Send to frontend
            await ws.send_text(response)

    except WebSocketDisconnect:
        print("Client disconnected")