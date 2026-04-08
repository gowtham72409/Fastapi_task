from google import genai
from google.genai import types
from pypdf import PdfReader
from backend.core.gemini_client import ask_gemini
from backend.config import GEMINI_API_KEY
from backend.config import EMBEDDING_MODEL
import numpy as np


client = genai.Client(api_key=GEMINI_API_KEY)

def embed_documents(texts: list[str]):
    """Batch-embed document pages."""
    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=texts,
        config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT"),
    )
    return np.array([e.values for e in response.embeddings], dtype=np.float32)
 
 
def embed_query(text: str):
    """Embed a single query string."""
    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
        config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY"),
    )
    return np.array(response.embeddings[0].values, dtype=np.float32)

async def extract_page(file_path):
    reader=PdfReader(file_path)
    return [
        {"page":i+1,"text":page.extract_text().strip()}
        for i,page in enumerate(reader.pages)
        if page.extract_text()
    ]


async def get_top_pages(pages,question,top_k=5):
    text=[p["text"] for p in pages]
    page_vector=embed_documents(text)
    query_vector=embed_query([question])[0]

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

    answer = await ask_gemini(prompt)

    return {"text":full_text,"answer":answer,"page_count":len(pages),"indexed_only":False}

