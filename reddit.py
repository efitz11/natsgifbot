import discord
from discord.ext import commands
import praw, prawcore.exceptions

from urllib.request import urlopen, Request
import urllib.parse
from datetime import datetime, timedelta
import random
import re
import utils

class Reddit():
    disabled_subs = ['coconutwater','trypophobia']
    disabled_str = "Sorry, retrieving posts from that sub is not allowed"

    def __init__(self,bot):
        self.bot = bot
        # get tokens from file
        f = open('tokens.txt','r')
        reddit_clientid = f.readline().strip()
        reddit_token = f.readline().strip()
        discord_token = f.readline().strip()
        f.close()
        self.reddit = praw.Reddit(client_id=reddit_clientid,
                     client_secret=reddit_token,
                     user_agent='windows:natsgifbot (by /u/efitz11)')


    def get_comment(self, url):
        # comment = self.reddit.comment(url=url)
        comment = self.reddit.submission(url=url).comments[0]
        return comment.body

    def sub(self, subreddit, selfpost=False,limit=25):
        if subreddit in self.disabled_subs:
            return [self.disabled_str]
        list = []
        try:
            for submission in self.reddit.subreddit(subreddit).hot(limit=limit):
                if submission.is_self == selfpost and not submission.stickied:
                    list.append(submission)
            num = random.randint(0,len(list)-1)
            return self.get_submission_string(list[num])
        except prawcore.exceptions.Redirect:
            return ["Error: subreddit not found"]
        
    @commands.command()
    async def r(self,*text:str):
        """<subreddit> get a random link post from a subreddit"""
        text = ''.join(text)
        for string in self.sub(text):
            await self.bot.say(string)
        # await self.bot.say(self.sub(text))
        
    def getsubmissiontext(self, submission):
        url = submission.url
        s = ""
        if submission.over_18:
            s = "**post is NSFW; embed hidden**\n"
            url = "<" + url + ">"
        score = self.getsubmissionscore(submission)
        if submission.is_self:
            output = submission.title + "\n" + submission.shortlink
        else:
            output = s+"["+ score + "]\t " + submission.title + "\n" + url + "  \t<" + submission.shortlink+">"
        return output
        
    def getsubmissionscore(self, submission):
        score = submission.score
        if score > 999:
            score = str(int(score/100)/10.0) + "k"
        else:
            score = str(score)
        return score

    def get_submission_string(self, submission, hide=False):
        ret = []
        if submission.link_flair_text is not None:
            flair = "*[%s]*" % submission.link_flair_text
        else:
            flair = ""
        userflair = ""
        if submission.author_flair_type == 'text' and submission.author_flair_text is not None:
            userflair = " [*%s*] " % submission.author_flair_text
        if submission.author_flair_type == 'richtext':
            for i in submission.author_flair_richtext:
                if 'e' in i and i['e'] == 'text':
                    userflair = " [*%s*] " % i['t'].strip()
        # import time
        # now = time.time()
        # diff = datetime.fromtimestamp(now) - datetime.utcfromtimestamp(now)
        # time = utils.prettydate(int(submission.created_utc) + int(diff.total_seconds()))
        time = utils.prettydate(int(submission.created_utc))
        if submission.is_self:
            ret.append("[%s] **%s** %s - posted by /u/%s%s to /r/%s, %s" % (self.getsubmissionscore(submission), submission.title, flair, submission.author, userflair, submission.subreddit, time))
            ret.append("%s" % submission.selftext)
            ret.append("<%s>" % submission.shortlink[:1995])
        else:
            ret.append("[%s] **%s** - posted by /u/%s%s to /r/%s, %s" % (self.getsubmissionscore(submission), submission.title, submission.author, userflair, submission.subreddit, time))
            ret.append("")
            if submission.over_18:
                ret.append("**post is NSFW; embed hidden**\n<%s>\t\t<%s>" % (submission.url, submission.shortlink))
            else:
                if hide:
                    ret.append("**post embed hidden by request**\n<%s>\t\t<%s>" % (submission.url, submission.shortlink))
                else:
                    ret.append("%s\t\t<%s>"% (submission.url, submission.shortlink))
        return ret

    @commands.command()
    async def rh(self, text:str, num:int=-1):
        """<subreddit> <num> get the #num post from subreddit/hot"""
        #subreddit = ''.join(text).lower()
        subreddit = text
        if subreddit in self.disabled_subs:
            await self.bot.say(self.disabled_str)
            return
        count = 0
        if num > 0:
            for submission in self.reddit.subreddit(subreddit).hot(limit=(num+2)):
                if submission.stickied:
                    continue
                count += 1
                if count == num:
                    for string in self.get_submission_string(submission):
                        if len(string) > 0:
                            await self.bot.say(string)
        else:
            output = "10 hottest posts from r/%s\n" % text
            for submission in self.reddit.subreddit(subreddit).hot(limit=10):
                score = self.getsubmissionscore(submission)
                output = output + "["+ score + "]\t " + submission.title + "\n\t\t<" + submission.shortlink + ">\n"
            await self.bot.say(output)

    @commands.command()
    async def rn(self, text:str, num:int=-1):
        """<subreddit> <num> get the #num post from subreddit/new"""
        subreddit = text
        if subreddit in self.disabled_subs:
            await self.bot.say(self.disabled_str)
            return
        count = 0
        if num > 0:
            for submission in self.reddit.subreddit(subreddit).new(limit=(num+2)):
                count += 1
                if count == num:
                    for string in self.get_submission_string(submission):
                        if len(string) > 0:
                            await self.bot.say(string)
        else:
            output = "10 newest posts from r/%s\n" % text
            for submission in self.reddit.subreddit(subreddit).new(limit=10):
                score = self.getsubmissionscore(submission)
                output = output + "["+ score + "]\t " + submission.title + "\n\t\t<" + submission.shortlink + ">\n"
            await self.bot.say(output)
                
    @commands.command()
    async def rs(self, subreddit:str, *query:str):
        """<subreddit> get the first post (by hot) matching the query"""
        patterns = []
        hidden = False
        if "hide" in query:
            query = ["" if x.lower() == "hide" else x for x in query]
            hidden = True
        for s in query:
            patterns.append(re.compile(s,re.IGNORECASE))
        if subreddit.endswith("/new"):
            subreddit = subreddit[:subreddit.find("/")]
            if subreddit in self.disabled_subs:
                await self.bot.say(self.disabled_str)
                return
            list = self.reddit.subreddit(subreddit).new(limit=100)
        else:
            i = subreddit.find("/")
            if i != -1:
                subreddit = subreddit[:i]
            if subreddit in self.disabled_subs:
                await self.bot.say(self.disabled_str)
                return
            list = self.reddit.subreddit(subreddit).hot(limit=100)
        for submission in list:
            matched = True
            for pat in patterns:
                if not re.search(pat,submission.title):
                    matched = False
                    break
                if matched:
                    # output = self.getsubmissiontext(submission)
                    # await self.bot.say(output)
                    count = 0
                    for string in self.get_submission_string(submission, hide=hidden):
                        if len(string) == 0:
                            count += 1
                            continue
                        elif len(string) < 2000:
                            if count == 1:
                                string = "```%s```" % string
                            await self.bot.say(string)
                        else:
                            strs = utils.split_long_message(string)
                            for s in strs:
                                await self.bot.say("```%s```" % s)
                        count = count + 1
                    return

    @commands.command()
    async def fp(self):
        """get a random FP quote"""
        for string in self.sub('justFPthings',selfpost=True, limit=250):
            await self.bot.say(string)
        
def setup(bot):
    bot.add_cog(Reddit(bot))
