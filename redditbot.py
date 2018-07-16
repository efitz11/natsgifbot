import praw, prawcore.exceptions
import pprint
import gifs
import json
from datetime import datetime
import mymlbstats

class RedditBot():
    def __init__(self):
        self.enabled_subs = ["computerdudetest","nationals","aaahhhtionals"]
        self.banned_subs = ["baseball"] #fuck the mods
        self.all_subs = self.enabled_subs + self.banned_subs
    
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
            sub = comment.subreddit.display_name.lower()
            if sub in self.all_subs:
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
                        else:
                            reply = reply + "[Sorry, I couldn't find a matching gif.](https://gfycat.com/CandidHeartfeltDuck)\n*****\n"
                if len(reply) > 0:
                    if sub in self.banned_subs:
                        user = comment.author.name
                        reply = "Sorry, I am banned in the subreddit you asked me in (fuck the mods), but here is your gif:\n\n" + reply
                        print("attempting to send reply:")
                        self.reddit.redditor(user).message("your gif request", reply)
                    else:
                        reply = reply + "^^computer-dude ^^bot ^^made ^^by ^^[/u\/efitz11](/user/efitz11) ^^--- "
                        reply = reply + "[^^more ^^info ^^on ^^computer-dude](https://github.com/efitz11/natsgifbot/blob/master/computer-dude.md)"
                        comment.reply(reply)
            comment.mark_read()

    def create_postlist(self, team, subreddit):
        file = 'giflists/' + team + ".csv"
        output = ""
        import string
        for submission in self.reddit.subreddit(subreddit).new(limit=1000):
            if all(c in string.printable for c in submission.title):
                output = "%s\n%s,%s" % (output, submission.title, submission.url)
        with open(file, 'w') as f:
            f.write(output)

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

    def check_time(self):
        time = datetime.now()
        hasgame = len(mymlbstats.get_single_game("wsh")) > 0
        if hasgame and time.hour == 21 and time.minute == 1:
        # if hasgame:
            with open(".dongday.txt", 'r') as f:
                dongedyet = f.readline().strip()
            date = "%d%d" % (time.month, time.day)
            if dongedyet != date:
                for submission in self.reddit.subreddit("nationals").new(limit=12):
                    if submission.title.lower().startswith("game thread"):
                        print("posted dong comment")
                        submission.reply("[%s](%s)" % ("It's that time", "https://gfycat.com/FaintElasticAmericanavocet"))
                        with open(".dongday.txt", 'w') as f:
                            f.write(date)

class TwitterBot:
    def __init__(self):
        import tweepy
        #read tokens
        with open('keys.json','r') as f:
            keys = f.read()

        keys = json.loads(keys)
        keys = keys['keys']
        for key in keys:
            if key['name'] == "twitter":
                api_key = key['api_key']
                secret = key['api_secret']
                token = key['token']
                token_secret = key['token_secret']
            if key['name'] == "reddit":
                self.r_cid = key['client_id']
                self.r_user = key['user']
                self.r_token = key['token']
                self.r_pw = key['password']

        auth = tweepy.OAuthHandler(api_key, secret)
        auth.set_access_token(token, token_secret)
        self.api = tweepy.API(auth)

    def check_last_tweet(self):
        #read last tweet
        with open('lasttweet.txt','r') as f:
            last_id = f.readline().strip()
        # user = api.get_user('nationalsump')
        # new_tweets = api.user_timeline(screen_name='nationalsump', count=1, tweet_mode="extended")
        new_tweets = self.api.user_timeline(screen_name='nationalsump', count=1)
        for tweet in new_tweets:
            if str(tweet.id) != last_id:
                print("new tweet %d" % tweet.id)
                with open('lasttweet.txt','w') as f:
                    f.write(str(tweet.id))

                # post on reddit
                reddit = praw.Reddit(client_id=self.r_cid,
                      client_secret=self.r_token,
                      user_agent='ubuntu:computer-dude (by /u/efitz11)',
                      username=self.r_user,password=self.r_pw)

                for submission in reddit.subreddit("nationals").new(limit=12):
                    if submission.title.lower().startswith("game thread"):
                        picture = tweet.entities['media'][0]['media_url_https']
                        comment = tweet.text.replace("\n","\n\n")
                        if "Soto" in tweet.text:
                            comment = comment.replace("OnePursuit","JuanPursuit")
                        index = comment.find("https://t.co")
                        comment = comment[:index]
                        index = comment.find('\n')
                        comment = "[%s](%s)%s" % (comment[:index], picture, comment[index:])
                        comment = comment + "\n\nhttps://twitter.com/NationalsUmp/status/%d" % (tweet.id)
                        submission.reply(comment)

if __name__ == "__main__":
    r = RedditBot()
    # see if new gifs have been submitted to /r/nationalsgifs
    r.update_postlist()
    # respond to gif requests
    r.check_mentions()
    #r.check_time()
    t = TwitterBot()
    t.check_last_tweet()

