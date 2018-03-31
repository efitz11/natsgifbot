from urllib.request import urlopen, Request
from datetime import datetime, timedelta
import time
import json, os

def get_schedule():
    now = datetime.now() - timedelta(hours=5)
    date = str(now.year) + "-" + str(now.month).zfill(2) + "-" + str(now.day).zfill(2)
    schd = "mlb" + os.sep + date + ".txt"
    return schd

def get_last_name(fullname):
    if "Jr." in fullname:
        fullname = fullname[:-4]
    return fullname.split(' ')[-1]

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
        output = output + "%s %s @ %s %s # %s\n" % (awayabv, arecord, homeabv, hrecord, detailstatus)

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

def get_single_game(team):
    schd = get_schedule()
    if not os.path.isfile(schd):
        make_mlb_schedule()
    game = ""
    with open(schd,'r') as f:
        for line in f:
            if team.lower() in line.lower():
                game = line.strip()
    output = ""
    if game != "":
        gamepk = game.split(':')[0]
        teams = []
        with open('mlb/teams.txt','r') as f:
            for line in f:
                teams.append(line.strip().split(','))
        schedule = get_day_schedule()
        for game in schedule['dates'][0]['games']:
            if str(game['gamePk']) == gamepk:
                output = get_single_game_info(gamepk,game,teams)
                abstractstatus = game['status']['abstractGameState']
                if abstractstatus == "Live":
                    pbp = get_pbp(gamepk)
                    if 'description' not in pbp['allPlays'][-1]:
                        lastplay = pbp['allPlays'][-2]
                    else:
                        lastplay = pbp['allplays'][-1]
                    output = output + "\tLast Play: " + lastplay['result']['description'] + "\n"
    return(output)

if __name__ == "__main__":
    #make_mlb_schedule()
    #get_mlb_teams()
    get_single_game("nationals")
    #get_all_game_info()
    #get_ET_from_timestamp("2018-03-31T20:05:00Z")
