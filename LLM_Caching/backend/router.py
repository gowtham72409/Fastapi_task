import os
import uuid
import datetime
import re
import tempfile
from fastapi import APIRouter, WebSocket, UploadFile, File, WebSocketDisconnect, Form
from pydantic import BaseModel
from backend.agents.audio import audio_agent
from backend.agents.video import video_agent
from backend.agents.pdf_agent import pdf_agent
from backend.db import get_db_pool
from backend.process_task import process_task
from backend.core.semantic_cache import redis, INDEX_KEY, CACHE_PREFIX


router = APIRouter(tags=['router'])

UPLOAD_DIR = os.path.join(tempfile.gettempdir(), "multi_ai_agent_uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

db_pool_instance = None

@router.on_event("startup")
async def startup():
    global db_pool_instance
    db_pool_instance = await get_db_pool()

@router.websocket("/ws")
async def websocket_text(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            text   = await ws.receive_text()
            result = await process_task(text, db_pool_instance)
            await ws.send_json(result)
    except WebSocketDisconnect:
        print("Client disconnected (text WS)")
    except Exception as e:
        print(f"WebSocket error: {e}")


@router.websocket("/ws/mic")
async def websocket_mic(ws: WebSocket):
    await ws.accept()
    tmp_path = None
    try:
        while True:
            data     = await ws.receive_bytes()
            tmp_path = f"{UPLOAD_DIR}/mic_{uuid.uuid4()}.webm"
            with open(tmp_path, "wb") as f:
                f.write(data)
            try:
                transcript = await audio_agent(tmp_path)
                with open(tmp_path, "rb") as f:
                    file_bytes = f.read()
                await ws.send_json({"type": "transcript", "text": transcript})
                result = await process_task(transcript, db_pool_instance, media_type="audio", file_bytes=file_bytes)
                await ws.send_json({**result, "type": "agent_result"})
            finally:
                _delete(tmp_path); tmp_path = None
    except WebSocketDisconnect:
        print("Client disconnected (mic WS)")
    except Exception as e:
        print(f"Mic WebSocket error: {e}")
    finally:
        if tmp_path: _delete(tmp_path)

@router.delete("/cache/clear")
async def clear_semantic_cache():
    """Clear all semantic cache entries."""
    keys = await redis.keys(f"{CACHE_PREFIX}*")
    if keys:
        await redis.delete(*keys)
    await redis.delete(INDEX_KEY)
    return {"cleared": len(keys) + 1}


@router.post("/upload-audio")
async def upload_audio(file: UploadFile = File(...)):
    path = _tmp_path(file.filename)
    await _save_upload(file, path)
    try:
        text   = await audio_agent(path)
        with open(path, "rb") as f:
            file_bytes = f.read()
        result = await process_task(text, db_pool_instance, media_type="audio", file_bytes=file_bytes)
        return {"type": "audio", "transcript": text, **result}
    finally:
        _delete(path)


@router.post("/upload-video")
async def upload_video(file: UploadFile = File(...)):
    path = _tmp_path(file.filename)
    await _save_upload(file, path)
    try:
        text   = await video_agent(path)
        with open(path, "rb") as f:
            file_bytes = f.read()
        result = await process_task(text, db_pool_instance, media_type="video", file_bytes=file_bytes)
        return {"type": "video", "transcript": text, **result}
    finally:
        _delete(path)


@router.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...),question: str    = Form(default=""),):
    path = _tmp_path(file.filename)
    await _save_upload(file, path)
    try:
        pdf_result = await pdf_agent(path, question="")   
        with open(path, "rb") as f:
            pdf_bytes = f.read()
            
        async with db_pool_instance.acquire() as conn:
            task_id = str(uuid.uuid4())
            await conn.execute(
                """
                INSERT INTO ai_task_memory (task_id, user_input, created_at, updated_at, pdf_file)
                VALUES ($1, $2, $3, $4, $5)
                """, task_id, f"Uploaded PDF: {file.filename}", datetime.datetime.now(), datetime.datetime.now(), pdf_bytes
            )
            
        return {
            "type":         "pdf",
            "task_id":      task_id,
            "filename":     file.name if hasattr(file, "name") else file.filename,
            "page_count":   pdf_result["page_count"],
            "truncated":    pdf_result.get("truncated", False),
            "pdf_text":     pdf_result["text"],  
            "indexed_only": True,
        }
    finally:
        _delete(path)


class AskPdfRequest(BaseModel):
    question: str
    pdf_text: str

@router.post("/ask-pdf")
async def ask_pdf(req: AskPdfRequest):
    """Answer a question from already-extracted PDF text with page citations."""
    from backend.core.groq_client import ask_groq

    import re

    def get_relevant_pages(full_text: str, question: str, top_k: int = 15) -> str:
        pages = re.split(r'(?=\[Page \d+\]\n)', full_text)
        pages = [p.strip() for p in pages if p.strip()]
        
        if len(pages) <= top_k:
            return full_text
            
        stop_words = {"what", "is", "the", "in", "of", "and", "a", "to", "for", "on", "with", "as", "by", "an", "this", "that", "are", "from", "how", "why", "can", "you", "tell", "explain", "about", "details", "mention"}
        q_words = [w.lower() for w in re.findall(r'\w+', question) if w.lower() not in stop_words and len(w) > 2]
        
        selected_pages = {0, 1, 2} if len(pages) > 2 else set(range(len(pages)))
        
        if q_words:
            scores = []
            for i, p in enumerate(pages):
                p_lower = p.lower()
                score = sum(p_lower.count(qw) for qw in q_words)
                scores.append((score, i))
                
            scores.sort(key=lambda x: x[0], reverse=True)
            for score, i in scores:
                if len(selected_pages) >= top_k:
                    break
                if score > 0:
                    selected_pages.add(i)
                    
        for i in range(len(pages)):
            if len(selected_pages) >= top_k:
                break
            selected_pages.add(i)
            
        top_pages_idx = sorted(list(selected_pages))
        return "\n\n".join([pages[i] for i in top_pages_idx])

    context = get_relevant_pages(req.pdf_text, req.question)


    relevance_prompt = f"""You are a relevance classifier. Your ONLY job is to check whether the document below contains enough information to answer the user's question.

Document Content:
---
{context}
---

User Question: {req.question}

RULES (follow exactly):
- If the document clearly contains information about the question topic, reply with exactly: RELEVANT
- If the document does NOT contain information about the question topic, reply with exactly: NOT_RELEVANT
- Do NOT write anything else. Do NOT explain. Output ONLY one of those two words."""

    relevance = await ask_groq(relevance_prompt)
    relevance = relevance.strip().upper()

    if "NOT_RELEVANT" in relevance or "RELEVANT" not in relevance:
        return {
            "type":     "not_in_pdf",
            "redirect": True,
            "question": req.question,
        }

    answer_prompt = f"""You are an advanced document analysis assistant.

Document Content:
---
{context}
---

User Question: {req.question}

Instructions:
1. Write a clear, accurate, and concise answer based ONLY on the document content above.
2. You MUST append a new line at the very end of your response with the page numbers you used, formatted EXACTLY like this: "Sources: Page 1, Page 2". Do not forget this!
3. Do NOT guess or add outside knowledge."""

    answer = await ask_groq(answer_prompt)

    import re as _re
    src_match = _re.search(r'Sources\s*:\s*(.+)', answer, _re.IGNORECASE)
    if not src_match or src_match.group(1).strip().lower() in ("none", "", "n/a"):
        return {
            "type":     "not_in_pdf",
            "redirect": True,
            "question": req.question,
        }

    return {
        "type":   "pdf_answer",
        "answer": answer,
        "chat":   answer,
    }


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
