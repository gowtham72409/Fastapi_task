import requests

def get_file(url,filename):

    r=requests.get(url)

    with open(filename,"/wb") as f:
        f.write(r.content)

    return "File Downloaded"