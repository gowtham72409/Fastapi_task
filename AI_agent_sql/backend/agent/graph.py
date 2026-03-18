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


# async def execute_plan(page, plan):
#     results = []

#     for step in plan:
#         action = step.get("action")

#         if action == "open_url":
#             url = step.get("url")
#             await page.goto(url)
#             results.append(f"Opened {url}")

#         elif action == "search":
#             query = step.get("query")
#             await page.fill("input[name='q']", query)
#             await page.press("input[name='q']", "Enter")
#             results.append(f"Searched {query}")

#         elif action == "scrape":
#             selector = step.get("selector")
#             data = await page.locator(selector).all_inner_texts()
#             results.append(data)

#     return results

async def execute_plan(page, plan):
    results = []
    
    # Ensure plan is a list
    if isinstance(plan, str):
        import json
        plan = json.loads(plan)

    for step in plan:
        # Safety check: if step is a string, we can't use .get()
        if not isinstance(step, dict):
            print(f"Skipping invalid step: {step}")
            continue

        action = step.get("action")

        if action == "open_url":
            url = step.get("url")
            await page.goto(url)
            results.append(f"Opened {url}")

        elif action == "search":
            query = step.get("query")
            # Navigate to google first if not already there
            await page.goto("https://www.google.com")
            await page.fill("input[name='q']", query)
            await page.press("input[name='q']", "Enter")
            results.append(f"Searched {query}")
            
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