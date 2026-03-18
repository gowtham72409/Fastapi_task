import re
import ollama
import json

SYSTEM_PROMPT = """
You are an AI agent planner. 
Convert user input into a JSON array of actions.

Available actions:
1. open_url -> {"action": "open_url", "url": "<url>"}
2. search -> {"action": "search", "query": "<query>"}

Rules:
- If the user wants a video or specific info, use "search".
- Do not use placeholders like "result_from_search".
- Always return a JSON array.
"""

def create_plan(user_input):
    response = ollama.chat(
        model="phi3",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input}
        ]
    )

    raw = response['message']['content']
    clean_raw = raw.replace("```json", "").replace("```", "").strip()
    print("RAW PLAN:", raw)

    try:
        return json.loads(clean_raw)
    
    except Exception as e:
        print(f"JSON Parse Error: {e}")
        # Only fallback if it's truly broken
        return [{"action": "search", "query": user_input}]
    
def extract_url(text):
    match = re.search(r'\[.*\]', text, re.DOTALL)
    return match.group(0) if match else "[]"



def plan_steps(user_input: str):
    user_input = user_input.lower()

    steps = []

    url = extract_url(user_input)

    # 🔹 OPEN WEBSITE
    if "open" in user_input and url:
        steps.append({
            "action": "open_url",
            "url": url
        })

    # 🔹 SEARCH ACTION
    if "search" in user_input:
        query = user_input.replace("search", "").strip()

        steps.append({
            "action": "open_url",
            "url": "https://www.google.com"
        })

        steps.append({
            "action": "type",
            "selector": "input[name='q']",
            "text": query
        })

        steps.append({
            "action": "press_enter"
        })

    # 🔹 SCRAPE
    if "scrape" in user_input or "get titles" in user_input:
        steps.append({
            "action": "scrape",
            "selector": "h1, h2, h3"
        })

    # 🔹 DEFAULT RESPONSE
    if not steps:
        steps.append({
            "action": "respond",
            "text": "I understood your request but no action matched."
        })

    return steps