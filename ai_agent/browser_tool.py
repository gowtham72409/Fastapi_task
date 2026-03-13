from playwright.sync_api import sync_playwright

class BrowserTools:

    def __init__(self):

        self.playwright = sync_playwright().start()

        self.browser = self.playwright.chromium.launch(
            headless=False
        )

        self.context = self.browser.new_context()

        self.page = self.context.new_page()


    def open_url(self, url):

        self.page.goto(url)


    def search(self, selector, text):

        self.page.fill(selector, text)

        self.page.press(selector, "Enter")


    def get_text(self, selector):

        self.page.wait_for_selector(selector)

        return self.page.inner_text(selector)


    def click(self, selector):

        self.page.click(selector)


    def close(self):

        self.browser.close()

        self.playwright.stop()