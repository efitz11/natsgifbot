import praw, prawcore.exceptions

class RedditBot():
    def __init__(self):
        # get tokens from file
        f = open('reddittokens.txt','r')
        reddit_clientid = f.readline().strip()
        reddit_token = f.readline().strip()
        password = f.readline().strip()
        f.close()
        print(reddit_clientid)
        print(reddit_token)
        self.reddit = praw.Reddit(client_id=reddit_clientid,
                     client_secret=reddit_token,
                     user_agent='ubuntu:computer-dude (by /u/efitz11)',
                     username="computer-dude",password=password)
        #print(self.reddit.user.me())
                     
    def check_mentions(self):
        print("checking messages")
        for mention in self.reddit.inbox.mentions(limit=100):
            print(mention.author, mention.body)
