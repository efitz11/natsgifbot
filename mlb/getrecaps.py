from urllib.request import urlopen, Request
import json
from datetime import datetime, timedelta
from xml.etree import ElementTree
import sys

def get_recaps(return_str=False):
    now = datetime.now() - timedelta(days=1)
    date = str(now.year) + "-" + str(now.month).zfill(2) + "-" + str(now.day).zfill(2)
    url = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=" + date
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    s = json.loads(urlopen(req).read().decode("utf-8"))
    games = s['dates'][0]['games']
    recaps = []
    output = ""
    for game in games:
        content = "https://statsapi.mlb.com" + game['content']['link']
        req = Request(content, headers={'User-Agent' : "ubuntu"})
        c = json.loads(urlopen(req).read().decode("utf-8"))
        for item in c['highlights']['live']['items']:
            if item['title'].startswith("Recap:"):
                title = item['title']
                link = item['playbacks'][3]['url']
                duration = item['duration'][3:]
                s = "[%s](%s) - %s\n" % (title, link, duration)
                print(s)
                output = output + s + "\n"
                recaps.append((title, link, duration))
    if return_str:
        return output
    return recaps

def get_direct_video_url(indirecturl):
    url = indirecturl
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
                return url
                break
    except Exception as e:
        print("error parsing/receiving XML from url " + mlburl)
        return

def find_fastcast(return_str=False):
    url = "https://search-api.mlb.com/svc/search/v2/mlb_global_sitesearch_en/sitesearch?hl=true&facet=type&expand=partner.media&q=fastcast&page=1"
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    s = json.loads(urlopen(req).read().decode("utf-8"))
    result = s['docs'][0]
    title = result['title']
    if "MLB.com FastCast" in title:
        blurb = result['blurb']
        url = result['url']
        dir = get_direct_video_url(url)
        if dir is not None:
            url = dir
        duration = result['duration'][3:]
        s = "[%s](%s) - %s\n\n" % (blurb,url,duration)
        print(s)
        if return_str:
            return s
        return (blurb,url,duration)

def find_top_plays(return_str=False):
    url = "https://search-api.mlb.com/svc/search/v2/mlb_global_sitesearch_en/sitesearch?hl=true&facet=type&expand=partner.media&q=top%2B5%2Bplays&page=1"
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    s = json.loads(urlopen(req).read().decode("utf-8"))
    result = s['docs'][0]
    blurb = result['blurb']
    now = datetime.now() - timedelta(days=1)
    date = "%d/%d/%s:" % (now.month, now.day, str(now.year)[2:])
    if "Top 5 Plays" in blurb and blurb.startswith(date):
        url = result['url']
        dir = get_direct_video_url(url)
        if dir is not None:
            url = dir
        duration = result['duration'][3:]
        s = "[%s](%s) - %s\n\n" % (blurb,url,duration)
        print(s)
        if return_str:
            return s
        return (blurb,url,duration)
    if return_str:
        return ""
    return None

def post_on_reddit(comment):
    import praw
    with open('.fitz.json', 'r') as f:
        f = json.loads(f.read())['keys']['efitz11']
    reddit = praw.Reddit(client_id=f['client_id'],
                         client_secret=f['token'],
                         user_agent='recap bot on ubuntu (/u/efitz11)',
                         username=f['user'],password=f['password'])
    user = reddit.redditor('baseballbot')
    for submission in user.submissions.new(limit=5):
        if 'Around the Horn' in submission.title:
            idx = submission.title.find('-')
            date = submission.title[idx+2:]
            now = datetime.now()
            today = "%d/%d/%s" % (now.month,now.day,str(now.year)[2:])
            # print(comment)
            if date == today:
                print("Adding comment to thread: %s - %s" % (submission.title, submission.url))
                submission.reply(comment)
            break

if __name__ == "__main__":
    output = find_fastcast(return_str=True)
    output = output + find_top_plays(return_str=True)
    output = output + get_recaps(return_str=True)
    if len(sys.argv) > 1 and sys.argv[1] == "post":
        post_on_reddit(output)

