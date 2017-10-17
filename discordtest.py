import discord
from discord.ext import commands
import random
import mlbgame
import datetime
import praw

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
async def gif(name : str):
	if name == "electricchair":
		await bot.say('https://gfycat.com/ClearHauntingHoverfly')
	elif name == "boo":
		await bot.say('https://gfycat.com/IllustriousOpulentGoldfish')
	elif name == "murder":
		await bot.say('https://gfycat.com/FondVibrantHousefly')
	return
	
@bot.command()
async def mlb(team :str):
	team = team.title()
	print("team: %s" % team)
	now = datetime.datetime.now()
	print(now.year, now.month, now.day)
	day = mlbgame.day(now.year, now.month, now.day, home=team, away=team)
	print(day)
	if len(day) > 0 :
		game = day[0]
		id = game.game_id
		print (id)
		#print(mlbgame.game.box_score(id))
		await bot.say(game)

@bot.command()
async def mlbd(team :str, year:int, month:int, day:int):
	team = team.title()
	print("team: %s" % team)
	gameday = mlbgame.day(year, month, day, home=team, away=team)
	if len(gameday) > 0 :
		game = gameday[0]
		id = game.game_id
		box = mlbgame.game.GameBoxScore(mlbgame.game.box_score(id))
		s = game.nice_score() + "\n" + box.print_scoreboard()
		await bot.say(s)
		#await bot.say(box.print_scoreboard())

def sub(subreddit, selfpost=False):
	list = []
	for submission in reddit.subreddit(subreddit).hot(limit=25):
		if submission.is_self == selfpost:
			list.append(submission.url)
	num = random.randint(0,len(list)-1)
	return (list[num])
	
		
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
	
reddit = praw.Reddit(client_id='gFy19-aFuFdAdQ',
                     client_secret='',
                     user_agent='windows:natsgifbot (by /u/efitz11)')
print(reddit.read_only)
bot.run('')