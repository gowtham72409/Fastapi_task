from playwright.async_api import async_playwright
from config import BROWSER_HEADLESS

class BrowserManager:

    async def start(self):
        self.playwright = await async_playwright().start()

        self.browser = await self.playwright.chromium.launch(
            headless=BROWSER_HEADLESS
        )

        self.page = await self.browser.new_page()

    async def open(self, url):
        await self.page.goto(url)
        return "Website opened"

    async def click(self, selector):
        await self.page.click(selector)
        return "Clicked"

    async def type(self, selector, text):
        await self.page.fill(selector, text)
        return "Typed"

    async def get_html(self):
        return await self.page.content()

