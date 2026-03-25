from backend.core.groq_client import ask_groq
import json

async def planner_agent(user_input: str):
    prompt = f"""
    You are a planner AI.

    Decide which agents to use for this task:
    Available agents:
    - research
    - code
    - audio
    - video
    - chat

    Return ONLY JSON like:
    {{"agents": ["research", "code","chat]}}

    Task:
    {user_input}
    """

    response = await ask_groq(prompt)

    try:
        response = response.replace("```json", "").replace("```", "")
        data = json.loads(response)
        return data["agents"]
    except:
        return ["chat"]