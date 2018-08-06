import redditbot
import string
import re

def remove_emoji(string):
    emoji_pattern = re.compile("["
                           u"\U0001F600-\U0001F64F"  # emoticons
                           u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                           u"\U0001F680-\U0001F6FF"  # transport & map symbols
                           u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                           u"\U00002702-\U000027B0"
                           u"\U000024C2-\U0001F251"
                           "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', string)


user = 'efitz11'
filename = "%s.txt" % user
subreddits = ['baseball','nationals']

r = redditbot.RedditBot()
comments = r.reddit.redditor(user).comments.new(limit=1000)
bodies = []
table = str.maketrans("","",string.punctuation)
for c in comments:
    if str(c.subreddit) in subreddits:
        if 'fastcast' not in c.body.lower():
            bodies.append(c.body.lower().translate(table))

s = ""
for b in bodies:
    words = b.split()
    for w in words:
        if len(w) < 4:
            continue
        if 'http' in w:
            continue
        else:
            s = "%s %s " % (s, w)

with open(filename, 'w', encoding='utf-8') as f:
    f.write(s)
