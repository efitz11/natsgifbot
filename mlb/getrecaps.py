from urllib.request import urlopen, Request
import json
from datetime import datetime, timedelta
from xml.etree import ElementTree
import sys, time

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
                for pb in item['playbacks']:
                    if "2500K" in pb['url']:
                        link = pb['url']
                        break
                # link = item['playbacks'][3]['url']
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
    cid = url[url.rfind('c-')+2:]
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
    print(url)
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    s = json.loads(urlopen(req).read().decode("utf-8"))
    result = s['docs'][0]
    title = result['title']
    now = datetime.now()
    date = "%d-%02d-%02d" % (now.year, now.month, now.day)
    print(date)
    if "MLB.com FastCast".lower() in title.lower() and date in result['display_timestamp']:
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
    if return_str:
        return ""

def find_top_plays(return_str=False):
    url = "https://search-api.mlb.com/svc/search/v2/mlb_global_sitesearch_en/sitesearch?hl=true&facet=type&expand=partner.media&q=top%2Bplays&page=1"
    print(url)
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    s = json.loads(urlopen(req).read().decode("utf-8"))
    results = s['docs']
    now = datetime.now()# - timedelta(days=1)
    yesterday = now - timedelta(days=1)
    yest = "%d/%d/%s:" % (yesterday.month, yesterday.day, str(yesterday.year)[2:])
    date = "%d-%02d-%02d" % (now.year, now.month, now.day)
    vids = []
    output = ""
    for res in results:
        if date in res['display_timestamp'] or yest in res['blurb']:
            blurb = res['blurb']
            if "top" in blurb.lower() and ("plays" in blurb.lower() or "home runs" in blurb.lower()):
                url = res['url']
                dir = get_direct_video_url(url)
                if dir is not None:
                    url = dir
                duration = res['duration'][3:]
                s = "[%s](%s) - %s\n\n" % (blurb,url,duration)
                print(s)
                if return_str:
                    output = output + s
                vids.append((blurb,url,duration))
    if return_str:
        return output
    return vids

def find_quick_pitch(return_str=False):
    url = "https://search-api.mlb.com/svc/search/v2/mlb_global_sitesearch_en/sitesearch?hl=true&facet=type&expand=partner.media&q=quick%2Bpitch&page=1"
    print(url)
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    s = json.loads(urlopen(req).read().decode("utf-8"))
    result = s['docs'][0]
    blurb = result['blurb']
    now = datetime.now() - timedelta(days=1)
    date = "%d/%d/%s" % (now.month, now.day, str(now.year)[2:])
    if "quick pitch recap" in blurb.lower() and date in blurb:
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

def find_youtube_homeruns(return_str=False):
    url = "https://www.googleapis.com/youtube/v3/search?part=snippet&q=mlb+all+home+runs&order=date&channelId=UCoLrcjPV5PbUrUyXq5mjc_A"
    with open("../keys.json",'r') as f:
        f = json.loads(f.read())
    key = None
    for k in f['keys']:
        if k['name'] == "youtube":
            key = k['key']
    if key is not None:
        d = datetime.now() - timedelta(days=1)
        url = url + "&key=" + key
        print(url)
        req = Request(url, headers={'User-Agent' : "ubuntu"})
        s = json.loads(urlopen(req).read().decode("utf-8"))
        import calendar
        month = calendar.month_name[d.month]
        for res in s['items']:
            datestr = "%s %d, %d" % (month, d.day, d.year)
            otherdatestr = "%d/%d/%s" % (d.month, d.day, str(d.year)[2:])
            if datestr in res['snippet']['title'] or otherdatestr in res['snippet']['title']:
                id = res['id']['videoId']
                title = res['snippet']['title']
                url = "https://www.googleapis.com/youtube/v3/videos?id=" + id + "&part=contentDetails&key=" + key
                print(url)
                req = Request(url, headers={'User-Agent' : "ubuntu"})
                s = json.loads(urlopen(req).read().decode("utf-8"))
                duration = s['items'][0]['contentDetails']['duration']
                duration = duration[2:]
                duration = duration.replace('M',':')
                duration = duration.replace('S','')
                url = "https://www.youtube.com/watch?v=" + id
                s = "[%s](%s) - %s\n\n" % (title,url,duration)
                print(s)
                if return_str:
                    return s
                return (title,url,duration)
        if return_str:
            return ""

def find_must_cs(return_str=False):
    url = "https://search-api.mlb.com/svc/search/v2/mlb_global_sitesearch_en/sitesearch?hl=true&facet=type&expand=partner.media&q=must%2Bc&page=1"
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    s = json.loads(urlopen(req).read().decode("utf-8"))
    results = s['docs']
    yesterday = datetime.now() - timedelta(days=1)
    vids = []
    output = ""
    for res in results:
        if res['blurb'].startswith("Must C"):
            for tag in res['tags']:
                if tag['type'] == 'event_date':
                    date = tag['value']
            if date[:10] == "%d-%02d-%02d" % (yesterday.year, yesterday.month, yesterday.day):
                blurb = res['blurb']
                url = get_direct_video_url(res['url'])
                duration = res['duration'][3:]
                s = "[%s](%s) - %s\n\n" % (blurb,url,duration)
                print(s)
                if return_str:
                    output = output + s
                vids.append((blurb,url,duration))
    if return_str:
        return output
    return vids

def find_statcasts(return_str=False):
    url = "https://search-api.mlb.com/svc/search/v2/mlb_global_sitesearch_en/sitesearch?hl=true&facet=type&expand=partner.media&q=statcast&page=1"
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    s = json.loads(urlopen(req).read().decode("utf-8"))
    results = s['docs']
    yesterday = datetime.now() - timedelta(days=1)
    vids = []
    output = ""
    for res in results:
        date = ""
        for tag in res['tags']:
            if tag['type'] == 'event_date':
                date = tag['value']
        if date[:10] == "%d-%02d-%02d" % (yesterday.year, yesterday.month, yesterday.day):
            blurb = res['blurb']
            url = get_direct_video_url(res['url'])
            duration = res['duration'][3:]
            s = "[%s](%s) - %s\n\n" % (blurb,url,duration)
            print(s)
            if return_str:
                output = output + s
            vids.append((blurb,url,duration))
    if return_str:
        return output
    return vids

def post_on_reddit(cron=False):
    import praw
    with open('.fitz.json', 'r') as f:
        f = json.loads(f.read())['keys']['efitz11']
    reddit = praw.Reddit(client_id=f['client_id'],
                         client_secret=f['token'],
                         user_agent='recap bot on ubuntu (/u/efitz11)',
                         username=f['user'],password=f['password'])
    user = reddit.redditor('baseballbot')
    posted = False
    while not posted:
        for submission in user.submissions.new(limit=5):
            if 'Around the Horn' in submission.title:
                #idx = submission.title.find('-')
                #date = submission.title[idx+2:]
                now = datetime.now()
                today = "%d/%d/%s" % (now.month,now.day,str(now.year)[2:])
                todayalt = "%d/%d/%s" % (now.month,now.day,str(now.year))
                # print(comment)
                #if date == today:
                if today in submission.title or todayalt in submission.title:
                    print("Adding comment to thread: %s - %s" % (submission.title, submission.url))
                    comment = get_all_outputs()
                    submission.reply(comment)
                    posted = True
                break
        if not cron:
            posted = True
        elif not posted:
            print("didn't find ATH, checking in 5 minutes...")
            time.sleep(5*60)

def get_all_outputs():
    output = find_fastcast(return_str=True)
    output = output + find_quick_pitch(return_str=True)
    output = output + find_youtube_homeruns(return_str=True)
    output = output + find_top_plays(return_str=True)
    output = output + "****\n"
    output = output + find_must_cs(return_str=True)
    output = output + "****\n"
    output = output + find_statcasts(return_str=True)
    output = output + "****\n"
    output = output + get_recaps(return_str=True)
    return output

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "post":
        if len(sys.argv) > 2 and sys.argv[2] == "cron":
            post_on_reddit(cron=True)
        else:
            post_on_reddit()
    else:
        print(get_all_outputs())
