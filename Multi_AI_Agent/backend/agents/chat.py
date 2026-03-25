from backend.core.groq_client import ask_groq

async def chat_agent(task, memory):
    prompt = f"""
    You are a helpful chatbot.
    Answer naturally:

    {task}
    """
    
    return await ask_groq(prompt)
    # return await ask_groq(f"Answer:\n{task}\nContext:{memory}")