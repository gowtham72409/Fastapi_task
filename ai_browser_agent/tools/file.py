import requests


class FileTool:

    def download(self, url, filename):

        r = requests.get(url)

        with open(filename, "wb") as f:
            f.write(r.content)

        print("Downloaded:", filename)