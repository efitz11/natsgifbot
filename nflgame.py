from urllib.request import urlopen, Request
import time, json,html

#Constants
MODE_ACTIVE = 0
MODE_INACTIVE = 1
GAME_STATUS_PRE = 0
GAME_STATUS_IN = 1
GAME_STATUS_POST = 2

def get_game(team, sport):
    req = Request("http://espn.go.com/"+sport+"/scoreboard")
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
        score1 = int(event['competitions'][0]['competitors'][0]['score'])
        team1abv = event['competitions'][0]['competitors'][0]['team']['abbreviation']
        team2 = html.unescape(event['competitions'][0]['competitors'][1]['team']['location'])
        tid2 = event['competitions'][0]['competitors'][1]['id']
        score2 = int(event['competitions'][0]['competitors'][1]['score'])
        team2abv = event['competitions'][0]['competitors'][1]['team']['abbreviation']
            
        homestatus = event['competitions'][0]['competitors'][0]['homeAway']
        name1 = event['competitions'][0]['competitors'][0]['team']['name']
        name2 = event['competitions'][0]['competitors'][1]['team']['name']
        
        game['odds'] = ""
        if 'odds' in event['competitions'][0]:
            game['odds'] = " - " + event['competitions'][0]['odds'][0]['details']
        
        if homestatus == 'home':
            game['hometeam'], game['homeid'], game['homeabv'], game['homescore'], game['awayteam'], game['awayid'], game['awayabv'], game['awayscore'], game['homename'], game['awayname'] =\
                team1, tid1, team1abv, score1, team2, tid2, team2abv, score2, name1, name2
        else:
            game['hometeam'], game['homeid'], game['homeabv'], game['homescore'], game['awayteam'], game['awayid'], game['awayabv'], game['awayscore'], game['homename'], game['awayname'] = \
                team2, tid2, team2abv, score2, team1, tid1, team1abv, score1, name2, name1
            
        #print (game)
        games.append(game)
    if len(team) == 0:
        output = "Today's games:\n"
        for game in games:
            output = output + "**%s %s** @ **%s %s** - %s%s\n" % (game['awayabv'], game['awayscore'],game['homeabv'], game['homescore'], game['time'],game['odds'])
        return output
    for game in games:
        if game['hometeam'].lower() == team.lower() or game['homeabv'].lower() == team.lower() or game['awayteam'].lower() == team.lower() or game['awayabv'].lower() == team.lower() or game['homename'].lower() == team.lower() or game['awayname'].lower() == team.lower():
            return "**%s %s** @ **%s %s** - %s%s" % (game['awayabv'], game['awayscore'],game['homeabv'], game['homescore'], game['time'], game['odds'])
    
    return "game not found"