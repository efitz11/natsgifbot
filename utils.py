from urllib.request import urlopen, Request
import json

def get_json(url,encoding="utf-8"):
    print(url)
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    return json.loads(urlopen(req).read().decode(encoding))

def format_table(labels, dicts, repl_map={}, showlabels=True, linebreaknum=0, linebreak=''):
    '''linebreak args will break every linebreaknum lines with the specified string'''
    #create a bunch of empty lines to start
    lines = ['' for i in range(len(dicts)+1)]

    # construct table column by column from left to right
    for label in labels:
        l = label
        # replace label with display label if mapped
        if l in repl_map:
            l = repl_map[label]
        # find initial column width set by display label
        if showlabels:
            length = len(l)
        else:
            length = 0
        # find actual length of column set by widest value in all dicts for the label
        for d in dicts:
            if label in d:
                r = str(d[label])
            else:
                r = ""
            length = max(length, len(r))
        # hide column if none of the dicts have an entry
        # here we're adding the label to the top if one of the dicts does have an entry
        if length > 0:
            lines[0] = "%s %s" % (lines[0], l.rjust(length).upper())
        # construct the column
        for i in range(len(dicts)):
            if label in dicts[i]:
                r = str(dicts[i][label])
            else:
                r = ""  # empty cell
            if length > 0:
                lines[i+1] = "%s %s" % (lines[i+1], r.rjust(length))

    # remove the top line if we want to hide column names
    if not showlabels:
        lines = lines[1:]

    # add the line breaks if necessary
    if linebreaknum > 0:
        newlines = []
        while len(lines) > 0:
            for i in range(linebreaknum):
                if len(lines) > 0:
                    newlines.append(lines.pop(0))
            newlines.append(linebreak)
        lines = newlines[:-1]

    return '\n'.join(lines)
