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
                first = True
                for text in lines:
                    if mention_str in text:
                        text = text.replace(mention_str,'').strip()
                        if text.startswith("gif"):
                            text = text.replace("gif",'').strip()
                        rep = gifs.gif(text)
                        if "no matches" != rep:
                            lastcomma = rep.rfind(',')
                            if first:
                                first = False
                            else:
                                reply = reply + "\n*****\n"
                            reply = reply + rep[:lastcomma] + "  \n" + rep[lastcomma+1:]
                if len(reply) > 0:
                    comment.reply(reply)
            comment.mark_read()
            

if __name__ == "__main__":
    r = RedditBot()
    r.check_mentions()
