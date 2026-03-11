from fastapi import FastAPI,UploadFile,File
import shutil
import os
from rag_service import RAGService

app=FastAPI()

rag=RAGService()

os.makedirs("uploads",exist_ok=True)
os.makedirs("vector_db",exist_ok=True)

@app.on_event("startup")
def load_vector():
    rag.load_vector_store()

@app.get("/")
def home():
    return {"message": "LangChain Page Index RAG Backend"}

@app.post("/uploads")
def upload_book(file:UploadFile=File(...)):

    file_path=f"uploads/{file.filename}"

    with open(file_path,"wb") as buffer:
        shutil.copyfileobj(file.file,buffer)

    result=rag.index_book(file_path)
    return result

@app.post("/chat")
def chat(question:str):
    answer=rag.ask_question(question)

    return {"Answer":answer}