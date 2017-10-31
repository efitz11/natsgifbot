import json, html
from urllib.request import urlopen, Request


def get_scores(team):
    req = Request("https://statsapi.web.nhl.com/api/v1/schedule?expand=schedule.teams,schedule.linescore")
    req.headers["User-Agent"] = "windows 10 bot"
    # Load data
    scoreData = json.loads(urlopen(req).read().decode("utf-8"))
    
    games = scoreData['dates'][0]['games']
    #print (games)
    
    if len(games) == 0:
        return
    if len(team) != 0:
        team = team.lower()
        for game in games:
            awayt = game['teams']['away']['team']['abbreviation'].lower()
            homet = game['teams']['home']['team']['abbreviation'].lower()
            awayfull = game['teams']['away']['team']['name'].lower()
            homefull = game['teams']['home']['team']['name'].lower()
            if awayt == team or homet == team or awayfull.find(team)>-1 or homefull.find(team)>-1:
                return "```python\n" + parse_game(game) + "```"
        return
    output = "```python\n"
    for game in games:
        output = output + parse_game(game)

    return output + "```"

def parse_game(game):
    aways = game['teams']['away']['score']
    awayt = game['teams']['away']['team']['abbreviation']
    homes = game['teams']['home']['score']
    homet = game['teams']['home']['team']['abbreviation']
    awayfull = game['teams']['away']['team']['name']
    homefull = game['teams']['home']['team']['name']
    output = "%s %s @ %s %s" % (awayt, aways, homet, homes)
    if game['status']['abstractGameState'] == 'Live':
        period = game['linescore']['currentPeriodOrdinal']
        time = game['linescore']['currentPeriodTimeRemaining']
        output = output + " - %s %s\n" % (period, time)
    else:
        state = game['status']['detailedState']
        output = output + " - %s\n" % state
    return output