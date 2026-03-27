from backend.core.groq_client import ask_groq

async def evaluation_agent(results):
    prompt = f"""
    Evaluate the following outputs and summarize quality:

    {results}
    """
    return await ask_groq(prompt)
    # return await ask_groq(f"Evaluate:\n{results}")

