from bs4 import BeautifulSoup


class ScraperTool:

    def scrape_titles(self, html):

        soup = BeautifulSoup(html, "html.parser")

        titles = []

        for h in soup.find_all("h2"):
            titles.append(h.text)

        return titles