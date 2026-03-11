from fastapi import FastAPI, UploadFile, File
import shutil
import os
from rag import process_book, ask_question

app = FastAPI()

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.post("/upload-book")
async def upload_book(file: UploadFile = File(...)):

    file_path = f"{UPLOAD_FOLDER}/{file.filename}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    result = process_book(file_path)

    return {"message": result}


@app.get("/chat")
def chat(question: str):

    answer = ask_question(question)

    return {"answer": answer}


