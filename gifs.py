import re, random

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