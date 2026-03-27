from backend.core.groq_client import ask_groq

async def research_agent(task):
    prompt = f"""
    You are a research agent.
    Explain clearly and concisely:for factual questions, explanations, analysis

    {task}
    """
    return await ask_groq(prompt)
    # return await ask_groq(f"Explain clearly:\n{task}")

