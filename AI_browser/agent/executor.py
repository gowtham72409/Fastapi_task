from browser_manager import BrowserManager
from tools.scraper import scrape_html
from tools.downloader import get_file

class ActionExecutor:

    def __init__(self):
        self.browser = BrowserManager()

    async def start(self):
        await self.browser.start()

    async def execute(self, action, params):

        if action == "open":
            return await self.browser.open(params["url"])

        elif action == "search":
            await self.browser.type("input[name='q']", params["query"])
            await self.browser.page.keyboard.press("Enter")
            return "Search done"

        elif action == "scrape":
            html = await self.browser.get_html()
            return scrape_html(html)
        

