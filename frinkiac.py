from urllib.request import urlopen, Request
import urllib.parse
import json

def get_response(url):
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    #req.headers["User-Agent"] = "windows 10 bot"
    return urlopen(req).read().decode("utf-8")
    
def get_ep_ts(query):
    url = "https://frinkiac.com/api/search?q="+urllib.parse.quote_plus(query)
    response = json.loads(get_response(url))
    ep = response[0]["Episode"]
    ts = response[0]["Timestamp"]
    return (ep,ts)
    
def get_lines(ep,ts):
    url = "https://frinkiac.com/api/caption?e=%s&t=%s" % (ep,ts)
    print(url)
    response = json.loads(get_response(url))
    return response["Subtitles"]
    
def get_context_frames(ep,ts):
    url = "https://frinkiac.com/api/frames/%s/%s/4000/4000" % (ep,ts)
    response = json.loads(get_response(url))
    return response
    
def get_meme(query):
    ep,ts = get_ep_ts(query)
    subs = get_lines(ep,ts)
    
    for s in subtitles:
        line = s["Content"]
        words = line.split(' ')
        print(words)
        l = ""
        while (len(words)>0):
            if len(l) + len(words[0]) < 25:
                l = l + " " + words.pop(0)
            else:
                subs = subs + l + "\n"
                l = words.pop(0)
        subs = subs + l + "\n"
    subs = subs.strip()
    url = "https://frinkiac.com/meme/%s/%s.jpg?lines=%s" % (ep,ts,urllib.parse.quote_plus(subs))
    return(url)

def get_gif(query):
    ep,ts = get_ep_ts(query)
    subs = get_lines(ep,ts)
    context = get_context_frames(ep,ts)
    url = "https://frinkiac.com/gif/%s/%s/%s.gif?lines=%s" %(ep,context[0]['Timestamp'],context[-1]['Timestamp'],urllib.parse.quote_plus(subs))
    return url
