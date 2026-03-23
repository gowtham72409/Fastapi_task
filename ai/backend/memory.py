import psycopg2
from backend.vector_store import add_to_vector_store, search_vector_store


conn = psycopg2.connect(
    dbname="ai_agent",
    user="postgres",
    password="password",   
    host="localhost",
    port="5432"
)

conn.autocommit = True
cursor = conn.cursor()

SESSION_ID = "user_1"



def save_message(role: str, content: str):
    try:
        cursor.execute(
            """
            INSERT INTO chat_history (session_id, role, content)
            VALUES (%s, %s, %s)
            """,
            (SESSION_ID, role, content)
        )

     
        add_to_vector_store(content)

    except Exception as e:
        print("DB Save Error:", e)


def get_recent_history(limit=5):
    try:
        cursor.execute(
            """
            SELECT role, content
            FROM chat_history
            WHERE session_id = %s
            ORDER BY created_at DESC
            LIMIT %s
            """,
            (SESSION_ID, limit)
        )

        rows = cursor.fetchall()

     
        rows.reverse()

        return [{"role": r[0], "content": r[1]} for r in rows]

    except Exception as e:
        print("DB Fetch Error:", e)
        return []



def get_relevant_context(query: str):
    try:
        return search_vector_store(query)
    except Exception as e:
        print("Vector Search Error:", e)
        return []

def clear_memory():
    try:
        cursor.execute(
            "DELETE FROM chat_history WHERE session_id = %s",
            (SESSION_ID,)
        )
    except Exception as e:
        print("Clear Error:", e)