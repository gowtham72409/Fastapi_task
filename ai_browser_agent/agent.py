from planner import create_plan
from tools.browser import BrowserTool
from tools.scraper import ScraperTool
from tools.file import FileTool

import json

def safe_parse(json_str):
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print("JSON parse error:", e)
        return []


class AIAgent:

    def __init__(self):

        self.browser = BrowserTool()
        self.scraper = ScraperTool()
        self.file_tool = FileTool()

    def execute(self, steps):

        for step in steps:

            action = step.get("action")

            if action == "open_url":
                self.browser.open_url(step["url"])

            elif action == "search":
                query = step.get("query") or step.get("value") or step.get("text")
                if query:
                    self.browser.search(query)
                else:
                    self.browser.click("input[type='submit'], #nav-search-submit-button")

            elif action == "click":
                self.browser.click(step["selector"])

            elif action == "type":
                selector = step.get("selector") or "input[type='text']"
                text = step.get("text") or step.get("value") or step.get("query")
                self.browser.type(selector, text)
    # If text is '\r', simulate Enter
                if text == "\r":
                    self.page.keyboard.press("Enter")
                if text is None:
                    print("No text provided for type, skipping.")
                else:
                    print("Typing:", text, "into:", selector)
                    self.browser.type(selector, text) 

            elif action == "wait":
                ms = step.get("milliseconds", 2000)
                self.browser.wait(ms)

            elif action == "scrape":
                selector = step.get("selector", "body")
                texts = self.page.locator(selector).all_inner_texts()
                print("Scraped Titles:")
                for t in texts:
                    print("-", t)

                    if step.get("screenshot"):
                        filename = step.get("filename", "screenshot")
                        self.page.screenshot(path=f"{filename}.png", full_page=True)

            elif action == "download":
                self.file_tool.download(step["url"], step["filename"])

            elif action == "screenshot":
                path = step.get("path", "page.png")
                full = step.get("full_page", False)
                self.browser.screenshot(path, full)

    def run(self, task):

        plan = create_plan(task)

        print("PLAN:", plan)

        self.execute(plan)

    # In tools/browser.py
    def close(self):
        input("Press Enter to close the browser...")
        self.browser.close()
        self.playwright.stop()