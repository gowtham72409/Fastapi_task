from groq import Groq
from backend.config import GROQ_API_KEY


client = Groq(api_key=GROQ_API_KEY)

async def ask_groq(prompt: str):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile", 
        messages=[
            {"role": "system", "content": "You are an intelligent AI agent system."},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content

