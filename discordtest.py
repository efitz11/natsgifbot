import discord
from discord.ext import commands
import random
import mlbgame
from datetime import datetime, timedelta
import praw, prawcore.exceptions
import re
import asyncio

import mymlbgame, cfbgame, nflgame

bot = commands.Bot(command_prefix='!')

pattern69 = re.compile('(^|[\s\.])[6][9]([\s\.]|$)')
    
# get tokens from file
f = open('tokens.txt','r')
reddit_clientid = f.readline().strip()
reddit_token = f.readline().strip()
discord_token = f.readline().strip()
f.close()

f = open('channelids.txt')
main_chid = f.readline().strip()
f.close()


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    
@bot.command()
async def gif(*name : str):
    """returns a nationals gif matching the search query"""
    if name[0] == "electricchair":
        await bot.say('https://gfycat.com/ClearHauntingHoverfly')
    elif name[0] == "murder":
        await bot.say('https://gfycat.com/FondVibrantHousefly')
    else:
        matches = []
        patterns = []
        query = ""
        for s in name:
            patterns.append(re.compile(s,re.IGNORECASE))
            query = query + " " + s
        f = open('postlist.csv','r')
        for line in f:
            matched = True
            for pat in patterns:
                if not re.search(pat,line):
                    matched = False
                    break
            if matched:
                matches.append(line)
        f.close()
        print ("query: " + query.strip())
        print (matches)
        if len(matches) == 0:
            return
        num = random.randint(0,len(matches)-1)
        await bot.say(matches[num].strip())
            
    return

    
@bot.command()
async def mlb(*team :str):
    """<team> to show today's game, or blank to show all games"""
    now = datetime.now() - timedelta(hours=3)
    if len(team) == 0:
        day = mlbgame.day(now.year, now.month, now.day)
        output = "Today's scores:\n```python\n"
        for game in day:
            output = output + mymlbgame.get_game_str(game.game_id) +'\n'
        await bot.say(output.strip() + "```")
        return
    
    teamname = team[0].title()
    day = mlbgame.day(now.year, now.month, now.day, home=teamname, away=teamname)
    
    if len(day) > 0 :
        game = day[0]
        id = game.game_id
        output = mymlbgame.get_game_str(id,lastplay=True)
        await bot.say("```python\n" + output + "```")

@bot.command()
async def mlbd(year:int, month:int, day:int, *team:str):
    """<yyyy mm dd> to show all of that day's games; add a team for just one"""
    if len(team) == 0:
        gameday = mlbgame.day(year, month, day)
        output = "The day's scores:\n```python\n"
        for game in gameday:
            output = output + mymlbgame.get_game_str(game.game_id) +'\n'
        await bot.say(output.strip() + "```")
        return
    else:
        team = team[0].title()
        gameday = mlbgame.day(year, month, day, home=team, away=team)

    if len(gameday) > 0 :
        game = gameday[0]
        id = game.game_id
        box = mlbgame.game.GameBoxScore(mlbgame.game.box_score(id))
        s = game.nice_score() #+ "\n```" + box.print_scoreboard() + "```"
        await bot.say(s)

def sub(subreddit, selfpost=False):
    list = []
    try:
        for submission in reddit.subreddit(subreddit).hot(limit=25):
    #        if submission.is_self == selfpost and not submission.stickied and not submission.over_18:
            if submission.is_self == selfpost and not submission.stickied:
                if submission.is_self:
                    list.append(submission.title)
                else:
                    list.append(submission.title + "\n" + submission.url + "  \t<" + submission.shortlink+">")
        num = random.randint(0,len(list)-1)
        return (list[num])
    except prawcore.exceptions.Redirect:
        return ("Error: subreddit not found")

@bot.command()
async def mockify(*text:str):
    """MocKiFy aNy sTrIng of tExT"""
    input = ' '.join(text).lower()
    last = False
    output = ""
    prob = 20
    for s in input:
        num = random.randint(0,100)
        if not last and num > prob:
            output = output + (s.upper())
            prob = 20
            last = True
        else:
            output = output + (s)
            prob = prob - 4
            last = False
    await bot.say(output)
        
@bot.command()
async def memeify(*text:str):
    """M E M E I F Y   A N Y   S T R I N G   O F   T E X T"""
    input = ' '.join(text)
    output = ""
    for s in input:
        output = output + " " + s
    await bot.say(output.strip().upper())
    
@bot.command()
async def pup():
    """show a random pic of a pupper"""
    await bot.say(sub('puppies'))

@bot.command()
async def kit():
    """show a random pic of a kitten"""
    await bot.say(sub('kittens'))

@bot.command()
async def corg():
    """show a random pic of a corgi"""
    await bot.say(sub('corgi'))    

@bot.command()
async def fp():
    """get a random FP quote"""
    await bot.say(sub('justFPthings',selfpost=True))    
    
@bot.command()
async def r(text:str):
    """<subreddit> get a random link post from a subreddit"""
    await bot.say(sub(text))
    
@bot.command()
async def fuck():
    l = ['barves','cubs','dh','dodgers','mets','yankees']
    num = random.randint(0,len(l)-1)
    await bot.say(('the '+ l[num]).upper())
    
@bot.command()
async def pajokie():
    await bot.say("https://cdn.discordapp.com/attachments/328677264566910977/343555639227842571/image.jpg")

@bot.command()
async def roll(*num:int):
    """roll an n-sided die (6 default)"""
    nu = 6
    if len(num) != 0:
        nu = num[0]
    n = random.randint(1,nu)
    await bot.say(n)
    
@bot.command()
async def flip():
    """flip a coin"""
    res = "heads" if random.randint(0,1) == 0 else "tails"
    await bot.say(res)
    
@bot.command()
async def cfb(*team:str):
    """<team> display score of team's cfb game"""
    t = ' '.join(team)
    await bot.say(cfbgame.get_game(t))
    
@bot.command()
async def nfl(*team:str):
    """<optional team> display score(s) of nfl game"""
    t = ' '.join(team)
    await bot.say(nflgame.get_game(t,'nfl'))
    
@bot.command()
async def nba(*team:str):
    """<optional team> display score(s) of nba game"""
    t = ' '.join(team)
    await bot.say(nflgame.get_game(t,'nba'))
'''  
@bot.command()
async def nhl(*team:str):
    t = ' '.join(team)
    await bot.say(nflgame.get_game(t,'nhl'))
'''    

@bot.command()
async def giflist():
    await bot.say("https://github.com/efitz11/natsgifbot/blob/master/postlist.csv")

@bot.event
async def on_message(message):
    #stuff
    if message.author == bot.user:
        return
    if message.content.startswith(bot.command_prefix):
        await bot.process_commands(message)
    else:
        if pattern69.search(message.content):
            await bot.send_message(message.channel, 'Nice.')

updater = mymlbgame.Updater()

async def my_bg_task():
    await bot.wait_until_ready()
    channel = discord.Object(id = main_chid)
    while not bot.is_closed:
        #print("update")
        teamname = "Astros"
        now = datetime.now() - timedelta(hours=3)
        day = mlbgame.day(now.year, now.month, now.day, home=teamname, away=teamname)
        
        if len(day) > 0 :
            game = day[0]
            id = game.game_id
            output = updater.update(id)
            if output != "" and output != None:
                output = "```python\n" + output + "```"
                await bot.send_message(channel,output)
        await asyncio.sleep(15)

reddit = praw.Reddit(client_id=reddit_clientid,
                     client_secret=reddit_token,
                     user_agent='windows:natsgifbot (by /u/efitz11)')
print(reddit.read_only)
bot.loop.create_task(my_bg_task())
bot.run(discord_token)
