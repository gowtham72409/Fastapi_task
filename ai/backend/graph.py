from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Dict

from backend.llm import get_llm
from backend.tools import open_url, search_google,execute_tool
from backend.memory import get_recent_history, get_relevant_context

llm = get_llm()

class AgentState(TypedDict):
    input: str
    history: List[Dict]
    context: List[str]
    plan: List[Dict]
    result: List[str]
    status: str

def planner(state: AgentState):
    history_text = "\n".join(
        [f"{m['role']}: {m['content']}" for m in state["history"]]
    )

    context_text = "\n".join(state["context"])

    prompt = f"""
    You are an intelligent AI agent.

    Conversation history:
    {history_text}

    Relevant past context:
    {context_text}

    Current input:
    {state['input']}

    Create JSON plan:
    [
      {{"action": "search", "query": "..."}},
      {{"action": "open_url", "url": "..."}}
    ]
    """

    response = llm.invoke(prompt)

    import json
    try:
        plan = json.loads(response.content)
    except:
        plan = [{"action": "chat", "message": state["input"]}]

    return {"plan": plan}

def executor(state):
    results = []

    for step in state["plan"]:
        result = execute_tool(step)
        results.append(result)

    return {"result": results}

def critic(state):
    return {"status": "success"}


def router(state):
    return END


builder = StateGraph(AgentState)

builder.add_node("planner", planner)
builder.add_node("executor", executor)
builder.add_node("critic", critic)

builder.set_entry_point("planner")

builder.add_edge("planner", "executor")
builder.add_edge("executor", "critic")
builder.add_edge("critic", END)

graph = builder.compile()