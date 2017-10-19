import discord
from discord.ext import commands
import random
import mlbgame
from datetime import datetime, timedelta
import praw
import re

description = '''An example bot to showcase the discord.ext.commands extension
module.
There are a number of utility commands being showcased here.'''
bot = commands.Bot(command_prefix='!', description=description)

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
		await bot.say(matches[num].split(',')[-1].strip())
			
	return
	
def get_game_str(gameid):
	overview = mlbgame.game.overview(gameid)
	print(overview)
	
	hometeam = overview['home_name_abbrev']
	homeruns = overview['home_team_runs']
	awayteam = overview['away_name_abbrev']
	awayruns = overview['away_team_runs']
	outs     = overview['outs']
	inning   = overview['inning']
	top_inn  = "Top" if overview['top_inning'] == 'N' else "Bot"
	outs = outs + " out" + ("" if outs == "1" else "s")
	status   = overview['status']
	
	output = "%s %s @ %s %s" % (awayteam, awayruns, hometeam, homeruns)
	if status != 'Final':
		output = output + ":  %s %s - %s" % (top_inn, inning, outs)
	else:
		output = output + " (F)"
	if 'pbp_last' in overview:
		lplay    = overview['pbp_last']
		output = output + "\n\tLast play: " + lplay
	return output
	
@bot.command()
async def mlb(*team :str):
	now = datetime.now() - timedelta(hours=3)
	if len(team) == 0:
		day = mlbgame.day(now.year, now.month, now.day)
		output = "Today's scores:\n"
		for game in day:
			output = output + get_game_str(game.game_id) +'\n'
		await bot.say(output.strip())
		return
	print ("eh?")
	
	teamname = team[0].title()
	day = mlbgame.day(now.year, now.month, now.day, home=teamname, away=teamname)
	
	if len(day) > 0 :
		game = day[0]
		id = game.game_id
		output = get_game_str(id)
		await bot.say(output)

@bot.command()
async def mlbd(team :str, year:int, month:int, day:int):
	team = team.title()
	gameday = mlbgame.day(year, month, day, home=team, away=team)
	
	if len(gameday) > 0 :
		game = gameday[0]
		id = game.game_id
		box = mlbgame.game.GameBoxScore(mlbgame.game.box_score(id))
		s = game.nice_score() + "\n" + box.print_scoreboard()
		await bot.say(s)

def sub(subreddit, selfpost=False):
	list = []
	for submission in reddit.subreddit(subreddit).hot(limit=25):
		if submission.is_self == selfpost:
			if submission.is_self:
				list.append(submission.title)
			else:
				list.append(submission.url)
	num = random.randint(0,len(list)-1)
	return (list[num])

@bot.command()
async def mockify(*text:str):
	input = ""
	for s in text:
		input = input + " " + s
	input = input.strip()
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
async def fuck():
	l = ['barves','cubs','dh','dodgers','mets','yankees']
	num = random.randint(0,len(l)-1)
	await bot.say(('the '+ l[num]).upper())
	
@bot.command()
async def pajokie():
	await bot.say("https://cdn.discordapp.com/attachments/328677264566910977/343555639227842571/image.jpg")

# get tokens from file
f = open('tokens.txt','r')
reddit_token = f.readline().strip()
discord_token = f.readline().strip()
f.close()

reddit = praw.Reddit(client_id='gFy19-aFuFdAdQ',
                     client_secret=reddit_token,
                     user_agent='windows:natsgifbot (by /u/efitz11)')
print(reddit.read_only)
bot.run(discord_token)