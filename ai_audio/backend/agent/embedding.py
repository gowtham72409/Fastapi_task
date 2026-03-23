from sentence_transformers import SentenceTransformer

model=SentenceTransformer("all-MiniLM-L6-v2")

def embedd(text):
    return model.encode(text).tolist()