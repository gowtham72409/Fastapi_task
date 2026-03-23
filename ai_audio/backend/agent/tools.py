
from playwright.async_api import async_playwright

class BrowserTools:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    async def start(self):
        """Initialize browser (call once at startup)"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=False)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()

    async def open_url(self, url: str):
        await self.page.goto(url)
        return f"Opened {url}"

    async def click(self, selector: str):
        await self.page.click(selector)
        return f"Clicked {selector}"

    async def type(self, selector: str, text: str):
        await self.page.fill(selector, text)
        return f"Typed into {selector}"

    async def scrape(self, selector: str):
        elements = await self.page.locator(selector).all_inner_texts()
        return elements

    async def get_title(self):
        return await self.page.title()

    async def close(self):
        await self.browser.close()
        await self.playwright.stop()