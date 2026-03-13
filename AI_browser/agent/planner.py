# import json
# import os
# from openai import OpenAI

# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# SYSTEM_PROMPT = """
# You are an automation planner.

# Convert the user task into steps.

# Available actions:
# open(url)
# search(query)
# scrape()

# Return JSON list of steps.
# """

# def plan_task(task):

#     response = client.chat.completions.create(
#         model="gpt-4o-mini",
#         messages=[
#             {"role": "system", "content": SYSTEM_PROMPT},
#             {"role": "user", "content": task}
#         ]
#     )

#     plan = response.choices[0].message.content

#     return json.loads(plan)
import requests
import json
import re

OLLAMA_URL = "http://localhost:11434/api/generate"


def extract_json(text):
    """
    Extract JSON array from LLM response
    """
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        return match.group(0)
    return None


def plan_task(task):

    prompt = f"""
You are an AI browser planner.

Convert the user task into JSON steps.

Actions allowed:
open, search, click, type, scrape_titles

User task:
{task}

Return ONLY JSON array.
"""

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": "llama3",
            "prompt": prompt,
            "stream": False
        }
    )

    data = response.json()

    print("OLLAMA RESPONSE:", data)

    plan_text = data["response"]

    # Extract JSON from response
    json_text = extract_json(plan_text)

    if not json_text:
        raise Exception("No JSON found in LLM response")

    plan = json.loads(json_text)

    return plan