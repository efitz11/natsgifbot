from urllib.request import urlopen, Request
import json
from datetime import datetime, timedelta
from xml.etree import ElementTree

def get_recaps():
    now = datetime.now() - timedelta(days=1)
    date = str(now.year) + "-" + str(now.month).zfill(2) + "-" + str(now.day).zfill(2)
    url = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=" + date
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    s = json.loads(urlopen(req).read().decode("utf-8"))
    games = s['dates'][0]['games']
    recaps = []
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
                recaps.append((title,link,duration))
    return recaps


def find_fastcast():
    url = "https://search-api.mlb.com/svc/search/v2/mlb_global_sitesearch_en/sitesearch?hl=true&facet=type&expand=partner.media&q=fastcast&page=1"
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    s = json.loads(urlopen(req).read().decode("utf-8"))
    result = s['docs'][0]
    title = result['title']
    if "MLB.com FastCast" in title:
        blurb = result['blurb']
        url = result['url']
        one=url[-3]
        two=url[-2]
        thr=url[-1]
        cid = url[url.index('c-')+2:]
        mlburl = "http://www.mlb.com/gen/multimedia/detail/%s/%s/%s/%s.xml"%(one,two,thr,cid)
        try:
            req = Request(mlburl, headers={'User-Agent' : "ubuntu"})
            tree = ElementTree.fromstring(urlopen(req).read().decode("utf-8"))
            media = tree.findall('url')
            for tag in media:
                if "2500K.mp4" in tag.text:
                    url = tag.text
                    break
        except Exception as e:
            print("error parsing/receiving XML from url " + mlburl)
            return

        duration = result['duration']
        print("[%s](%s) - %s\n" % (blurb,url,duration))
        return (blurb,url,duration)

if __name__ == "__main__":
    find_fastcast()
    get_recaps()
