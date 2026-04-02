import asyncio
import asyncpg
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.config import DATABASE_URL

async def init_db():
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS ai_task_memory (
                task_id VARCHAR(255) PRIMARY KEY,
                user_input TEXT,
                planner_output TEXT,
                research_result TEXT,
                code_result TEXT,
                audio_result TEXT,
                video_result TEXT,
                evaluation_result TEXT,
                chat_response TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                pdf_file BYTEA,
                audio_file BYTEA,
                video_file BYTEA
            )
        """)
        
        try:
            await conn.execute("ALTER TABLE ai_task_memory ADD COLUMN pdf_file BYTEA;")
        except Exception:
            pass
        try:
            await conn.execute("ALTER TABLE ai_task_memory ADD COLUMN audio_file BYTEA;")
        except Exception:
            pass
        try:
            await conn.execute("ALTER TABLE ai_task_memory ADD COLUMN video_file BYTEA;")
        except Exception:
            pass
        await conn.close()
        print("Table ai_task_memory created successfully.")
    except Exception as e:
        print(f"Error creating table: {e}")

if __name__ == "__main__":
    asyncio.run(init_db())
