from langgraph.graph import StateGraph
from backend.agent.planner import plan_steps
from backend.agent.memory import retrieve_memory, save_memory
from backend.agent.tools import BrowserTools
from typing import TypedDict

tools = BrowserTools()

class State(TypedDict):
    input: str
    memory: str
    output: str

async def planner_node(state: State):
    print("PLANNER RECEIVED:", state)

    user_input = state.get("input")
    if not user_input:
        raise ValueError("Missing 'input' in state")

    return {
        "input": user_input,
        "memory": "sample memory"
    }

async def execute_plan(browser_manager, plan):
    results = []
    for step in plan:
        action = step.get("action")
        if action == "open_url":
            res = await browser_manager.open_url(step.get("url"))
            results.append(res)
        elif action == "type":
            res = await browser_manager.type(step.get("selector"), step.get("text"))
            results.append(res)
        elif action == "search":
            await browser_manager.open_url("https://www.google.com")
            res = await browser_manager.type("input[name='q']", step.get("query"))
            await browser_manager.page.press("input[name='q']", "Enter")
            results.append(f"Searched for {step.get('query')}")
    return results

async def responder_node(state: State):
    return {
        "input": state["input"],
        "memory": state["memory"],
        "output": f"Response: {state['input']}"
    }

builder = StateGraph(State)

builder.add_node("planner", planner_node)
builder.add_node("responder", responder_node)

builder.add_edge("planner", "responder")

builder.set_entry_point("planner")
builder.set_finish_point("responder")

graph = builder.compile()