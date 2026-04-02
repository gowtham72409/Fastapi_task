from pypdf import PdfReader
from backend.core.groq_client import ask_groq


def extract_pdf_pages(file_path: str) -> tuple[list[dict], int]:
    """
    Extract text per page. Returns ([{page, text}, ...], total_pages).
    """
    reader = PdfReader(file_path)
    pages = []
    for i, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if text:
            pages.append({"page": i, "text": text})
    return pages, len(reader.pages)


def build_indexed_context(pages: list[dict], max_chars: int = 12000) -> str:
    """Build a context string with clear page markers, truncated to max_chars."""
    chunks = []
    total = 0
    for p in pages:
        block = f"[Page {p['page']}]\n{p['text']}"
        if total + len(block) > max_chars:
            remaining = max_chars - total
            if remaining > 100:
                chunks.append(block[:remaining] + "\n...[truncated]")
            break
        chunks.append(block)
        total += len(block)
    return "\n\n".join(chunks)


async def pdf_agent(file_path: str, question: str = "") -> dict:
    """
    Upload-time call (no question): just index, return metadata, NO content shown.
    Question-time call: answer + page citations.
    """
    pages, page_count = extract_pdf_pages(file_path)

    if not pages:
        return {
            "text": "",
            "answer": "",
            "page_count": page_count,
            "truncated": False,
            "indexed_only": True,
        }

    full_text = "\n\n".join(f"[Page {p['page']}]\n{p['text']}" for p in pages)
    truncated = len(full_text) > 12000
    context   = build_indexed_context(pages)

    if not question:
        return {
            "text": full_text,
            "answer": "",          
            "page_count": page_count,
            "truncated": truncated,
            "indexed_only": True,
        }


    prompt = f"""You are a document analysis assistant with access to a PDF broken into numbered pages.

PDF content{" (truncated)" if truncated else ""}:
---
{context}
---

User question: {question}

Instructions:
- Answer clearly and concisely based ONLY on the document content above.
- After your answer, add a "Sources:" section listing the exact page numbers you used.
- Format sources as: Sources: Page 2, Page 4
- If the answer spans multiple pages, list all of them.
- If the answer is not found in the document, say so clearly."""

    answer = await ask_groq(prompt)

    return {
        "text": full_text,
        "answer": answer,
        "page_count": page_count,
        "truncated": truncated,
        "indexed_only": False,
    }
