from urllib.request import urlopen, Request
import time, json,html
from datetime import datetime

#Constants
MODE_ACTIVE = 0
MODE_INACTIVE = 1
GAME_STATUS_PRE = 0
GAME_STATUS_IN = 1
GAME_STATUS_POST = 2

NBA_TEAM_WIDTH = 4
NBA_SCORE_WIDTH = 3
NFL_TEAM_WIDTH = 3
NFL_SCORE_WIDTH = 2


def get_game(team, sport):
    #see if team is actually a week number
    isint = False
    try:
        w = int(team)
        isint = True
        team = ""
    except ValueError:
        pass
    if isint:
        link = "http://espn.go.com/"+sport+"/scoreboard/_/year/" + str(datetime.now().year) + "/seasontype/2/week/" + str(w)
    else:
        link = "http://espn.go.com/"+sport+"/scoreboard"

    link = link + "/?t=" + str(time.time())
    req = Request(link)
    req.headers["User-Agent"] = "windows 10 bot"
    # Load data
    scoreData = urlopen(req).read().decode("utf-8")
    f = open('espnout.txt','w',encoding="utf-8")
    f.write(json.dumps(scoreData))
    f.close()
    searchstr = 'window.espn.scoreboardData'
    scoreData = scoreData[scoreData.find(searchstr)+len(searchstr):]
    scoreData = scoreData[scoreData.find('= ')+len('= '):]    
    scoreData = json.loads(scoreData[:scoreData.find('};')+1])
    
    #print(scoreData)
    #f = open('espnout.txt','w')
    #f.write(json.dumps(scoreData))
    #f.close()
    
    if sport == "nba":
        scorew = NBA_SCORE_WIDTH
        teamw = NBA_TEAM_WIDTH
    elif sport == "nfl":
        scorew = NFL_SCORE_WIDTH
        teamw = NFL_TEAM_WIDTH
    
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
        game['homeid'] = event['competitions'][0]['competitors'][0]['id']
        game['awayid'] = event['competitions'][0]['competitors'][1]['id']
        
        for l in event['links']:
            if l['text'] == "Summary":
                game['link'] = l['href']
        
        game['odds'] = ""
        if 'odds' in event['competitions'][0]:
            if 'details' in event['competitions'][0]['odds'][0]:
                game['odds'] = " - " + event['competitions'][0]['odds'][0]['details']
        game['broadcast'] = ""
        for b in event['competitions'][0]['broadcasts']:
            if b['market'] == 'national':
                game['broadcast'] = b['names'][0]
                break
        if sport == "nfl":
            try:
                game['possteam'] = event['competitions'][0]['situation']['possession']
            except:
                game['possteam'] = None
            if 'leaders' in event['competitions'][0]:
                leaders = event['competitions'][0]['leaders'][0]['leaders']
                game['passleader'] = leaders[0]['athlete']['displayName'] + " - " + str(leaders[0]['value']) + " yds"
                leaders = event['competitions'][0]['leaders'][1]['leaders']
                game['rushleader'] = leaders[0]['athlete']['displayName'] + " - " + str(leaders[0]['value']) + " yds"
                leaders = event['competitions'][0]['leaders'][2]['leaders']
                game['recleader'] = leaders[0]['athlete']['displayName'] + " - " + str(leaders[0]['value']) + " yds"
            try:
                game['situation'] = event['competitions'][0]['situation']['downDistanceText']
            except:
                game['situation'] = ""
                
        if homestatus == 'home':
            game['hometeam'], game['homeid'], game['homeabv'], game['homescore'], game['awayteam'], game['awayid'], game['awayabv'], game['awayscore'], game['homename'], game['awayname'] =\
                team1, tid1, team1abv, score1, team2, tid2, team2abv, score2, name1, name2
        else:
            game['hometeam'], game['homeid'], game['homeabv'], game['homescore'], game['awayteam'], game['awayid'], game['awayabv'], game['awayscore'], game['homename'], game['awayname'] = \
                team2, tid2, team2abv, score2, team1, tid1, team1abv, score1, name2, name1
            
        #print (game)
        games.append(game)
    if len(team) == 0:
        if sport == "nfl":
            week = scoreData['week']['number']
            output = "Week %s games:" % week
        else:
            output = "Today's games:"
        output = output + "\n```python\n"
        for game in games:
            output = output + "%s %s @ %s %s # %s - %s%s\n" % (game['awayabv'].ljust(teamw), str(game['awayscore']).rjust(scorew),game['homeabv'].ljust(teamw), str(game['homescore']).rjust(scorew), game['time'], game['broadcast'], game['odds'])
        return output + "```"
    for game in games:
        if game['hometeam'].lower() == team.lower() or game['homeabv'].lower() == team.lower() or game['awayteam'].lower() == team.lower() or game['awayabv'].lower() == team.lower() or team.lower() in game['homename'].lower() or team.lower() in game['awayname'].lower():
            if 'link' in game:
                link = "<"+game['link']+">"
            else:
                link = ""
            return "%s```python\n" % (link) + pretty_print_game(game,sport) + "```"
            #return "<%s>```python\n%s %s @ %s %s # %s%s```" % (game['link'], game['awayabv'], game['awayscore'],game['homeabv'], game['homescore'], game['time'], game['odds'])
            #return "**%s %s** @ **%s %s** - %s%s" % (game['awayabv'], game['awayscore'],game['homeabv'], game['homescore'], game['time'], game['odds'])
    
    return "game not found"

def pretty_print_game(game,sport):
    namejust = max(len(game['awayabv']), len(game['homeabv']))
    odds = game['odds']
    if len(odds) > 0:
        odds = odds[3:]
    output = "%s %s # %s\n%s %s # %s %s\n" % (game['awayabv'].rjust(namejust), str(game['awayscore']).rjust(2), odds, game['homeabv'].rjust(namejust), str(game['homescore']).rjust(2), game['time'], game['broadcast'])
    if sport == "nfl":
        if game['possteam'] is not None:
            if game['possteam'] == game['homeid']:
                output = output[:output.rfind('#')] + '🏈' + output[output.rfind('#')+1:]
            else:
                output = output[:output.find('#')] + '🏈' + output[output.find('#')+1:]
        output = output + game['situation'] + "\n" 
        #output = output + "Pass leader: " + game['passleader'] + "\n"
        #output = output + "Rush leader: " + game['rushleader'] + "\n"
        #output = output + "Recv leader: " + game['recleader'] + "\n"
    return output
    
    
#def get_nfl_standings():
#    req = Request("http://espn.go.com/nfl/standings")
#    req.headers["User-Agent"] = "windows 10 bot"
#    # Load data
#    scoreData = urlopen(req).read().decode("utf-8")
#    rowclass = "<tr class=\" standings-row\">"
#    teamclass = "<span class=\"team-names\">"
#    scoreData = scoreData[scoreData.find(rowclass)]

def get_nfl_scores(team):
    req = Request("http://www.nfl.com/liveupdate/scores/scores.json")
    req.headers["User-Agent"] = "windows 10 bot"
    # Load data
    games = json.loads(urlopen(req).read().decode("utf-8"))
    output = "```python\n"
    for game in games:
        game = games[game]
        homet = game['home']['abbr'].rjust(NFL_TEAM_WIDTH)
        awayt = game['away']['abbr'].rjust(NFL_TEAM_WIDTH)
        homes = str(game['home']['score']['T']).rjust(NFL_SCORE_WIDTH)
        aways = str(game['away']['score']['T']).rjust(NFL_SCORE_WIDTH)
        qtr   = game['qtr']
        clock = game['clock']
        rz = game['redzone']
        post = game['posteam']
        down = game['down']
        togo = game['togo']
        yl = game['yl']
        output = output + "%s %s @ %s %s" % (awayt, aways, homet, homes)
        if qtr != "Final": #todo replace with game in progress status
            output = output + " - %sQ %s\n" % (qtr, clock)
            output = output + "\tPos: %s, %s and %d from %s" % (post,down,togo,yl)
        else:
            output = output + " - %s\n" %(qtr)
    return output + "```"

    
