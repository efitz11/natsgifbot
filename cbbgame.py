from urllib.request import urlopen, Request
import time, json,html
from datetime import datetime, timedelta
'''
borrowed some code from /r/cfb's IRC bot, thank you
https://github.com/diagonalfish/FootballBotX2
'''


#Constants
MODE_ACTIVE = 0
MODE_INACTIVE = 1
GAME_STATUS_PRE = 0
GAME_STATUS_IN = 1
GAME_STATUS_POST = 2

base_url = "http://espn.go.com/mens-college-basketball/scoreboard/_/"

type = "50"
# Other leagues go here

groupmap = {
            "atlantic 10":"3", "a10":"3",
            "asun":"46","a-sun":"46",
            "acc":"2", 
            "am-east":"1","ameast":"1",
            "american":"62", "aac":"62",
            "big 12":"8", 
            "big east":"4",
            "big sky":"5",
            "big south":"6",
            "big ten":"7", "big 10":"7",
            "big west":"9",
            "c-usa":"11", "cusa":"11",
            "caa":"10",
            "horizon":"45",
            "ivy":"12",
            "maac":"13",
            "mac":"14",
            "meac":"16",
            "mvc":"18",
            "mw":"44",
            "nec":"19",
            "ovc":"20",
            "pac 12":"21", "pac-12":"21",
            "patriot":"22",
            "sec":"23",
            "swac":"26",
            "southern":"24",
            "southland":"25",
            "summit":"49",
            "sun belt":"27",
            "wac":"30",
            "wcc":"29"}

def get_game(team,delta=None):
    if team == "conferences":
        output = ""
        for t in groupmap:
            output = output + t + ", "
        return output
        
    now = datetime.now()
    
    all = False
    if delta is not None:
        now = now + timedelta(days=delta)
        url = base_url + "group/" + type + "/date/"+ str(now.year) + str(now.month).zfill(2) + str(now.day).zfill(2)
        if team is None or team.lower() == "none" or team.lower() == "all":
            all = True
            url = base_url + "date/"+ str(now.year) + str(now.month).zfill(2) + str(now.day).zfill(2)
        elif team.lower() in groupmap:
            group = groupmap[team.lower()]
            url = base_url + "group/" + group + "/date/"+ str(now.year) + str(now.month).zfill(2) + str(now.day).zfill(2)
            all = True 
    else:        
        url = "http://espn.go.com/mens-college-basketball/scoreboard/_/group/" + type + "/year/"+str(now.year)+"/seasontype/2/?t=" + str(time.time())
        if team == None or team == "" or team.lower == "none":
            url = "http://www.espn.com/mens-college-basketball/scoreboard/_/year/" + str(now.year)+"/seasontype/2"
            all = True
        elif team.lower() in groupmap:
            url = "http://www.espn.com/mens-college-basketball/scoreboard/_/group/" + groupmap[team.lower()] + "/year/"+str(now.year)+"/seasontype/2/"
            all = True
    
    req = Request(url)
    req.headers["User-Agent"] = "windows 10 bot"
    # Load data
    scoreData = urlopen(req).read().decode("utf-8")
    scoreData = scoreData[scoreData.find('window.espn.scoreboardData 	= ')+len('window.espn.scoreboardData 	= '):]
    scoreData = json.loads(scoreData[:scoreData.find('};')+1])
    #print(scoreData)
    #f = open('espnout.txt','w')
    #f.write(json.dumps(scoreData))
    #f.close()

    games = []
    if delta is None:
        date = scoreData['events'][0]['date']
        date = date[:date.find('T')].split('-')
        date = date[1] + "/" + date[2] + "/" + date[0]
    else:
        date = str(now.month) + "/" + str(now.day) + "/" + str(now.year)
    for event in scoreData['events']:
        game = dict()

        game["date"] = event['date']
        status = event['status']['type']['state']
        if status == "pre":
            game['status'] = GAME_STATUS_PRE
            game['time'] = event['status']['type']['shortDetail']
        elif status == "in":
            game['status'] = GAME_STATUS_IN
            game['time'] = event['status']['type']['shortDetail']
        else:
            game['status'] = GAME_STATUS_POST
            game['time'] = "FINAL"
        team1 = html.unescape(event['competitions'][0]['competitors'][0]['team']['location'])
        tid1 = event['competitions'][0]['competitors'][0]['id']
        score1 = event['competitions'][0]['competitors'][0]['score']
        team1abv = event['competitions'][0]['competitors'][0]['team']['abbreviation']
        team2 = html.unescape(event['competitions'][0]['competitors'][1]['team']['location'])
        tid2 = event['competitions'][0]['competitors'][1]['id']
        score2 = event['competitions'][0]['competitors'][1]['score']
        team2abv = event['competitions'][0]['competitors'][1]['team']['abbreviation']
        
        rank1 = event['competitions'][0]['competitors'][0]['curatedRank']
        rank2 = event['competitions'][0]['competitors'][1]['curatedRank']
        
        game['odds'] = ""
        if 'odds' in event['competitions'][0]:
            if 'details' in event['competitions'][0]['odds'][0]:
                game['odds'] = " - " + event['competitions'][0]['odds'][0]['details']
        
        # Hawaii workaround
        if team1 == "Hawai'i":
            team1 = "Hawaii"
        if team2 == "Hawai'i":
            team2 = "Hawaii"
            
        homestatus = event['competitions'][0]['competitors'][0]['homeAway']
        for l in event['links']:
            if l['text'] == "Summary":
                game['link'] = l['href']
        
        if homestatus == 'home':
            game['hometeam'], game['homeid'], game['homeabv'], game['homescore'], game['awayteam'], game['awayid'], game['awayabv'], game['awayscore'], game['homerank'], game['awayrank']=\
                team1, tid1, team1abv, score1, team2, tid2, team2abv, score2, rank1, rank2
        else:
            game['hometeam'], game['homeid'], game['homeabv'], game['homescore'], game['awayteam'], game['awayid'], game['awayabv'], game['awayscore'], game['homerank'], game['awayrank'] = \
                team2, tid2, team2abv, score2, team1, tid1, team1abv, score1, rank2, rank1
            
        #print (game)
        games.append(game)
    #output = "Games on " + str(now.month) + "/" + str(now.day) + "/" + str(now.year)
    dateline = "Games on " + date
    if all:
        output = ""
        for game in games:
            ar = game['awayrank']['current']
            hr = game['homerank']['current']
            awayr = "("+str(ar)+")" if (ar <= 25 and ar > 0) else ""
            homer = "("+str(hr)+")" if (hr <= 25 and hr > 0) else ""
            output = output +  "%s %s %s @ %s %s %s # %s%s\n" % (awayr.rjust(4),game['awayabv'].rjust(5), game['awayscore'].rjust(2), homer.rjust(4),game['homeabv'].rjust(5), game['homescore'].rjust(2), game['time'],game['odds'])
            #output = output + pretty_print_game(game)
        return (dateline + "\n```python\n" + output+"```")
    for game in games:
        if game['hometeam'].lower() == team.lower() or game['homeabv'].lower() == team.lower() or game['awayteam'].lower() == team.lower() or game['awayabv'].lower() == team.lower():
            # ar = game['awayrank']['current']
            # hr = game['homerank']['current']
            # awayr = "("+str(ar)+")" if (ar <= 25 and ar > 0) else ""
            # homer = "("+str(hr)+")" if (hr <= 25 and hr > 0) else ""
            # return output + "\n```python\n%s%s %s @ %s%s %s # %s%s```" % (awayr,game['awayabv'], game['awayscore'], homer,game['homeabv'], game['homescore'], game['time'], game['odds'])
            output = pretty_print_game(game)
            return (dateline + " - <" + game['link'] + ">\n```python\n" + output + "```")
    return "game not found"

def pretty_print_game(game):
    ar = game['awayrank']['current']
    hr = game['homerank']['current']
    awayr = "("+str(ar)+")" if (ar <= 25 and ar > 0) else ""
    homer = "("+str(hr)+")" if (hr <= 25 and hr > 0) else ""
    namejust = max(len(game['awayabv']), len(game['homeabv']))
    if '-' in game['time']:
        gdate = game['time'].split('-')[0]
        gtime = game['time'].split('- ')[1]
    else:
        gdate = ""
        gtime = game['time']
    output = "%s %s %s # %s\n%s %s %s # %s%s\n" % (awayr.rjust(4),game['awayabv'].rjust(namejust), game['awayscore'].rjust(2), gdate, homer.rjust(4),game['homeabv'].rjust(namejust), game['homescore'].rjust(2), gtime, game['odds'])
    return output
    
def pretty_print_games(games):
    started = []
    pregame = []
    final = []
    for game in games:
        if game['status'] == GAME_STATUS_PRE:
            started.append(game)
        else:
            pregame.append(game)
    
