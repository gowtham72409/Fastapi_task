import os
import json
import asyncio
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.config import HUBSPOT_ACCESS_TOKEN

mcp_app = FastAPI(title="Own MCP Server")

mcp_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

HUBSPOT_TOKEN = HUBSPOT_ACCESS_TOKEN


TOOLS: Dict[str, dict] = {
    "hubspot_get_contacts": {
        "description": "Fetch recent HubSpot CRM contacts",
        "provider": "hubspot",
        "params": ["limit"],
    },
    "hubspot_create_contact": {
        "description": "Create a new HubSpot contact",
        "provider": "hubspot",
        "params": ["email", "firstname", "lastname"],
    },
    "hubspot_get_deals": {
        "description": "List open HubSpot deals",
        "provider": "hubspot",
        "params": ["limit"],
    },
    "echo": {
        "description": "Echo back a message (built-in test tool)",
        "provider": "builtin",
        "params": ["message"],
    },
    "web_search_mcp": {
        "description": "Search the web via MCP layer",
        "provider": "builtin",
        "params": ["query"],
    },
}



HUBSPOT_BASE = "https://api.hubapi.com"

async def hs_get_contacts(limit: int = 5) -> dict:
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{HUBSPOT_BASE}/crm/v3/objects/contacts",
            headers={"Authorization": f"Bearer {HUBSPOT_TOKEN}"},
            params={"limit": limit, "properties": "firstname,lastname,email"},
            timeout=10,
        )
        return r.json()

async def hs_create_contact(email: str, firstname: str = "", lastname: str = "") -> dict:
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{HUBSPOT_BASE}/crm/v3/objects/contacts",
            headers={"Authorization": f"Bearer {HUBSPOT_TOKEN}", "Content-Type": "application/json"},
            json={"properties": {"email": email, "firstname": firstname, "lastname": lastname}},
            timeout=10,
        )
        return r.json()

async def hs_get_deals(limit: int = 5) -> dict:
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{HUBSPOT_BASE}/crm/v3/objects/deals",
            headers={"Authorization": f"Bearer {HUBSPOT_TOKEN}"},
            params={"limit": limit, "properties": "dealname,amount,dealstage"},
            timeout=10,
        )
        return r.json()



@mcp_app.get("/mcp/tools")
async def list_tools():
    """Returns all available MCP tools."""
    return {"tools": TOOLS}

class CallRequest(BaseModel):
    tool: str
    params: Dict[str, Any] = {}

@mcp_app.post("/mcp/call")
async def call_tool(req: CallRequest):
    tool_name = req.tool
    params = req.params

    if tool_name not in TOOLS:
        return JSONResponse(status_code=404, content={"error": f"Tool '{tool_name}' not found"})

    tool = TOOLS[tool_name]

    try:
        
        if tool["provider"] == "builtin":
            if tool_name == "echo":
                return {"result": params.get("message", "")}

            if tool_name == "web_search_mcp":
               
                return {"result": f"[MCP web search] Results for: {params.get('query', '')}"}

        
        if tool["provider"] == "hubspot":
            if not HUBSPOT_TOKEN:
                return {"error": "HUBSPOT_ACCESS_TOKEN not configured"}

            if tool_name == "hubspot_get_contacts":
                data = await hs_get_contacts(int(params.get("limit", 5)))
                return {"result": data}

            if tool_name == "hubspot_create_contact":
                data = await hs_create_contact(
                    params.get("email", ""),
                    params.get("firstname", ""),
                    params.get("lastname", ""),
                )
                return {"result": data}

            if tool_name == "hubspot_get_deals":
                data = await hs_get_deals(int(params.get("limit", 5)))
                return {"result": data}

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

    return {"error": "Unknown handler"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(mcp_app, host="0.0.0.0", port=8001)