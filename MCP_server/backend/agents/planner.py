from backend.core.groq_client import ask_groq
import json

async def planner_agent(user_input: str):
    prompt = f"""
    You are a planner AI.

    Decide which agents to use for this task:
    Available agents:
    - research   → for factual questions, explanations, analysis
    - code       → for code generation, debugging, programming tasks
    - audio      → for audio transcription tasks
    - video      → for video processing tasks
    - mcp        → for CRM actions (HubSpot contacts, deals), Slack messages, Notion pages, GitHub issues
    - chat       → for general conversation, greetings, simple questions

    Return ONLY valid JSON like:
    {{"agents": ["research", "chat"]}}

    Task:
    {user_input}
    """

    response = await ask_groq(prompt)

    try:
        response = response.replace("```json", "").replace("```", "").strip()
        data = json.loads(response)
        return data["agents"]
    except Exception:
        return ["chat"]