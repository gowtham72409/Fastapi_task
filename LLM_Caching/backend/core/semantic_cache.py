import json 
import hashlib
import numpy as np
from sentence_transformers import SentenceTransformer
from backend.core.redis_client import redis
from backend.config import EMBEDDING_MODEL

model=SentenceTransformer(EMBEDDING_MODEL)

CACHE_PREFIX = "sem_cache:"
INDEX_KEY="sem_cache:index"
SIMILARITY_THRESHOLDE = 0.85
CACHE_TTL=60 * 60 * 24

def embedd(text:str):
    return model.encode([text])[0]

def cosine_similarity(vec1,vec2):
    a=np.array(vec1)
    b=np.array(vec2)
    return float(np.dot(a,b)/(np.linalg.norm(a) * np.linalg.norm(b)+1e-9))

async def get_cache(query:str):
    """Return cached result if a semantically similar query exists."""
    query_vec=embedd(query)

    raw_index=await redis.get(INDEX_KEY)

    if not raw_index:
        return None
    
    index=json.loads(raw_index)
    best_score, best_key=0.0,None

    for entry in index:
        stored_vec = np.array(entry["vector"], dtype=np.float32)
        score = cosine_similarity(query_vec, stored_vec)
        if score > best_score:
            best_score, best_key = score, entry["key"]

    if best_score >= SIMILARITY_THRESHOLDE and best_key:
        raw = await redis.get(best_key)
        if raw:
            print(f"[SemanticCache] HIT  score={best_score:.3f}  key={best_key}")
            return json.loads(raw)

    print(f"[SemanticCache] MISS  best_score={best_score:.3f}")
    return None
    
async def set_cached(query: str, result: dict):
    """Store result and update the embedding index."""
    query_vec=embedd(query)
    cache_key=CACHE_PREFIX+hashlib.sha3_256(query.encode()).hexdigest()[:16]

    await redis.setex(cache_key,CACHE_TTL,json.dumps(result))


    raw_index=await redis.get(INDEX_KEY)
    index=json.loads(raw_index) if raw_index else []                           

    index.append({
        "key":    cache_key,
        "query":  query,
        "vector": query_vec.tolist(),
    })

    if len(index) > 1000:
        index = index[-1000:]

    await redis.setex(INDEX_KEY, CACHE_TTL * 7, json.dumps(index))
    print(f"[SemanticCache] STORED  key={cache_key}")


    