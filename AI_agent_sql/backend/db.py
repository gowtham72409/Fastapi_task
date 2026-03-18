import psycopg2

conn=psycopg2.connect(
    dbname= "agent_db",
    user= "postgres",
    password= "your_password",
    host= "localhost",
    port= "5432"
)

def init_db():
    cur = conn.cursor()

    cur.execute("CREATE EXTENSION IF NOT EXISTS vector")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS chat_history (
        id SERIAL PRIMARY KEY,
        session_id TEXT,
        role TEXT,
        message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS memory (
        id SERIAL PRIMARY KEY,
        content TEXT,
        embedding VECTOR(384)
    )
    """)

    conn.commit()
    cur.close()
