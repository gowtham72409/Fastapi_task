from google import genai
from backend.config import GEMINI_API_KEY

client = genai.Client(api_key=GEMINI_API_KEY)

call_counter = {"count": 0, "total_tokens": 0}

async def ask_gemini(prompt: str):
    try:
        response = await client.aio.models.generate_content(
            model="gemini-2.5-flash", 
            contents=prompt,
            config={"system_instruction": "You are an intelligent AI agent system."},
        )

        usage = response.usage_metadata
        tokens_used = usage.total_token_count if usage else 0

        call_counter["count"] += 1
        call_counter["total_tokens"] += tokens_used

        print(
            f"[Gemini] Call #{call_counter['count']} | "
            f"Tokens this call: {tokens_used} | "
            f"Total so far: {call_counter['total_tokens']}"
        )

        return response.text

    except Exception as e:
        return f"Gemini API Error: {str(e)}"