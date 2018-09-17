from urllib.request import urlopen, Request
import json

def get_json(url,encoding="utf-8"):
    print(url)
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    return json.loads(urlopen(req).read().decode(encoding))

def format_table(labels, dicts, repl_map={}, showlabels=True):
    lines = ['' for i in range(len(dicts)+1)]
    for label in labels:
        l = label
        if l in repl_map:
            l = repl_map[label]
        if showlabels:
            length = len(l)
        else:
            length = 0
        for d in dicts:
            if label in d:
                r = str(d[label])
            else:
                r = ""
            length = max(length, len(r))
        if length > 0:
            lines[0] = "%s %s" % (lines[0], l.rjust(length).upper())
        for i in range(len(dicts)):
            if label in dicts[i]:
                r = str(dicts[i][label])
            else:
                r = ""
            if length > 0:
                lines[i+1] = "%s %s" % (lines[i+1], r.rjust(length))
    if showlabels:
        return '\n'.join(lines)
    else:
        return '\n'.join(lines[1:])
