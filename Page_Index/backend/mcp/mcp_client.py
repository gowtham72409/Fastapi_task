import httpx
import json
from typing import Any, Dict

MCP_BASE = "http://localhost:8001"

async def list_mcp_tools() -> dict:
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{MCP_BASE}/mcp/tools", timeout=5)
        return r.json()

async def call_mcp_tool(tool: str, params: Dict[str, Any] = {}) -> Any:
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{MCP_BASE}/mcp/call",
            json={"tool": tool, "params": params},
            timeout=10,
        )
        return r.json()

async def resolve_tool(user_input: str) -> dict | None:
    """
    Very lightweight intent → tool resolver.
    In production this could itself call an LLM.
    """
    lower = user_input.lower()
    if "hubspot" in lower or "crm" in lower or "contact" in lower:
        if "create" in lower or "add" in lower:
            return {"tool": "hubspot_create_contact", "params": {}}
        if "deal" in lower:
            return {"tool": "hubspot_get_deals", "params": {"limit": 5}}
        return {"tool": "hubspot_get_contacts", "params": {"limit": 5}}
    if "search" in lower:
        return {"tool": "web_search_mcp", "params": {"query": user_input}}
    return None