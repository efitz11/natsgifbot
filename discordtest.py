import discord
from discord.ext import commands
import random
from datetime import datetime, timedelta, time
import re, json, os
import asyncio
from urllib.request import urlopen, Request
import urllib.parse
import utils

import mymlbgame, cfbgame, nflgame, xmlreader, nhlscores, cbbgame, stocks, olympics, gifs, gfycat
import odds as oddsmod
import weather as weathermodule
import frinkiac, web, tacobell
import hq as hqmod

bot = commands.Bot(command_prefix='!')
prefixes = ['!', '?', 'bot ', 'Bot']

extensions = ["baseball","sports","reddit"]

auth_users = ['fitz#6390']

pattern69 = re.compile('(^|[\s\.]|\$)[6][\.]*[9]([\s\.]|x|%|$|th)')
patterncheer = re.compile('cheer$', re.IGNORECASE)
patternpoop = re.compile('mets|phillies|braves',re.IGNORECASE)
patternperf = re.compile('perfect game',re.IGNORECASE)
patternbenoit = re.compile('benoit$',re.IGNORECASE)
patternalexaplay = re.compile('alexa play', re.IGNORECASE)
patternshitbot = re.compile('shit bot', re.IGNORECASE)
# patterneaton = re.compile('(?<!(Miami University Great ))(Adam Eaton)', re.IGNORECASE)
patterntwitter = re.compile('https://.*twitter.com/([^/?]+)*')

pidfile = 'discordbotpid.txt'
miscfile = 'misc.json'
    
# get tokens from file
f = open('tokens.txt','r')
reddit_clientid = f.readline().strip()
reddit_token = f.readline().strip()
discord_token = f.readline().strip()
f.close()

f = open('channelids.txt')
main_chid = f.readline().strip()
f.close()

#write pid file
f = open(pidfile,'w')
f.write(str(os.getpid()))
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
					'z':u"\U0001F1FF",
                    '0':u"\u0030" + u"\u20E3",
                    '1':u"\u0031" + u"\u20E3",
                    '2':u"\u0032" + u"\u20E3",
                    '3':u"\u0033" + u"\u20E3",
                    '4':u"\u0034" + u"\u20E3",
                    '5':u"\u0035" + u"\u20E3",
                    '6':u"\u0036" + u"\u20E3",
                    '7':u"\u0037" + u"\u20E3",
                    '8':u"\u0038" + u"\u20E3",
                    '9':u"\u0039" + u"\u20E3"}

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    
@bot.command()
async def gif(*name : str):
    """returns a nationals gif matching the search query"""
    # await bot.say(gifs.fuzzygif(' '.join(name)))
    await bot.say(gifs.gif(' '.join(name)))

@bot.command()
async def gfy(*name : str):
    """returns a gif from efitz111 on gfycat"""
    await bot.say(gfycat.search_gfys(' '.join(name)))

@bot.command(pass_context=True)
async def gfyall(ctx, *name : str):
    """returns up to 30 gifs from efitz111 on gfycat"""
    if 'bot' in str(ctx.message.channel):
        await bot.say(gfycat.search_gfys(' '.join(name), num=30))
    else:
        await bot.say("this command is only allowed in the bot channel")

@bot.command()
async def mlbgif(*name : str):
    """returns a nationals gif matching the search query"""
    await bot.say(gifs.get_mlb_gif(' '.join(name)))    
    
@bot.command(pass_context=True)
async def gifall(ctx, *name:str):
    """returns all gifs matching the search query"""
    if 'bot' not in str(ctx.message.channel):
        await bot.say("this command is only allowed in the bot channel")
        return
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

            # if len(output) > 1850:
            #     output = output + "... more gifs not displayed due to char limit"
            #     break
        for m in utils.split_long_message(output):
            await bot.say(m)
        # await bot.say(output.strip())
        
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
        
@bot.command()
async def mockify(*text:str):
    """MocKiFy aNy sTrIng of tExT"""
    input = ' '.join(text).lower()
    await bot.say(mockify_text(input))

@bot.command(pass_context=True)
async def mock(ctx, *search:str):
    """mOcKiFy tHe pReViOuS MeSsaGe"""
    srch = ' '.join(search)
    async for m in bot.logs_from(ctx.message.channel,limit=10):
        skip = False
        for prefix in prefixes:
            if m.clean_content.startswith(prefix):
                skip = True
                break
        if not skip:
            if srch.lower() in m.clean_content.lower():
                await bot.say(mockify_text(m.clean_content.lower()))
                return
    
@bot.command()
async def memeify(*text:str):
    """M E M E I F Y   A N Y   S T R I N G   O F   T E X T"""
    input = ''.join(text)
    output = ""
    for s in input:
        output = output + " " + s
    await bot.say(output.strip().upper())

def last_replace(s, old, new):
    li = s.rsplit(old, 1)
    return new.join(li)

def uwuify_text(text):
    # borrowed from github.com/zenrac, thanks
    vowels = ['a', 'e', 'i', 'o', 'u', 'A', 'E', 'I', 'O', 'U']
    smileys = [';;w;;', '^w^', '>w<', 'UwU', '(・`ω\´・)', '(´・ω・\`)']

    text = text.replace('L', 'W').replace('l', 'w')
    text = text.replace('R', 'W').replace('r', 'w')

    text = last_replace(text, '!', '! {}'.format(random.choice(smileys)))
    text = last_replace(text, '?', '? owo')
    text = last_replace(text, '.', '. {}'.format(random.choice(smileys)))

    for v in vowels:
        if 'n{}'.format(v) in text:
            text = text.replace('n{}'.format(v), 'ny{}'.format(v))
        if 'N{}'.format(v) in text:
            text = text.replace('N{}'.format(v), 'N{}{}'.format('Y' if v.isupper() else 'y', v))

    return text

@bot.command()
async def uwuify(*text:str):
    """uwu what's this?"""
    text = (' ').join(text)
    await bot.say(uwuify_text(text))

@bot.command(pass_context=True)
async def uwu(ctx, *search:str):
    """uwuify the pwevious command"""
    srch = ' '.join(search)
    async for m in bot.logs_from(ctx.message.channel,limit=10):
        skip = False
        for prefix in prefixes:
            if m.clean_content.startswith(prefix):
                skip = True
                break
        if not skip:
            if srch.lower() in m.clean_content.lower():
                await bot.say(uwuify_text(m.clean_content.lower()))
                return

@bot.command()
async def fire():
    await bot.say("DAVEY MARTINEZ")

@bot.command(pass_context=True)
async def fuck(ctx,*addlist):
    with open(miscfile, 'r') as f:
        s = json.loads(f.read())

    if len(addlist) > 0:
        write = False
        if str(ctx.message.author) in auth_users:
            if addlist[0] == 'add':
                add = ' '.join(addlist[1:]).upper()
                s['fucklist'].append(add)
                write = True
            elif addlist[0] == 'remove':
                remove = ' '.join(addlist[1:]).upper()
                s['fucklist'].remove(remove)
                write = True
        if addlist[0] == 'list':
            output = ""
            for item in s['fucklist']:
                output = "%s%s, " % (output, item)
            output = output[:-2]
            await bot.say(output)
        else:
            search = ' '.join(addlist).lower()
            for l in s['fucklist']:
                if search in l.lower():
                    await bot.say("FUCK " + l.upper())
                    return
        if write:
            with open(miscfile, 'w') as f:
                f.write(json.dumps(s, indent=4))
            await bot.say("done.")
        return

    l = s['fucklist']
    num = random.randint(0,len(l)-1)
    await bot.say((l[num]).upper())

@bot.command()
async def pajokie():
    """GO HOKIES!"""
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

def get_youtube(query):
    query = query.replace(' ','+')
    url = "https://www.youtube.com/results?search_query=" + query

    req = Request(url)
    req.headers["User-Agent"] = "windows 10 bot"
    resource = urlopen(req)
    content = resource.read().decode('utf-8')

    findstr = "<li><div class=\"yt-lockup yt-lockup-tile yt-lockup-video vve-check clearfix\" data-context-item-id=\""
    contents = content[content.find(findstr)+len(findstr):]
    vid = contents[:contents.find("\"")]
    return "https://youtube.com/watch?v="+vid

@bot.command()
async def youtube(*query:str):
    """get the first youtube video for a query"""
    q = '+'.join(query)
    await bot.say(get_youtube(q))

@bot.command()
async def weather(*location:str):
    """oh the weather outside is weather"""
    output = weathermodule.get_current_weather('%2C'.join(location))
    await bot.say(output)
@bot.command(pass_context=True)
async def forecast(ctx, *location:str):
    if 'bot' in str(ctx.message.channel):
        output = weathermodule.get_forecast('%2C'.join(location))
        await bot.say(output)
    else:
        await bot.say("this command is only allowed in the bot channel")

@bot.command()
async def radar(*query):
    """show pic of the current DC weather radar"""
    randstr = "?%d" % random.randint(0,9999)
    if len(query) == 0:
        await bot.say("<https://weather.com/weather/radar/interactive/l/20003:4:US?layer=radar>")
        await bot.say("https://api.weather.com/v2/maps/dynamic?geocode=38.85,-76.95&h=600&w=800&lod=8&product=twcRadarMosaic&map=light&format=jpg&language=en&apiKey=d522aa97197fd864d36b418f39ebb323&a=0"
                      + randstr)
    else:
        lat,lon = weathermodule.get_lat_lon('+'.join(query))
        lat,lon = (round(lat,1),round(lon,1))
        await bot.say("https://api.weather.com/v2/maps/dynamic?geocode=%.2f,%.2f&h=600&w=800&lod=8&product=twcRadarMosaic&map=light&format=jpg&language=en&apiKey=d522aa97197fd864d36b418f39ebb323&a=0" % (lat,lon)
                      + randstr)

@bot.command()
async def snow():
    """show NWS snow probability image"""
    randstr = "?%d" % random.randint(0,9999)
    await bot.say("https://www.weather.gov/images/lwx/winter/StormTotalSnowWeb1.png" + randstr)

@bot.command()
async def metar(airport_code:str):
    """get airport metar"""
    await bot.say(weathermodule.get_current_metar(airport_code))

def convert_number_to_emoji(num):
    snum = str(num)
    out = ""
    for s in snum:
        out = out + emoji_letter_map[s]
    return out

@bot.command(pass_context=True)
async def link(ctx,*args):
    objname = 'links'
    with open(miscfile,'r') as f:
        s = json.loads(f.read())
    if objname not in s:
        s[objname] = {}
    links = s[objname]
    if len(args) == 3 and args[0] == 'add':
        if str(ctx.message.author) in auth_users:
            linkname = args[1].lower()
            if linkname in links:
                await bot.say('link name already in use')
            else:
                if args[2].startswith('http'):
                    s[objname][linkname] = args[2]
                    with open(miscfile,'w') as f:
                        f.write(json.dumps(s, indent=4))
                    await bot.say('link %s added.' % linkname)
                else:
                    await bot.say('link doesn\'t begin with `http`')
        else:
            await bot.say(links['dont'])
    else:
        name = args[0].lower()
        if name == 'list':
            output = ""
            for l in links:
                output = output + l + ", "
            await bot.say(output[:-2])
        elif name in links:
            await bot.say(links[name])
        else:
            await bot.say("could not find a link named %s" % name)

@bot.command(pass_context=True)
async def countdown(ctx, *addlist):
    with open(miscfile,'r') as f:
        s = json.loads(f.read())

    if len(addlist) == 5 and addlist[0] == "add":
        if str(ctx.message.author) in auth_users:
            name = addlist[1]
            month = int(addlist[2])
            day = int(addlist[3])
            year = int(addlist[4])
            if month > 0 and month <= 12:
                if day > 0 and day <= 31:
                    if year >= 2018:
                        d = dict()
                        d['name'] = name
                        d['month'] = month
                        d['day'] = day
                        d['year'] = year
                        s['countdown'].append(d)

    countdown = s['countdown']
    now = datetime.now()
    removelist = []
    dayslist = []
    for event in countdown:
        d = datetime(event['year'], event['month'], event['day']) - now
        if d.days >= -1:
            dayslist.append((d.days, event))
        else:
            removelist.append(event)

    for event in removelist:
        s['countdown'].remove(event)

    dayslist.sort()
    sortedlist = []
    for d, value in dayslist:
        sortedlist.append(value)
        await bot.say("%s %s until %s" % (convert_number_to_emoji(d+1), "day" if (d+1 == 1) else "days", value['name']))
    s['countdown'] = sortedlist

    with open(miscfile,'w') as f:
        f.write(json.dumps(s, indent=4))

@bot.command()
async def stock(*symbol:str):
    """Get a stock quote. Only works for stocks and ETFs"""
    if len(symbol) == 0:
        await bot.say(stocks.get_indexes())
        return
    out = stocks.get_quote(symbol[0])
    await bot.say(out)
    
@bot.command()
async def crypto(*symbol:str):
    """list the top 10 crypto prices, or a specific coin. from coinmarketcap"""
    sym = '-'.join(symbol)
    await bot.say(web.get_cryptocurrency_data(sym))
    
@bot.command()
async def frink(*query:str):
    """generate a gif from frinkiac"""
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

@bot.command()
async def zoop():
    """zoop"""
    await bot.say(":point_right: :sunglasses: :point_right:")

@bot.command()
async def pooz():
    """pooz"""
    await bot.say(":point_left: :sunglasses: :point_left:")

@bot.command(pass_context=True)
async def react(ctx, reactionstr:str, *search:str):
    """turn string into emoji and react to the most recent message that matches"""
    search = ' '.join(search)
    msg = reactionstr.lower()
    async for m in bot.logs_from(ctx.message.channel,limit=10):
        if not m.clean_content.startswith('!') and search in m.clean_content.lower():
            for s in msg:
                if s in emoji_letter_map:
                    await bot.add_reaction(m, emoji_letter_map[s])
            return
            
@bot.command()
async def wiki(*query:str):
    """get a link to wikipedia's first search result for your query"""
    await bot.say(web.get_wiki_page(' '.join(query)))

@bot.command()
async def beer(*beer_name):
    """get untappd info on a beer"""
    await bot.say(web.search_untappd(' '.join(beer_name)))
    
@bot.command()
async def poll(question, *answers):
    """Start a poll - the bot will post the question with the possible answers
       List the answers after the question, if any argument has spaces, remember
       to "quote the argument" to keep it as one entry
       
       if you don't enter any answers, the answers will default to yes/no"""
    output = "**%s\n\n%s**```python\n\n" % ("POLL", question)
    a = ord('A')
    for i in range(len(answers)):
        output = output + "\t" + chr(a+i) + " - " + answers[i] + "\n"
        
    if len(answers) == 0:
        output = output + "\tYes or No\n"
        m = await bot.say(output + "```")
        await bot.add_reaction(m,emoji_letter_map['y'])
        await bot.add_reaction(m,emoji_letter_map['n'])
        return
        
    m = await bot.say(output + "```")
    a = ord('a')
    
    for i in range(len(answers)):
        await bot.add_reaction(m,emoji_letter_map[chr(a+i)])
        
@bot.command(pass_context=True)
async def terminate(ctx):
    """no"""
    await bot.say("%s is not in the terminators file. This incident will be reported." % ctx.message.author.mention)

@bot.command(pass_context=True)
async def slap(ctx, *text:str):
    """Slap a user with a wet trout"""
    slappee = ' '.join(text)
    server = ctx.message.server
    for member in server.members:
        if slappee in member.name:
            slappee = member.mention
            break

    slapper = ctx.message.author

    await bot.say('*%s slaps %s around a bit with a large trout*' % (slapper.mention, slappee))
    
@bot.command()
async def clap(*text:str):
    await bot.say('👏'.join(text).upper() + '👏')

@bot.command()
async def big(text:str):
    """bot posts the requested image. use \"!big list\" to get the current list"""
    text = text.lower()
    basepath = '/home/ubuntu/images/'
    filelist = os.listdir(basepath)
    filelist.sort()
    if text == "list":
        output = ""
        for f in filelist:
            output = output + f[:f.find('.')] + ", "
        await bot.say(output[:-2])
    else:
        for f in filelist:
            fname = f[:f.find('.')]
            if fname == text:
                await bot.upload(basepath+f)
                
@bot.command(pass_context=True)
async def hq(ctx, *text:str):
    """commands for getting notified about hq games
    
       !hq register - register yourself for pings
       !hq unregister - take yourself off the list
       !hq check - check if you are registered
       !hq list - list everyone registered
       !hq ping - ping everyone registered
       !hq <number of people left> - get the payout for this number of people, assuming $5000 prize
       !hq <prize> <number of people> - get the payout for the number of people and the corresponding prize"""
    helpstring = "use '!help hq' to get help about this command"
    if len(text) == 0:
        await bot.say(helpstring)
    else:
        if len(text) == 2 and text[0].isdigit() and text[1].isdigit():
            money = round(int(text[0]) / int(text[1]),2)
            await bot.say("$" + str(money))
            return
        elif len(text) == 1 and text[0].isdigit():
            money = round(5000 / int(text[0]),2)
            await bot.say("$" + str(money))
            return
        t = ''.join(text)
        if t == "register":
            await bot.say(hqmod.register_user(ctx.message.author))
        elif t == "unregister":
            await bot.say(hqmod.unregister_user(ctx.message.author))
        elif t == "check":
            if hqmod.is_user_registered(ctx.message.author):
                await bot.say(ctx.message.author.display_name + " is registered for hq pings.")
            else:
                await bot.say(ctx.message.author.display_name + " is **NOT** registered for hq pings.")
        elif t == "ping":
            await bot.say(hqmod.list_users(mention=True))
        elif t == "list":
            await bot.say(hqmod.list_users())
        else:
            await bot.say(helpstring)
            
@bot.command()
async def medals():
    """get the current 2018 medal count"""
    await bot.say(olympics.get_medal_count())

@bot.command()
async def daymedals(*delta:int):
    """detailed list of the medals handed out for the day"""
    if len(delta)==0:
        d = 0
    else:
        d = delta[0]
    await bot.say(olympics.get_days_medals(delta=d))
    
@bot.command()
async def ig(username:str):
    """get the latest instagram post by the user"""
    await bot.say(web.get_latest_ig_post(username))

@bot.command()
async def tweet(username:str):
    """get the latest tweet by the user"""
    await bot.say(web.get_latest_tweet(username))

@bot.command()
async def imdb(*query):
    """get the first IMDB result for your query"""
    await bot.say(web.search_imdb(' '.join(query)))

@bot.command()
async def m8ball():
    """ask the magic 8 ball a question"""
    responses = ["It is certain", "As I see it, yes","Reply hazy try again","Don't count on it",
                 "It is decidedly so","Most likely","Ask again later","My reply is no",
                 "Without a doubt","Outlook good","Better not tell you now","My sources say no",
                 "Yes definitely","Yes","Cannot predict now","Outlook not so good",
                 "You may rely on it","Signs point to yes","Concentrate and ask again","Very doubtful"]
    await bot.say(responses[random.randint(0,len(responses)-1)])

@bot.command()
async def ud(*query):
    """query UrbanDictionary"""
    list = web.ud_def(' '.join(query))
    for l in list:
        await bot.say(l)

@bot.command()
async def cocktail(*query):
    """get info about a cocktail"""
    await bot.say(web.cocktail(' '.join(query)))

@bot.command(pass_context=True)
async def log(ctx, numlines=5):
    """print the last few lines of the bot log to see errors"""
    if str(ctx.message.author) in auth_users:
        from collections import deque
        out = ""
        d = deque(open("bot.log"), numlines+1)
        d.pop()
        for s in d:
            out = out + s
        out = "```%s```" % out
        await bot.say(out)

@bot.command()
async def meme(*query):
    """Get information about a meme, provided by KnowYourMeme"""
    await bot.say(web.kym(' '.join(query)))

@bot.command()
async def fitz(*message):
    """fitz"""
    await bot.say("<:fitz:535186966451322930> %s <:fitz:535186966451322930>" % ' '.join(message).upper())

@bot.command()
async def define(*query):
    """define a word"""
    await bot.say(web.get_definition(' '.join(query)))

@bot.command()
async def tb(num:int=3):
    """get a random taco bell order"""
    await bot.say(tacobell.random_items(num))

@bot.command()
async def say(*message):
    await bot.say(' '.join(message))

@bot.command()
async def odds(*query):
    leagues = ["ufc"]
    if len(query) == 0 or query[0] not in leagues:
        await bot.say('```Supported leagues: %s```' % leagues)
    else:
        league = query[0]
        team = ' '.join(query[1:])
        if len(team) == 0:
            team = None
        await bot.say("```python\n%s```" % oddsmod.get_league_odds_table(league, team=team))

@bot.event
async def on_message(message):
    #stuff
    # print(bot.commands)
    if message.author == bot.user:
        if patterntwitter.search(message.content):
            verified = web.check_tweet_verified(re.search(patterntwitter, message.content).group(1))
            if verified:
                await bot.add_reaction(message, u"\u2611")
            else:
                await bot.add_reaction(message, u"\u274C")
        return
    if message.content.startswith('bot ') or message.content.startswith('Bot '):
        message.content = '!' + message.content[4:]
    if message.content.startswith(bot.command_prefix):
        print("%s input command: %s" % (message.author, message.content))
        await bot.process_commands(message)
    elif message.content.split(' ')[0][1:] in bot.commands and message.content.startswith('?'):
        print("%s input command: %s" % (message.author, message.content))
        message.content = '!'+message.content[1:]
        await bot.delete_message(message)
        await bot.process_commands(message)
    else:
        # if 'reddit.com' in message.content:
        #     urls = re.findall(r'(https?://\S+)', message.content)
        #     for url in urls:
        #         print(url)
        #         await bot.send_message(message.channel, "```%s```" % bot.cogs['Reddit'].get_comment(url))
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
        if patternperf.search(message.content):
            await bot.send_message(message.channel,"FUCK JOSE TABATA")
        if patternbenoit.search(message.content):
            await bot.send_message(message.channel,"balls.")
        if patternshitbot.search(message.content):
            await bot.send_message(message.channel, "Fuck off! I'm doing my best.")
        match = patternalexaplay.search(message.content)
        if match:
            query = message.content[match.end():]
            await bot.send_message(message.channel,get_youtube(query.strip()))

        if patterntwitter.search(message.content):
            verified = web.check_tweet_verified(re.search(patterntwitter, message.content).group(1))
            if verified:
                await bot.add_reaction(message, u"\u2611")
            else:
                await bot.add_reaction(message, u"\u274C")
        # if patterneaton.search(message.content):
        #     await bot.send_message(message.channel,"Miami University Great Adam Eaton*")

updater = mymlbgame.Updater()

async def my_bg_task():
    await bot.wait_until_ready()
    channel = discord.Object(id = main_chid)
    # while not bot.is_closed:
        #print("update")
        # teamname = "Astros"
        # now = datetime.now() - timedelta(hours=3)
        # day = mlbgame.day(now.year, now.month, now.day, home=teamname, away=teamname)
        
        # if len(day) > 0 :
        #     game = day[0]
        #     id = game.game_id
        #     output = updater.update(id)
        #     if output != "" and output != None:
        #         output = "```python\n" + output + "```"
        #         await bot.send_message(channel,output)
        # await asyncio.sleep(15)
        
async def update_mlbtr():
    await bot.wait_until_ready()
    channel = bot.get_channel(id = main_chid)
    # triviach = discord.utils.find(lambda m: m.name == 'trivia', channel.server.channels)
    while not bot.is_closed:
        # if hqmod.check_hq():
            # await bot.send_message(channel,":rotating_light: HQ is starting soon :rotating_light: --- head to %s" % (triviach.mention))
            # await bot.send_message(triviach,":rotating_light: HQ is starting soon :rotating_light:")
            # await bot.send_message(triviach, hqmod.list_users(mention=True))
            
        out = mlbtr.mlbtr()
        if out != None:
            await bot.send_message(channel,out)
        await asyncio.sleep(60*3)
        
mlbtr = xmlreader.XmlReader()

#print(reddit.read_only)
#bot.loop.create_task(my_bg_task())
bot.loop.create_task(update_mlbtr())
for ext in extensions:
    bot.load_extension(ext)
bot.run(discord_token)
