from backend.core.groq_client import ask_groq

async def code_agent(task):
    prompt = f"""
    You are a coding assistant.
    Generate clean, correct Python code for:for code generation, debugging, programming tasks

    {task}
    """
    return await ask_groq(prompt)
    # return await ask_groq(f"Generate Python code:\n{task}")
