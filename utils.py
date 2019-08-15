from urllib.request import urlopen, Request
import json
import os
import datetime,time


def get_json(url, encoding="utf-8"):
    print(url)
    req = Request(url, headers={'User-Agent': "ubuntu"})
    return json.loads(urlopen(req).read().decode(encoding))

def get_keys(name):
    """
    Returns the keys listed in keys.json
    :param name: name of the service you want the keys for
    :return: dictionary containing the keys
    """
    with open("keys.json",'r') as f:
        f = json.loads(f.read())
    for k in f['keys']:
        if k['name'] == name:
            return k

def split_long_message(message, delim='\n'):
    MAX_LEN = 2000
    separate = []

    while len(message) > 0:
        if len(message) < MAX_LEN:
            separate.append(message)
            break
        cut = message[:MAX_LEN]
        idx = cut.rfind(delim)
        cut = message[:idx]
        separate.append(cut)
        message = message[idx+1:]
        if idx == -1:
            break

    return separate

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def format_reddit_table(labels, dicts, repl_map={}, left_list=[], bold=False, low_stats=[]):
    """
    Generates a reddit formatted table from a list of keys and a list of dicts for the data
    :param labels: list of dictionary keys that function as column labels
    :param dicts: list of python dictionaries containing the table data
    :param repl_map: a dict containing label mappings (dict key : column name)
    :param left_list: a list containing `dicts` keys to left justify (right is default)
    :param bold: bolden highest (or lowest) values in a column
    :param low_stats: list of stats where lower is better (for bolding)
    :return: string containing formatted table
    """
    # create a bunch of empty lines to start
    lines = ['' for i in range(len(dicts) + 2)]

    # construct table column by column from left to right
    for label in labels:
        l = label
        # replace label with display label if mapped
        if l in repl_map:
            l = repl_map[label]
        lines[0] = "%s|%s" % (lines[0], l.upper())
        if label in left_list:
            lines[1] = "%s|:--" % (lines[1])
        else:
            lines[1] = "%s|--:" % (lines[1])

        # find values to bold
        boldlist = []
        if is_number(dicts[0][label]):
            if bold:
                boldnum = -1
                for i in range(len(dicts)):
                    if i == 0:
                        boldnum = float(dicts[i][label])
                        boldlist.append(i)
                    else:
                        num = float(dicts[i][label])
                        if label in low_stats:
                            if num < boldnum:
                                boldnum = num
                                boldlist = [i]
                            elif num == boldnum:
                                boldlist.append(i)
                        else:
                            if num > boldnum:
                                boldnum = num
                                boldlist = [i]
                            elif num == boldnum:
                                boldlist.append(i)

        # construct the column
        for i in range(len(dicts)):
            if label in dicts[i]:
                r = str(dicts[i][label])
                if i in boldlist:
                    r = "**%s**" % r
            else:
                r = ""  # empty cell
            lines[i + 2] = "%s|%s" % (lines[i + 2], r)

    return '\n'.join(lines)

def format_table(labels, dicts, repl_map={}, showlabels=True, linebreaknum=0, linebreak='', left_list=[], reddit=False, def_repl=True, bold=False, low_stats=[]):
    """
    Generates a formatted table if printed in monospace text
    :param labels: A list of column labels
    :param dicts: A list of python dictionaries, containing the data to be tabled. labels in the param labels should be the dict keys
    :param repl_map: A python dict, with labels as keys mapped to names for display (replace map)
    :param showlabels: Set to False to turn off the top row
    :param linebreaknum: An int corresponding to how many rows between line breaks
    :param linebreak: The string to print as a line break
    :param justmap: A list of keys from `dicts` to left justify instead of right
    :param reddit: True if you want to return a table formatted for reddit
    :param bold: passes to format_reddit_table
    :param low_stats: passes to format_reddit_table
    :return: A string containing the formatted table
    """
    if def_repl:
        repl_map = {'d':'2B', 't':'3B', **repl_map}

    if reddit:
        return format_reddit_table(labels, dicts, repl_map=repl_map, left_list=left_list, bold=bold, low_stats=low_stats)

    # create a bunch of empty lines to start
    lines = ['' for i in range(len(dicts) + 1)]

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
        # hide column if none of the dicts have an entry and column names are hidden
        # here we're adding the label to the top if one of the dicts does have an entry and top row is hidden
        if length > 0:
            if label in left_list:
                lines[0] = "%s %s" % (lines[0], l.ljust(length).upper())
            else:
                lines[0] = "%s %s" % (lines[0], l.rjust(length).upper())
        # construct the column
        for i in range(len(dicts)):
            if label in dicts[i]:
                r = str(dicts[i][label])
            else:
                r = ""  # empty cell
            if length > 0:
                if label in left_list:
                    lines[i + 1] = "%s %s" % (lines[i + 1], r.ljust(length))
                else:
                    lines[i + 1] = "%s %s" % (lines[i + 1], r.rjust(length))

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

def write_to_file(contents, filename, subdir, prependtimestamp=False):
    if prependtimestamp:
        import time
        timestr = time.strftime('%Y%m%d-%H%M%S')
        filename = "%s-%s" % (timestr, filename)
    if not os.path.exists(subdir):
        os.makedirs(subdir)
    filename = os.path.join(subdir,filename)
    with open(filename, 'w') as f:
        f.write(contents)
    return filename

def get_ET_from_timestamp(timestamp):
    utc = datetime.datetime.strptime(timestamp,"%Y-%m-%dT%H:%M:00Z") #"2018-03-31T20:05:00Z",
    nowtime = time.time()
    diff = datetime.datetime.fromtimestamp(nowtime) - datetime.datetime.utcfromtimestamp(nowtime)
    utc = utc + diff
    return datetime.datetime.strftime(utc, "%I:%M %p ET")

def prettydate(d):
    """get an instagram-style relative date
        can pass in epoch time or a datetime instance"""
    if isinstance(d, int):
        d = datetime.datetime.fromtimestamp(d)
    diff = datetime.datetime.now() - d
    s = diff.seconds
    if diff.days > 7 or diff.days < 0:
        return d.strftime('%d %b %y')
    elif diff.days == 1:
        return '1 day ago'
    elif diff.days > 1:
        return '{:.0f} days ago'.format(diff.days)
    elif s <= 1:
        return 'just now'
    elif s < 60:
        return '{:.0f} seconds ago'.format(s)
    elif s < 120:
        return '1 minute ago'
    elif s < 3600:
        return '{:.0f} minutes ago'.format(s/60)
    elif s < 7200:
        return '1 hour ago'
    else:
        return '{:.0f} hours ago'.format(s/3600)
