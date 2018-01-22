import discord
from discord.ext import commands
import random
import mlbgame
from datetime import datetime, timedelta, time
import praw, prawcore.exceptions
import re, json
import asyncio
from urllib.request import urlopen, Request
import urllib.parse

import mymlbgame, cfbgame, nflgame, xmlreader, nhlscores, cbbgame, stocks
import weather as weathermodule
import frinkiac, cryptocurrency, wikipedia

bot = commands.Bot(command_prefix='!')

extensions = ["baseball","sports","reddit"]

pattern69 = re.compile('(^|[\s\.]|\$)[6][\.]*[9]([\s\.]|x|%|$|th)')
patterncheer = re.compile('cheer', re.IGNORECASE)
patternsolis = re.compile('solis', re.IGNORECASE)
patternpoop = re.compile('mets|phillies|braves',re.IGNORECASE)
patternperf = re.compile('perfect game',re.IGNORECASE)

    
# get tokens from file
f = open('tokens.txt','r')
reddit_clientid = f.readline().strip()
reddit_token = f.readline().strip()
discord_token = f.readline().strip()
f.close()

f = open('channelids.txt')
main_chid = f.readline().strip()
f.close()

emoji_letter_map = {'a':u"\U0001F1E6",
					'b':u"\U0001F1E7",
					'c':u"\U0001F1E8",
					'd':u"\U0001F1E9",
					'e':u"\U0001F1EA",
					'f':u"\U0001F1EB",
					'g':u"\U0001F1EC",
					'h':u"\U0001F1ED",
					'i':u"\U0001F1EE",
					'j':u"\U0001F1EF",
					'k':u"\U0001F1F0",
					'l':u"\U0001F1F1",
					'm':u"\U0001F1F2",
					'n':u"\U0001F1F3",
					'o':u"\U0001F1F4",
					'p':u"\U0001F1F5",
					'q':u"\U0001F1F6",
					'r':u"\U0001F1F7",
					's':u"\U0001F1F8",
					't':u"\U0001F1F9",
					'u':u"\U0001F1FA",
                    'v':u"\U0001F1FB",
					'w':u"\U0001F1FC",
					'x':u"\U0001F1FD",
					'y':u"\U0001F1FE",
					'z':u"\U0001F1FF",}

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    
@bot.command()
async def gif(*name : str):
    """returns a nationals gif matching the search query"""
    matches = []
    patterns = []
    query = ""
    for s in name:
        patterns.append(re.compile(s,re.IGNORECASE))
        query = query + " " + s
    f = open('postlist.csv','r')
    for line in f:
        search = ','.join(line.split(',')[:-1])
        matched = True
        for pat in patterns:
            if not re.search(pat,search):
                matched = False
                break
        if matched:
            matches.append(line)
    f.close()
    #print ("query: " + query.strip())
    #print (matches)
    if len(matches) == 0:
        await bot.say("No matches")
        return
    num = random.randint(0,len(matches)-1)
    await bot.say(matches[num].strip())
        
    return
    
@bot.command()
async def gifall(*name:str):
    """returns all gifs matching the search query"""
    matches = []
    patterns = []
    query = ""
    for s in name:
        patterns.append(re.compile(s,re.IGNORECASE))
        query = query + " " + s
    f = open('postlist.csv','r')
    for line in f:
        search = ','.join(line.split(',')[:-1])
        matched = True
        for pat in patterns:
            if not re.search(pat,search):
                matched = False
                break
        if matched:
            matches.append(line)
    f.close()
    if len(matches) == 0:
        await bot.say("No matches")
        return
    else:
        output = ""
        for m in matches:
            m=m.strip()
            cpos = m.rfind(',') + 1
            output = output + m[:cpos] + "<" + m[cpos:] + ">\n"
            if len(output) > 1850:
                output = output + "... more gifs not displayed due to char limit"
                break
        print(output)
        await bot.say(output.strip())
        
    return
                
def mockify_text(text):
    last = False
    output = ""
    prob = 30
    for s in text:
        num = random.randint(0,100)
        if not s.isalpha():
            output = output + s
            continue
        if not last and num > prob:
            output = output + (s.upper())
            prob = 30
            last = True
        else:
            output = output + (s)
            prob = prob - 10
            last = False
    return output
    
class mocker():
    def __init__(self):
        self.lastmsg = {}
    def update(self,msg,channel):
        self.lastmsg[channel] = msg
    def mock(self,channel):
        try:
            text = mockify_text(self.lastmsg[channel].lower())
        except KeyError:
            text = "Error: no previous message for this channel"
        return text
        
@bot.command()
async def mockify(*text:str):
    """MocKiFy aNy sTrIng of tExT"""
    input = ' '.join(text).lower()
    await bot.say(mockify_text(input))

@bot.command(pass_context=True)
async def mock(ctx):
    """mOcKiFy tHe pReViOuS MeSsaGe"""
    await bot.say(mockobj.mock(ctx.message.channel))
    
@bot.command()
async def memeify(*text:str):
    """M E M E I F Y   A N Y   S T R I N G   O F   T E X T"""
    input = ''.join(text)
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
async def car():
    """show a random pic of a car"""
    l = ["cars","carporn","autos","shitty_car_mods"]
    i =  random.randint(0,len(l)-1)
    await bot.say(sub(l[i]))

@bot.command()
async def fp():
    """get a random FP quote"""
    await bot.say(sub('justFPthings',selfpost=True))    

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
async def giflist():
    await bot.say("https://github.com/efitz11/natsgifbot/blob/master/postlist.csv")
    
@bot.command()
async def youtube(*query:str):
    """get the first youtube video for a query"""
    q = '+'.join(query)
    url = "https://www.youtube.com/results?search_query=" + q
    
    req = Request(url)
    req.headers["User-Agent"] = "windows 10 bot"
    resource = urlopen(req)
    content = resource.read().decode(resource.headers.get_content_charset())
    
    findstr = "<li><div class=\"yt-lockup yt-lockup-tile yt-lockup-video vve-check clearfix\" data-context-item-id=\""
    contents = content[content.find(findstr)+len(findstr):]
    vid = contents[:contents.find("\"")]
    await bot.say("https://youtube.com/watch?v="+vid)

@bot.command()
async def weather(*location:str):
    output = weathermodule.get_current_weather('%2C'.join(location))
    await bot.say(output)
@bot.command()
async def forecast(*location:str):
    output = weathermodule.get_forecast('%2C'.join(location))
    await bot.say(output)

@bot.command()
async def countdown():
    od = datetime(2018,3,29) - datetime.now()
    st = datetime(2018,2,23) - datetime.now()
    pc = datetime(2018,2,14) - datetime.now()
    ho = datetime(2018,4,5) - datetime.now()

    await bot.say("%s days until pitchers and catchers report" % (pc.days+1))
    await bot.say("%s days until Spring Training, 2018" % (st.days+1))
    await bot.say("%s days until Opening Day, 2018" % (od.days+1))
    await bot.say("%s days until National's Home Opener, 2018" % (ho.days+1))

@bot.command()
async def stock(symbol:str):
    out = stocks.get_quote(symbol)
    await bot.say(out)
    
@bot.command()
async def crypto(*symbol:str):
    sym = '-'.join(symbol)
    await bot.say(cryptocurrency.get_cryptocurrency_data(sym))
    
@bot.command()
async def frink(*query:str):
    if query[0] == 'gif':
        query = query[1:]
        query = ' '.join(query)
        await bot.say(frinkiac.get_gif(query))
    else:
        query = ' '.join(query)
        await bot.say(frinkiac.get_meme(query))
    
@bot.command()
async def nice():
    """bot says 'nice''"""
    await bot.say("nice")
    
@bot.command(pass_context=True)
async def react(ctx, id:str, *msg:str):
    """turn string into emoji and react to the message specified
        you can retrieve the message id if you have developer mode on"""
    msg = ' '.join(msg)
    message = await bot.get_message(ctx.message.channel, id)
    msg = msg.lower()
    for s in msg:
        if s in emoji_letter_map:
            await bot.add_reaction(message, emoji_letter_map[s])
            
@bot.command()
async def wiki(*query:str):
    """get a link to wikipedia's first search result for your query"""
    await bot.say(wikipedia.get_wiki_page(' '.join(query)))
    
@bot.command()
async def poll(question, *answers):
    """Start a poll - the bot will post the question with the possible answers
       List the answers after the question, if any argument has spaces, remember
       to "quote the argument" to keep it as one entry"""
    output = "**POLL**```python\n#" + question + "\n"
    a = ord('A')
    for i in range(len(answers)):
        output = output + "\t" + chr(a+i) + " - " + answers[i] + "\n"
    m = await bot.say(output + "```")
    a = ord('a')
    for i in range(len(answers)):
        await bot.add_reaction(m,emoji_letter_map[chr(a+i)])
    
@bot.event
async def on_message(message):
    #stuff
    if message.author == bot.user:
        return
    if message.content.startswith(bot.command_prefix):
        await bot.process_commands(message)
    elif message.content.startswith('?'):
        message.content = '!'+message.content[1:]
        await bot.delete_message(message)
        await bot.process_commands(message)
    else:
        if pattern69.search(message.content):
            await bot.add_reaction(message, emoji_letter_map['n'])
            await bot.add_reaction(message, emoji_letter_map['i'])
            await bot.add_reaction(message, emoji_letter_map['c'])
            await bot.add_reaction(message, emoji_letter_map['e'])
        if patterncheer.search(message.content):
            await bot.add_reaction(message, emoji_letter_map['n'])
            await bot.add_reaction(message, emoji_letter_map['a'])
            await bot.add_reaction(message, emoji_letter_map['t'])
            await bot.add_reaction(message, emoji_letter_map['s'])
        if patternsolis.search(message.content):
            await bot.add_reaction(message, u"\U0001F528")
        if patternpoop.search(message.content):
            await bot.add_reaction(message, u"\U0001F4A9")
        if patternperf.search(message.content):
            await bot.send_message(message.channel,"FUCK JOSE TABATA")
        mockobj.update(str(message.content),message.channel)

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

def check_hq():
    dayst = time(14,57,0)
    dayet = time(15,0,0)
    nightst = time(20,57,0)
    nightet = time(21,0,0)
    
    dayofweek = datetime.today().weekday()
    now = datetime.time(datetime.now())
    if dayofweek >= 5 and (now<nightst): #weekends are nights only
        return False
    else:
        if (now>dayst and now<dayet)  or (now>nightst and now<nightet):
            return True
    return False
        
async def update_mlbtr():
    await bot.wait_until_ready()
    channel = bot.get_channel(id = main_chid)
    triviach = discord.utils.find(lambda m: m.name == 'trivia', channel.server.channels)
    while not bot.is_closed:
        if check_hq():
            await bot.send_message(channel,":rotating_light: HQ is starting soon :rotating_light: --- head to %s" % (triviach.mention))
            await bot.send_message(triviach,":rotating_light: HQ is starting soon :rotating_light:")
            
        out = mlbtr.mlbtr()
        if out != None:
            await bot.send_message(channel,out)
        await asyncio.sleep(60*3)
        
mockobj = mocker()
mlbtr = xmlreader.XmlReader()

#print(reddit.read_only)
#bot.loop.create_task(my_bg_task())
bot.loop.create_task(update_mlbtr())
for ext in extensions:
    bot.load_extension(ext)
bot.run(discord_token)
