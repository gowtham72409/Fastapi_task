from pypdf import PdfReader #-> used to read pdf files in python
from sentence_transformers import SentenceTransformer #-> text convert in embedding (vector)
import faiss #->uesd to fast similarity search betwwen vecter
import numpy as np #->Used for handling arrays and numerical data.
from transformers import pipeline  #->mports pipeline from Hugging Face Transformers.Used to run LLM models easily.

embed_model = SentenceTransformer("all-MiniLM-L6-v2")

generator = pipeline("text-generation", model="distilgpt2") #->Loads a text generation model.

texts = []
page_numbers = []
index = None


def process_book(file_path):
    global texts, page_numbers, index

    reader = PdfReader(file_path)

    all_chunks = []
    pages = []

    chunk_size = 500

    for page_num, page in enumerate(reader.pages):

        text = page.extract_text()

        chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

        for chunk in chunks:
            all_chunks.append(chunk)
            pages.append(page_num + 1)

    texts = all_chunks
    page_numbers = pages

    embeddings = embed_model.encode(texts)

    dim = embeddings.shape[1]

    index = faiss.IndexFlatL2(dim)
    index.add(np.array(embeddings))

    return "Book processed with page index"


def ask_question(question):
    global texts, page_numbers, index

    q_embed = embed_model.encode([question])

    D, I = index.search(np.array(q_embed), k=3)

    context = ""
    sources = []

    for i in I[0]:
        context += texts[i] + "\n"
        sources.append(page_numbers[i])

    prompt = f"""
    Context:
    {context}

    Question: {question}
    Answer:
    """

    result = generator(prompt, max_length=200, num_return_sequences=1)

    answer = result[0]["generated_text"]

    return {
        "answer": answer,
        "source_pages": list(set(sources))
    }