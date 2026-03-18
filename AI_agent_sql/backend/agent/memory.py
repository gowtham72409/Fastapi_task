from backend.db import conn
from backend.agent.embedding import embedd

def save_memory(text):

    emb=embedd(text)

    cur=conn.cursor()
    cur.execute(
    "INSERT INTO memory (content,embedding) VALUES (%s,%s)",
    (text,emb)  
    )
    conn.commit()

def retrieve_memory(query):

    emb=embedd(query)

    cur=conn.cursor()

    cur.execute(
    "SELECT content FROM memory ORDER BY embedding <-> %s::vector LIMIT 5",
    (emb,)
    )

    return [r[0] for r in cur.fetchall()]