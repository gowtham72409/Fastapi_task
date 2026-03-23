import re
import json
import os
from openai import OpenAI # pip install openai

# Initialize Groq Client
client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key="api_key"
)

SYSTEM_PROMPT = """
You are an AI agent planner. 
Convert user input into a JSON array of actions.

Available actions:
1. {"action": "open_url", "url": "<url>"}
2. {"action": "search", "query": "<query>"}

Rules:
- If the user says "open google", return [{"action": "open_url", "url": "https://www.google.com"}]
- If the user says "open youtube", return [{"action": "open_url", "url": "https://www.youtube.com"}]
- Always return a valid JSON array.
"""

def create_plan(user_input):
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile", # Groq's powerful model
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_input}
            ],
            response_format={ "type": "json_object" } # Groq supports JSON mode
        )

        raw = response.choices[0].message.content
        return json.loads(raw).get("actions", json.loads(raw)) # Handle different JSON structures
    
    except Exception as e:
        print(f"Groq Planner Error: {e}")
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