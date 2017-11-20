from urllib.request import urlopen, Request
import time, json,html
from datetime import datetime
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
            "horizon":"45"
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

def get_game(team):
    now = datetime.now()
    url = "http://espn.go.com/mens-college-basketball/scoreboard/_/group/" + type + "/year/"+str(now.year)+"/seasontype/2/?t=" + str(time.time())
    all = False
    if team == None or team == "":
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
        
        if homestatus == 'home':
            game['hometeam'], game['homeid'], game['homeabv'], game['homescore'], game['awayteam'], game['awayid'], game['awayabv'], game['awayscore'], game['homerank'], game['awayrank']=\
                team1, tid1, team1abv, score1, team2, tid2, team2abv, score2, rank1, rank2
        else:
            game['hometeam'], game['homeid'], game['homeabv'], game['homescore'], game['awayteam'], game['awayid'], game['awayabv'], game['awayscore'], game['homerank'], game['awayrank'] = \
                team2, tid2, team2abv, score2, team1, tid1, team1abv, score1, rank2, rank1
            
        #print (game)
        games.append(game)
    if all:
        output = "```python\n"
        for game in games:
            awayr = "("+str(game['awayrank']['current'])+")" if game['awayrank']['current'] <= 25 else ""
            homer = "("+str(game['homerank']['current'])+")" if game['homerank']['current'] <= 25 else ""
            output = output +  "%s %s %s @ %s %s %s # %s%s\n" % (awayr.rjust(4),game['awayabv'].rjust(5), game['awayscore'].rjust(2), homer.rjust(4),game['homeabv'].rjust(5), game['homescore'].rjust(2), game['time'],game['odds'])
        return (output+"```")
    for game in games:
        if game['hometeam'].lower() == team.lower() or game['homeabv'].lower() == team.lower() or game['awayteam'].lower() == team.lower() or game['awayabv'].lower() == team.lower():
            awayr = "("+str(game['awayrank']['current'])+") " if game['awayrank']['current'] <= 25 else ""
            homer = "("+str(game['homerank']['current'])+") " if game['homerank']['current'] <= 25 else ""
            return "```python\n%s%s %s @ %s%s %s # %s%s```" % (awayr,game['awayabv'], game['awayscore'], homer,game['homeabv'], game['homescore'], game['time'], game['odds'])
    return "game not found"
