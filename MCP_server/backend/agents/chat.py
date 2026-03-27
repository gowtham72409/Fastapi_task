from backend.core.groq_client import ask_groq
import json

async def chat_agent(task: str, memory: dict) -> str:
    mcp_context = ""
    if memory.get("mcp"):
        try:
            mcp_data = json.loads(memory["mcp"]) if isinstance(memory["mcp"], str) else memory["mcp"]
            mcp_context = f"\n\nMCP Tool Result:\n{json.dumps(mcp_data, indent=2)}"
        except Exception:
            mcp_context = f"\n\nMCP Result: {memory.get('mcp')}"

    research_ctx = f"\n\nResearch:\n{memory['research']}" if memory.get("research") else ""
    code_ctx     = f"\n\nCode:\n{memory['code']}"         if memory.get("code")     else ""

    prompt = f"""You are a helpful AI assistant connected to an MCP server that can query CRM systems (HubSpot), search the web, and more.

User request: {task}{mcp_context}{research_ctx}{code_ctx}


Respond naturally and helpfully. If MCP data is present, summarise it clearly for the user."""

    return await ask_groq(prompt)

