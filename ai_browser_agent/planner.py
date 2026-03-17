import ollama
import json
import re
from config import MODEL, SYSTEM_PROMPT


def clean_json(text):
    """
    Extract JSON list and fix common formatting issues
    """

    # extract JSON array
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if not match:
        return None

    json_text = match.group(0)

    # fix common errors
    json_text = json_text.replace("}}", "}")
    json_text = json_text.replace("\n", "")

    return json_text


def create_plan(task):

    response = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": task}
        ]
    )

    content = response["message"]["content"]

    print("\nLLM RAW RESPONSE:\n", content)

    json_text = clean_json(content)

    if not json_text:
        print("Planner error: JSON not found")
        return []

    try:
        plan = json.loads(json_text)
        return plan
    except Exception as e:
        print("JSON parse error:", e)
        print("Extracted JSON:", json_text)
        return []