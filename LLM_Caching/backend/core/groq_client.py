from groq import Groq
from backend.config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)

call_counter = {"count": 0, "total_tokens": 0}

async def ask_groq(prompt: str):
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",  # Uses 8b model to bypass 70b token limits
            messages=[
                {"role": "system", "content": "You are an intelligent AI agent system."},
                {"role": "user", "content": prompt}
            ]
        )
        call_counter["count"] += 1
        call_counter["total_tokens"] += response.usage.total_tokens
        print(f"[Groq] Call #{call_counter['count']} | "
              f"Tokens this call: {response.usage.total_tokens} | "
              f"Total so far: {call_counter['total_tokens']}")

        return response.choices[0].message.content
    except Exception as e:
        return f"Groq API Error: {str(e)}"