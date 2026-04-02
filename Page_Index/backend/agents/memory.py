import json
import datetime

async def save_task_memory(pool, task_id, user_input, subtasks, results, evaluation, chat):
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO ai_task_memory (
                task_id,
                user_input,
                planner_output,
                research_result,
                code_result,
                audio_result,
                video_result,
                evaluation_result,
                chat_response,
                created_at,
                updated_at,
                pdf_file,
                audio_file,
                video_file
            ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14)
            """,
            task_id,
            user_input,
            json.dumps(subtasks) if subtasks else None,
            results.get("research"),
            results.get("code"),
            results.get("audio"),
            results.get("video"),
            evaluation,
            chat,
            datetime.datetime.now(),
            datetime.datetime.now(),
            results.get("pdf_file"),
            results.get("audio_file"),
            results.get("video_file")
        )