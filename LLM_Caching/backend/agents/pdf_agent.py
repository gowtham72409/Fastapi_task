from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
from backend.core.groq_client import ask_groq
from backend.config import EMBEDDING_MODEL
import numpy as np

model=SentenceTransformer(EMBEDDING_MODEL)


async def extract_page(file_path):
    reader=PdfReader(file_path)
    return [
        {"page":i+1,"text":page.extract_text().strip()}
        for i,page in enumerate(reader.pages)
        if page.extract_text()
    ]


async def get_top_pages(pages,question,top_k=5):
    text=[p["text"] for p in pages]
    page_vector=model.encode(text)
    query_vector=model.encode([question])[0]

    scores=np.dot(page_vector,query_vector)/(
        np.linalg.norm(page_vector,axis=1)*np.linalg.norm(query_vector)
    )

    top_idx = np.argsort(scores)[::-1][:top_k]
    return sorted([pages[i] for i in top_idx], key=lambda x: x["page"])

async def pdf_agent(file_path,question=""):
    pages=await extract_page(file_path)
    full_text="\n\n".join(f"[Page {p['page']}]\n{p['text']}" for p in pages)

    if not question:
        return {"text":full_text,"page_count":len(pages),"indexed_only":True}
    
    top_pages=await get_top_pages(pages,question)
    context="\n\n".join(f"[page {p['page']}]\n{p['text']}" for p in top_pages)
    prompt=f"""Answer using only the document below.
End your reply with: Sources: Page X, Page Y

Document:
{context}

Question: {question}"""

    answer = await ask_groq(prompt)

    return {"text":full_text,"answer":answer,"page_count":len(pages),"indexed_only":False}

