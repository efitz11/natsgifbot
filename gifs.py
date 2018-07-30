import re, random
from urllib.request import urlopen, Request
import urllib.parse
import json
from fuzzywuzzy import fuzz

otherteams = ['atl','sea','phi','nyy','stl','chc']

def gif(query):
    matches = []
    patterns = []

    file = 'postlist.csv'

    name = query.split(" ")
    name[0] = name[0].lower()
    if len(name) > 0 and name[0] in otherteams:
        file = 'giflists/' + name[0] + '.csv'
        name = name[1:]

    for s in name:
        patterns.append(re.compile(s,re.IGNORECASE))

    f = open(file,'r')
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
        return fuzzygif(query, file)
    num = random.randint(0,len(matches)-1)
    return matches[num].strip()

def fuzzygif(query, file):
    highest,score = "",0
    matches = []
    f = open(file,'r')
    for line in f:
        search = ','.join(line.split(',')[:-1])
        sc = fuzz.partial_token_sort_ratio(query,search)
        if sc < 70:
            continue
        if sc > score:
            highest,score = line,sc
            print(highest,score)
            matches = [line]
        elif sc == score:
            matches.append(line)
    f.close()
    if len(matches) == 0:
        return "no matches"
    # for match in matches:
        # print(match)
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