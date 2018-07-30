import discord
from discord.ext import commands
import praw, prawcore.exceptions

from urllib.request import urlopen, Request
import urllib.parse
from datetime import datetime, timedelta, time
import random
import re

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


    def sub(self, subreddit, selfpost=False,limit=25):
        if subreddit in self.disabled_subs:
            return self.disabled_str
        list = []
        try:
            for submission in self.reddit.subreddit(subreddit).hot(limit=limit):
        #        if submission.is_self == selfpost and not submission.stickied and not submission.over_18:
                if submission.is_self == selfpost and not submission.stickied:
                    if submission.is_self:
                        list.append(submission.title)
                    else:
                        url = submission.url
                        s = ""
                        if submission.over_18:
                            s = "**post is NSFW; embed hidden**\n"
                            url = "<" + url + ">"
                        s = s + submission.title + "\n" + url + "  \t<" + submission.shortlink+">"
                        list.append(s)
            num = random.randint(0,len(list)-1)
            return (list[num])
        except prawcore.exceptions.Redirect:
            return ("Error: subreddit not found")
        
    @commands.command()
    async def r(self,*text:str):
        """<subreddit> get a random link post from a subreddit"""
        text = ''.join(text)
        await self.bot.say(self.sub(text))
        
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
                    output = self.getsubmissiontext(submission)
                    await self.bot.say(output)
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
                    output = self.getsubmissiontext(submission)
                    await self.bot.say(output)
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
                    output = self.getsubmissiontext(submission)
                    await self.bot.say(output)
                    return

    @commands.command()
    async def fp(self):
        """get a random FP quote"""
        await self.bot.say(self.sub('justFPthings',selfpost=True, limit=250))    
        
            
    @commands.command()
    async def pup(self):
        """show a random pic of a pupper"""
        await self.bot.say(self.sub('puppies'))

    @commands.command()
    async def kit(self):
        """show a random pic of a kitten"""
        await self.bot.say(self.sub('kittens'))

    @commands.command()
    async def corg(self):
        """show a random pic of a corgi"""
        await self.bot.say(self.sub('corgi'))    

    @commands.command()
    async def car(self):
        """show a random pic of a car"""
        l = ["cars","carporn","autos","shitty_car_mods"]
        i =  random.randint(0,len(l)-1)
        await self.bot.say(self.sub(l[i]))
        
def setup(bot):
    bot.add_cog(Reddit(bot))
