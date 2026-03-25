import asyncpg
from backend.config import DATABASE_URL

async def get_db_pool():
    return await asyncpg.create_pool(DATABASE_URL)