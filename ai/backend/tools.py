from playwright.sync_api import sync_playwright

browser_instance = None

def get_browser():
    global browser_instance
    if browser_instance is None:
        p = sync_playwright().start()
        browser_instance = p.chromium.launch(headless=False)
    return browser_instance

def open_url(url: str):
    try:
        browser = get_browser()
        page = browser.new_page()
        page.goto(url)

        return f"Opened URL: {url}"

    except Exception as e:
        return f"Error opening URL: {str(e)}"


def search_google(query: str):
    try:
        browser = get_browser()
        page = browser.new_page()

        page.goto("https://www.google.com")
        page.fill("input[name=q]", query)
        page.keyboard.press("Enter")

        return f"Searched Google for: {query}"

    except Exception as e:
        return f"Search failed: {str(e)}"


def chat_response(message: str):

    return f"AI says: {message}"


def execute_tool(action: dict):
    action_type = action.get("action")

    if action_type == "open_url":
        return open_url(action.get("url"))

    elif action_type == "search":
        return search_google(action.get("query"))

    elif action_type == "chat":
        return chat_response(action.get("message"))

    return "Unknown action"