from bs4 import BeautifulSoup

def scrape_html(html):

    srcape=BeautifulSoup(html,"html.parser")

    titles=[]

    for h in srcape.select("h3"):

        titles.append(h.text)
    
    return titles
