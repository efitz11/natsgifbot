from urllib.request import urlopen, Request
import json
from datetime import datetime, timedelta

def get_recaps():
    now = datetime.now() - timedelta(days=1)
    date = str(now.year) + "-" + str(now.month).zfill(2) + "-" + str(now.day).zfill(2)
    url = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=" + date
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    s = json.loads(urlopen(req).read().decode("utf-8"))
    games = s['dates'][0]['games']
    for game in games:
        content = "https://statsapi.mlb.com" + game['content']['link']
        req = Request(content, headers={'User-Agent' : "ubuntu"})
        c = json.loads(urlopen(req).read().decode("utf-8"))
        for item in c['highlights']['live']['items']:
            if item['title'].startswith("Recap:"):
                title = item['title']
                link = item['playbacks'][3]['url']
                duration = item['duration'][3:]
                print("[%s](%s) - %s\n" % (title,link,duration))
        # highlights.live.items[1].playbacks

if __name__ == "__main__":
    get_recaps()
