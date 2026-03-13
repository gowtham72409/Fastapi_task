from browser_tool import BrowserTools
from tasks import get_macbook_price


class AIAgent:

    def __init__(self):

        self.browser = BrowserTools()


    def run(self, command):

        if "macbook" in command and "amazon" in command:

            self.macbook_price()


    def macbook_price(self):

        task = get_macbook_price()

        self.browser.open_url(task["url"])

        self.browser.search(
            task["search_selector"],
            task["search_text"]
        )

        price = self.browser.get_text(
            task["price_selector"]
        )

        print("MacBook Price:", price)