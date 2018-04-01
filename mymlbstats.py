from urllib.request import urlopen, Request
from datetime import datetime, timedelta
import time
import json, os

def get_schedule():
    now = datetime.now() - timedelta(hours=5)
    date = str(now.year) + "-" + str(now.month).zfill(2) + "-" + str(now.day).zfill(2)
    schd = "mlb" + os.sep + date + ".txt"
    return schd

def get_gamepk_from_team(team):
    schd = get_schedule()
    if not os.path.isfile(schd):
        make_mlb_schedule()
    games = []
    with open(schd,'r') as f:
        for line in f:
            if team.lower() in line.lower():
                game = line.strip()
                gamepk = game.split(':')[0]
                games.append(gamepk)
    return games

def get_last_name(fullname):
    if "Jr." in fullname:
        fullname = fullname[:-4]
    return fullname.split(' ')[-1]

def get_abbrev(teamid):
    teamid = str(teamid)
    teams = []
    with open('mlb/teams.txt','r') as f:
        for line in f:
            teams.append(line.strip().split(','))
    abbrev = [item for item in teams if teamid in item][0][1].ljust(3)
    return abbrev

def get_ET_from_timestamp(timestamp):
    utc = datetime.strptime(timestamp,"%Y-%m-%dT%H:%M:00Z") #"2018-03-31T20:05:00Z",
    nowtime = time.time()
    diff = datetime.fromtimestamp(nowtime) - datetime.utcfromtimestamp(nowtime)
    utc = utc + diff
    return(datetime.strftime(utc, "%I:%M ET"))

def make_mlb_schedule(date=None):
    if date is None:
        now = datetime.now() - timedelta(hours=5)
        date = str(now.year) + "-" + str(now.month).zfill(2) + "-" + str(now.day).zfill(2)
    schd = "mlb" + os.sep + date + ".txt"
    teams = []
    with open('mlb/teams.txt','r') as f:
        for line in f:
            teams.append(line.strip().split(','))

    #print(teams)
    url = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=" + date
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    s = json.loads(urlopen(req).read().decode("utf-8"))
    games = s['dates'][0]['games']
    output = ""
    for game in games:
        awayid = str(game['teams']['away']['team']['id'])
        homeid = str(game['teams']['home']['team']['id'])
        print(awayid,homeid)
        awayt = [item for item in teams if awayid in item][0]
        homet = [item for item in teams if homeid in item][0]
        print(awayt)
        print(homet)

        output += "%s:%s:%s\n" % (game['gamePk'],awayt,homet)
    with open(schd,'w') as f:
        f.write(output)
        print("wrote to ", schd)
    return games

def get_mlb_teams():
    url = "http://statsapi.mlb.com/api/v1/teams?sportId=1"
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    s = json.loads(urlopen(req).read().decode("utf-8"))
    teams = s['teams']
    teammap = {}
    for s in teams:
        #print("%s - %s" % (s['id'],s['name']))
        teammap[s['id']] = s['name']
    for s in sorted(teammap):
        print(s,teammap[s])

def get_single_game_info(gamepk, gamejson, teams):
    game = gamejson
    output = ""
    abstractstatus = game['status']['abstractGameState']
    detailstatus = game['status']['detailedState']
    awayid = str(game['teams']['away']['team']['id'])
    homeid = str(game['teams']['home']['team']['id'])
    awayabv = [item for item in teams if awayid in item][0][1].ljust(3)
    homeabv = [item for item in teams if homeid in item][0][1].ljust(3)
    #print(gamepk)
    if abstractstatus == "Live":
        ls = get_linescore(gamepk)
        if ls['isTopInning']:
            inning = "Top"
        else:
            inning = "Bot"
        inning = inning + " " + ls["currentInningOrdinal"]
        outs = ls['outs']
        strikes = ls['strikes']
        balls = ls['balls']
        awayruns = ls['teams']['away']['runs']
        homeruns = ls['teams']['home']['runs']
        awayhits = ls['teams']['away']['hits']
        homehits = ls['teams']['home']['hits']
        bases = "---"
        if 'first' in ls['offense']:
            bases = "1" + bases[1:]
        if 'second' in ls['offense']:
            bases = bases[:1] + "2" + bases[2:]
        if 'third' in ls['offense']:
            bases = bases[:2] + "3"
        batter =  get_last_name(ls['offense']['batter']['fullName'])
        try:
            pitcher = get_last_name(ls['defense']['pitcher']['fullName'])
        except:
            pitcher = ""
        output = output + "%s %s @ %s %s: %s - %s outs %s Count: (%s-%s)\n" % (awayabv, awayruns, homeabv, homeruns, inning, outs, bases, balls, strikes)
        output = output + "\t" + "Pitching: %s \tBatting: %s\n" % (pitcher, batter)
        if ls['currentInning'] >= 6 and awayhits == 0:
            output = output + "\t##############################\n"
            output = output + "\t" + awayabv + "  HAS NO HITS SO FAR\n"
            output = output + "\t##############################\n"
        if ls['currentInning'] >= 6 and homehits == 0:
            output = output + "\t##############################\n"
            output = output + "\t" + homeabv + "  HAS NO HITS SO FAR\n"
            output = output + "\t##############################\n"
    elif abstractstatus == "Preview":
        awaywins = game['teams']['away']['leagueRecord']['wins']
        awayloss = game['teams']['away']['leagueRecord']['losses']
        homewins = game['teams']['home']['leagueRecord']['wins']
        homeloss = game['teams']['home']['leagueRecord']['losses']
        if detailstatus == "Scheduled":
            feed = get_game_feed(gamepk)
            probaway = feed['gameData']['probablePitchers']['away']['fullName'].split(',')[0]
            probhome = feed['gameData']['probablePitchers']['home']['fullName'].split(',')[0]
        elif detailstatus == "Pre-Game":
            ls = get_linescore(gamepk)
            probaway = get_last_name(ls['offense']['pitcher']['fullName'])
            probhome = get_last_name(ls['defense']['pitcher']['fullName'])
        arecord = "(%s-%s)" % (awaywins, awayloss)
        hrecord = "(%s-%s)" % (homewins, homeloss)
        time = get_ET_from_timestamp(game['gameDate'])
        output = output + "%s %s @ %s %s # %s - %s\n" % (awayabv, arecord, homeabv, hrecord, time,detailstatus)
        output = output + "\t%s v %s\n" % (probaway, probhome)
    elif abstractstatus == "Final":
        awaywins = game['teams']['away']['leagueRecord']['wins']
        awayloss = game['teams']['away']['leagueRecord']['losses']
        homewins = game['teams']['home']['leagueRecord']['wins']
        homeloss = game['teams']['home']['leagueRecord']['losses']
        arecord = "(%s-%s)" % (awaywins, awayloss)
        hrecord = "(%s-%s)" % (homewins, homeloss)
        try:
            aruns = game['teams']['away']['score']
            hruns = game['teams']['home']['score']
        except:
            aruns = ""
            hruns = ""
        output = output + "%s %s %s @ %s %s %s # %s\n" % (awayabv, aruns, arecord, homeabv, hruns, hrecord, detailstatus)

    return output

def get_all_game_info():
    now = datetime.now() - timedelta(hours=5)
    date = str(now.year) + "-" + str(now.month).zfill(2) + "-" + str(now.day).zfill(2)
    url = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=" + date
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    s = json.loads(urlopen(req).read().decode("utf-8"))
    games = s['dates'][0]['games']

    #load team info
    teams = []
    with open('mlb/teams.txt','r') as f:
        for line in f:
            teams.append(line.strip().split(','))

    output = ""
    for game in games:
        gamepk = str(game['gamePk'])
        output = output + get_single_game_info(gamepk, game, teams)
    return output

def get_linescore(gamepk):
    url = "https://statsapi.mlb.com/api/v1/game/" + gamepk + "/linescore"
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    s = json.loads(urlopen(req).read().decode("utf-8"))
    return s

def get_boxscore(gamepk):
    url = "https://statsapi.mlb.com/api/v1/game/" + gamepk + "/boxscore"
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    s = json.loads(urlopen(req).read().decode("utf-8"))
    return s

def get_game_feed(gamepk):
    url = "https://statsapi.mlb.com/api/v1/game/" + gamepk + "/feed/live"
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    s = json.loads(urlopen(req).read().decode("utf-8"))
    return s

def get_day_schedule():
    now = datetime.now() - timedelta(hours=5)
    date = str(now.year) + "-" + str(now.month).zfill(2) + "-" + str(now.day).zfill(2)
    url = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=" + date
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    s = json.loads(urlopen(req).read().decode("utf-8"))
    return s

def get_pbp(gamepk):
    url = "https://statsapi.mlb.com/api/v1/game/" + gamepk + "/playByPlay"
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    s = json.loads(urlopen(req).read().decode("utf-8"))
    return s

def get_lg_standings(lgid):
    now = datetime.now()
    url = "https://statsapi.mlb.com/api/v1/standings/regularSeason?leagueId=" + str(lgid) + "&season=" + str(now.year)
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    s = json.loads(urlopen(req).read().decode("utf-8"))
    return s

def get_single_game(team):
    gamepks = get_gamepk_from_team(team)
    teams = []
    with open('mlb/teams.txt','r') as f:
        for line in f:
            teams.append(line.strip().split(','))
    schedule = get_day_schedule()
    output = ""
    for game in schedule['dates'][0]['games']:
        try:
            idx = gamepks.index(str(game['gamePk']))
        except ValueError:
            continue
        gamepk = gamepks[idx]
        output = output + get_single_game_info(gamepk,game,teams)
        abstractstatus = game['status']['abstractGameState']
        if abstractstatus == "Live":
            pbp = get_pbp(gamepk)
            try:
                if 'description' not in pbp['allPlays'][-1]['result']:
                    lastplay = pbp['allPlays'][-2]
                else:
                    lastplay = pbp['allPlays'][-1]
                desc = lastplay['result']['description']
                pitch = lastplay['matchup']['pitcher']['fullName']
                output = output + "\tLast Play: With " + pitch + " pitching, " + desc + "\n"
            except Exception as e:
                print(e)
    return output

def list_scoring_plays(team):
    gamepk = get_gamepk_from_team(team)
    if gamepk == None:
        return []
    pbp = get_pbp(gamepk)
    plays = []
    for i in pbp['scoringPlays']:
        inning = pbp['allPlays'][i]['about']['halfInning'].upper() + " " + str(pbp['allPlays'][i]['about']['inning'])
        plays.append((inning, pbp['allPlays'][i]['result']['description']))
    return plays

def get_div_standings(div):
    div = div.lower()
    if div == "ale":
        id = 103
        idx = 1
    elif div == "alc":
        id = 103
        idx = 2
    elif div == "alw":
        id = 103
        idx = 0
    elif div == "nle":
        id = 104
        idx = 2
    elif div == "nlc":
        id = 104
        idx = 0
    elif div == "nlw":
        id = 104
        idx = 1
    else:
        return

    standings = get_lg_standings(id)
    div = standings['records'][idx]
    output = "```python\n"
    output = output + "%s %s %s %s\n" %(' '.rjust(3),'W'.rjust(3),'L'.rjust(3),'PCT'.rjust(5))
    for team in div['teamRecords']:
        teamid = team['team']['id']
        abbrev = get_abbrev(teamid)
        streak = team['streak']['streakCode']
        wins = str(team['wins']).rjust(3)
        loss = str(team['losses']).rjust(3)
        pct = team['leagueRecord']['pct'].rjust(5)
        rundiff = team['runDifferential']
        runall = team['runsAllowed']
        runscored = team['runsScored']
        output = output + "%s %s %s %s\n" % (abbrev, wins, loss, pct)
    output = output + "```"
    print(output)
    return output

if __name__ == "__main__":
    #make_mlb_schedule()
    #get_mlb_teams()
    #get_single_game("nationals")
    #get_all_game_info()
    #get_ET_from_timestamp("2018-03-31T20:05:00Z")
    get_div_standings("ale")
    get_div_standings("alc")
    get_div_standings("alw")
