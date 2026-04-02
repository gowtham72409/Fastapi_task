from groq import Groq
from backend.config import GROQ_API_KEY


client = Groq(api_key=GROQ_API_KEY)

async def ask_groq(prompt: str):
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",  # Uses 8b model to bypass 70b token limits
            messages=[
                {"role": "system", "content": "You are an intelligent AI agent system."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Groq API Error: {str(e)}"

