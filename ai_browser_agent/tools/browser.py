from playwright.sync_api import sync_playwright


class BrowserTool:

    def __init__(self):

        self.playwright = sync_playwright().start()

        self.browser = self.playwright.chromium.launch(
            headless=False,
            args=["--start-maximized"]
        )

        self.context = self.browser.new_context(no_viewport=True)

        self.page = self.context.new_page()

    def open_url(self, url):

        print("Opening:", url)

        self.page.goto(url, timeout=60000)

    def click(self, selector):
        print("Clicking:", selector)
        self.page.locator(selector).click()

    def search(self, query):

        try:
            self.page.fill("input[type='text']", query)
            self.page.keyboard.press("Enter")
        except:
            print("Search box not found")

    def type(self, selector, text):
        if not text:
            print("Skipping empty text")
            return

    # Wait for element
        self.page.wait_for_selector(selector, timeout=10000)
        self.page.locator(selector).fill(text)

    def get_html(self):

        return self.page.content()
    
    def wait(self, ms):
        self.page.wait_for_timeout(ms)

    def scroll_to_bottom(self):
        self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

    def screenshot(self, path="page.png", full_page=False):
        print("Taking screenshot...")
        self.page.screenshot(path=path, full_page=full_page)

    # def close(self):

    #     self.browser.close()
    #     self.playwright.stop()