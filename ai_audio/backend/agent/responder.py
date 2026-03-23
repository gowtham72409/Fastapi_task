from openai import OpenAI

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key="api_key"
)

def generate_answer(user_input):
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant", # Faster model for simple chat
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant"},
                {"role": "user", "content": user_input}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating response: {e}"