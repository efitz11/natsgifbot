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
        password = f.readline().strip()
        f.close()
        self.reddit = praw.Reddit(client_id=reddit_clientid,
                     client_secret=reddit_token,
                     user_agent='ubuntu:computer-dude (by /u/efitz11)',
                     username="computer-dude",password=password)
                     
    def check_mentions(self):
        mention_str = "/u/computer-dude"
        for comment in self.reddit.inbox.unread(limit=100):
            if comment.subreddit.display_name.lower() in self.enabled_subs:
                text = comment.body.lower()
                if mention_str in text:
                    text = text.replace(mention_str,'').strip()
                    if text.startswith("gif"):
                        text = text.replace("gif",'').strip()
                    reply = gifs.gif(text)
                    lastcomma = reply.rfind(',')
                    reply = reply[:lastcomma] + "\n\n" + reply[lastcomma+1]
                    comment.reply(reply)
            comment.mark_read()
            

if __name__ == "__main__":
    r = RedditBot()
    r.check_mentions()
