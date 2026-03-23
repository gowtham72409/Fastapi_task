from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import pickle
import os

model = SentenceTransformer("all-MiniLM-L6-v2")

INDEX_FILE = "faiss_index.bin"
DATA_FILE = "faiss_data.pkl"

if os.path.exists(INDEX_FILE):
    index = faiss.read_index(INDEX_FILE)
    with open(DATA_FILE, "rb") as f:
        texts = pickle.load(f)
else:
    index = faiss.IndexFlatL2(384)
    texts = []


def add_to_vector_store(text):
    embedding = model.encode([text])
    index.add(np.array(embedding).astype("float32"))
    texts.append(text)

    faiss.write_index(index, INDEX_FILE)
    with open(DATA_FILE, "wb") as f:
        pickle.dump(texts, f)


def search_vector_store(query, k=3):
    if len(texts) == 0:
        return []

    embedding = model.encode([query])
    D, I = index.search(np.array(embedding).astype("float32"), k)

    return [texts[i] for i in I[0] if i < len(texts)]