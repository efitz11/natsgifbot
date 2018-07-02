import re, random
from urllib.request import urlopen, Request
import urllib.parse
import json
from fuzzywuzzy import fuzz

def gif(query):
    matches = []
    patterns = []
    
    name = query.split(" ")
    for s in name:
        patterns.append(re.compile(s,re.IGNORECASE))
        
    f = open('postlist.csv','r')
    for line in f:
        search = ','.join(line.split(',')[:-1])
        matched = True
        for pat in patterns:
            if not re.search(pat,search):
                matched = False
                break
        if matched:
            matches.append(line)
    f.close()
    
    if len(matches) == 0:
        return "no matches"
    num = random.randint(0,len(matches)-1)
    return matches[num].strip()

def fuzzygif(query):
    highest,score = "",0
    matches = []
    f = open('postlist.csv','r')
    for line in f:
        search = ','.join(line.split(',')[:-1])
        sc = fuzz.token_set_ratio(query,search)
        if sc > score:
            highest,score = line,sc
            matches = [line]
        elif sc == score:
            matches.append(line)
    f.close()
    if len(matches) == 0:
        return "no matches"
    num = random.randint(0,len(matches)-1)
    return matches[num].strip()

def get_mlb_gif(query):
    url = "https://search-api.mlb.com/svc/search/v2/mlb_global_embed/query?expand=partner.media.photo&type=gif&q="+\
            urllib.parse.quote_plus("nationals " +query)+"&page=1&sort=new"
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    data = json.loads(urlopen(req).read().decode("utf-8"))
    if len(data['docs']) == 0:
        return "no matches"
    return data['docs'][0]['url']