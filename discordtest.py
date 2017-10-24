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

basesmap = {'0':'---',
            '1':'1--',
            '2':'-2-',
            '3':'--3',
            '4':'12-',
            '5':'1-3',
            '6':'-23',
            '7':'123'}

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
    
def get_game_str(gameid, lastplay=False):
    overview = mymlbgame.retoverview(gameid)
    
    hometeam = overview['home_name_abbrev']
    awayteam = overview['away_name_abbrev']
    status   = overview['status']
    
    if status == 'Pre-Game' or status == 'Warmup' or status == 'Preview':
        firstpitch = overview['first_pitch_et']
        awins = overview['away_win']
        aloss = overview['away_loss']
        hwins = overview['home_win']
        hloss = overview['home_loss']
        hrecord = "(%s-%s)" % (hwins,hloss)
        arecord = "(%s-%s)" % (awins,aloss)
        output = "%s %s @ %s %s # %s ET - %s\n\t" % (awayteam.ljust(3), arecord, hometeam.ljust(3), hrecord, firstpitch,status)
        output = output + overview['away_probable_pitcher'] + " v " + overview['home_probable_pitcher']
        return output
        
    homeruns = overview['home_team_runs']
    awayruns = overview['away_team_runs']
    outs     = overview['outs']
    inning   = overview['inning']
    top_inn  = "Top" if overview['top_inning'] == 'Y' else "Bot"
    outs = outs + " out" + ("" if outs == "1" else "s")
    
    output = "%s %s @ %s %s" % (awayteam.ljust(3), awayruns.rjust(2), hometeam.ljust(3), homeruns.rjust(2))
    if status != 'Final':
        bases = ""
        if 'runner_on_base_status' in overview:
            bases = basesmap[overview['runner_on_base_status']]
        output = output + ":  %s %s - %s %s" % (top_inn, inning, outs, bases)
    else:
        output = output + " (F) "
        wp = overview['winning_pitcher']
        lp = overview['losing_pitcher']
        sp = overview['save_pitcher']
        output = output + "# WP: " + wp.ljust(10) + "\tLP: " + lp.ljust(10) + (("\tSV: " + sp.ljust(10)) if sp != "" else "")
    if lastplay and 'pbp_last' in overview:
        pitcher = overview['current_pitcher']
        batter = overview['current_batter']
        lplay    = overview['pbp_last']
        output = output + "\n\tPitching: **%s** \tBatting: **%s**" % (pitcher, batter)
        output = output + "\n\tLast play: *" + lplay.strip() + "*"
    return output
    
@bot.command()
async def mlb(*team :str):
    now = datetime.now() - timedelta(hours=3)
    if len(team) == 0:
        day = mlbgame.day(now.year, now.month, now.day)
        output = "Today's scores:\n```python\n"
        for game in day:
            output = output + get_game_str(game.game_id) +'\n'
        await bot.say(output.strip() + "```")
        return
    
    teamname = team[0].title()
    day = mlbgame.day(now.year, now.month, now.day, home=teamname, away=teamname)
    
    if len(day) > 0 :
        game = day[0]
        id = game.game_id
        output = get_game_str(id,lastplay=True)
        await bot.say(output)

@bot.command()
async def mlbd(year:int, month:int, day:int, *team:str):
    if len(team) == 0:
        gameday = mlbgame.day(year, month, day)
        output = "The day's scores:\n```python\n"
        for game in gameday:
            output = output + get_game_str(game.game_id) +'\n'
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
    input = ' '.join(text)
    last = False
    output = ""
    for s in input:
        num = random.randint(0,100)
        if not last and num > 20:
            output = output + (s.upper())
            last = True
        else:
            output = output + (s)
            last = False
    await bot.say(output)
        
@bot.command()
async def memeify(*text:str):
    input = ' '.join(text)
    output = ""
    for s in input:
        output = output + " " + s
    await bot.say(output.strip().upper())
    
@bot.command()
async def pup():
    await bot.say(sub('puppies'))

@bot.command()
async def kit():
    await bot.say(sub('kittens'))

@bot.command()
async def corg():
    await bot.say(sub('corgi'))    

@bot.command()
async def fp():
    await bot.say(sub('justFPthings',selfpost=True))    
    
@bot.command()
async def subr(text:str):
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
    nu = 6
    if len(num) != 0:
        nu = num[0]
    n = random.randint(1,nu)
    await bot.say(n)
    
@bot.command()
async def flip():
    res = "heads" if random.randint(0,1) == 0 else "tails"
    await bot.say(res)
    
@bot.command()
async def cfb(*team:str):
    t = ' '.join(team)
    await bot.say(cfbgame.get_game(t))
    
@bot.command()
async def nfl(*team:str):
    t = ' '.join(team)
    await bot.say(nflgame.get_game(t,'nfl'))
    
@bot.command()
async def nba(*team:str):
    t = ' '.join(team)
    await bot.say(nflgame.get_game(t,'nba'))
'''  
@bot.command()
async def nhl(*team:str):
    t = ' '.join(team)
    await bot.say(nflgame.get_game(t,'nhl'))
'''    

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

    
async def my_bg_task():
    await bot.wait_until_ready()
    channel = discord.Object(id = main_chid)
    while not bot.is_closed:
        await asyncio.sleep(100)

reddit = praw.Reddit(client_id=reddit_clientid,
                     client_secret=reddit_token,
                     user_agent='windows:natsgifbot (by /u/efitz11)')
print(reddit.read_only)
#bot.loop.create_task(my_bg_task())
bot.run(discord_token)
