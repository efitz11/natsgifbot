import praw, prawcore.exceptions
import pprint
import gifs

class RedditBot():
    def __init__(self):
        self.enabled_subs = ["computerdudetest"]
    
        # get tokens from file
        f = open('reddittokens.txt','r')
        reddit_clientid = f.readline().strip()
        reddit_token = f.readline().strip()
        self.username = f.readline().strip()
        password = f.readline().strip()
        f.close()
        self.reddit = praw.Reddit(client_id=reddit_clientid,
                     client_secret=reddit_token,
                     user_agent='ubuntu:computer-dude (by /u/efitz11)',
                     username=self.username,password=password)
                     
    def check_mentions(self):
        mention_str = "/u/"+self.username.lower()
        for comment in self.reddit.inbox.unread(limit=100):
            if comment.subreddit.display_name.lower() in self.enabled_subs:
                textbody = comment.body.lower()
                lines = textbody.split('\n')
                reply = ""
                for text in lines:
                    if mention_str in text:
                        text = text.replace(mention_str,'').strip()
                        if text.startswith("gif"):
                            text = text.replace("gif",'').strip()
                        rep = gifs.gif(text)
                        if "no matches" != rep:
                            split = rep.split(',') 
                            link = split[-1]
                            text = ','.join(split[:-1])
                            reply = reply + "[%s](%s)" % (text,link)
                            reply = reply + "\n*****\n"
                if len(reply) == 0:
                    reply = "[Sorry, I couldn't find a matching gif.](https://gfycat.com/CandidHeartfeltDuck)\n*****\n"
                if len(reply) > 0:
                    reply = reply + "^^computer-dude ^^bot ^^made ^^by ^^[/u\/efitz11](/user/efitz11) ^^--- "
                    reply = reply + "[^^more ^^info ^^on ^^computer-dude](https://github.com/efitz11/natsgifbot/blob/master/computer-dude.md)"
                    comment.reply(reply)
            comment.mark_read()
    def update_postlist(self):
        with open("lastgif.txt", "r") as f:
            lastgif = f.readline().strip()
        first = True
        for submission in self.reddit.subreddit("nationalsgifs").new(limit=10):
            if submission.url == lastgif:
                break
            else:
                with open("postlist.csv", "a") as f:
                    f.write("%s,%s\n" % (submission.title,submission.url))
                    print("added new gif %s,%s" % (submission.title,submission.url))
                #only write the first new gif as it'll be first in the list next time
                if first:
                    with open("lastgif.txt","w") as f:
                        f.write(submission.url)
            first = False

if __name__ == "__main__":
    r = RedditBot()
    # see if new gifs have been submitted to /r/nationalsgifs
    r.update_postlist()
    # respond to gif requests
    r.check_mentions()
