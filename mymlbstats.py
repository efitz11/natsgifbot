from urllib.request import urlopen, Request
from datetime import datetime, timedelta
import time
import json, os
import mlb.BoxScore as BoxScore

def _get_date_from_delta(delta=None):
    now = datetime.now() - timedelta(hours=5)
    if delta is not None and (delta.startswith('+') or delta.startswith('-')):
        delta = int(delta)
        now = now + timedelta(days=delta)
    return now

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
    url = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=" + date + "&expand=schedule.teams,schedule.decisions"
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    s = json.loads(urlopen(req).read().decode("utf-8"))
    games = s['dates'][0]['games']
    output = ""
    for game in games:
        awayid = str(game['teams']['away']['team']['id'])
        homeid = str(game['teams']['home']['team']['id'])
        print(awayid,homeid)
        awayt = game['teams']['away']['team']['abbreviation']
        homet = game['teams']['home']['team']['abbreviation']
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

def get_single_game_info(gamepk, gamejson):
    game = gamejson
    output = ""
    abstractstatus = game['status']['abstractGameState']
    detailstatus = game['status']['detailedState']
    awayabv = game['teams']['away']['team']['abbreviation']
    homeabv = game['teams']['home']['team']['abbreviation']
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
            probaway = game['teams']['away']['probablePitcher']['fullName'].split(',')[0]
            probhome = game['teams']['home']['probablePitcher']['fullName'].split(',')[0]
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
            output = output + "%s %s %s @ %s %s %s # %s\n" % (awayabv, aruns, arecord, homeabv, hruns, hrecord, detailstatus)
            decisions = game['decisions']
            wp = get_last_name(decisions['winner']['fullName'])
            lp = get_last_name(decisions['loser']['fullName'])
            output = output + "\t WP: %s LP: %s" % (wp.ljust(12), lp.ljust(12))
            if 'save' in decisions:
                output = output + "\t SV: %s" % (get_last_name(decisions['save']['fullName']))
            output = output + "\n"
        except KeyError:
            # no score - game was probably postponed
            output = output + "%s %s @ %s %s # %s\n" % (awayabv, arecord, homeabv, hrecord, detailstatus)

    return output

def get_all_game_info(delta=None):
    """delta is + or - a number of days"""
    s = get_day_schedule(delta)
    games = s['dates'][0]['games']

    output = ""
    if delta is not None:
        now = _get_date_from_delta(delta)
        output = "For %d/%d/%d:\n\n" % (now.month,now.day,now.year)
    for game in games:
        gamepk = str(game['gamePk'])
        output = output + get_single_game_info(gamepk, game)
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

def get_day_schedule(delta=None):
    now = _get_date_from_delta(delta)
    date = str(now.year) + "-" + str(now.month).zfill(2) + "-" + str(now.day).zfill(2)
    url = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=" + date + "&expand=schedule.teams,schedule.decisions"
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
    url = "https://statsapi.mlb.com/api/v1/standings/regularSeason?" \
          "leagueId=" + str(lgid) + "&season=" + str(now.year) + "&hydrate=team"
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    s = json.loads(urlopen(req).read().decode("utf-8"))
    return s

def get_single_game(team,delta=None):
    """delta is + or - a number of days"""
    s = get_day_schedule(delta)
    games = s['dates'][0]['games']
    output = ""
    if delta is not None:
        output = "For %d/%d/%d:\n\n" % (now.month,now.day,now.year)
    for game in games:
        gamepk = str(game['gamePk'])
        awayabv = game['teams']['away']['team']['abbreviation'].lower()
        homeabv = game['teams']['home']['team']['abbreviation'].lower()
        awayname = game['teams']['away']['team']['name'].lower()
        homename = game['teams']['home']['team']['name'].lower()
        if team in awayabv or team in homeabv or team in awayname or team in homename:
            output = output + get_single_game_info(gamepk,game)
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
    # gamepks = get_gamepk_from_team(team)
    # if len(gamepks) == 0:
    #     return []
    plays = []
    for gamepk in gamepks:
        pbp = get_pbp(gamepk)
        for i in pbp['scoringPlays']:
            play = pbp['allPlays'][i]
            inning = play['about']['halfInning'].upper() + " " + str(play['about']['inning'])
            desc = "With " + play['matchup']['pitcher']['fullName'] + " pitching, " + play['result']['description']
            plays.append((inning, desc))
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
    output = output + "%s %s %s %s %s %s %s %s %s\n" %\
             (' '.rjust(3),'W'.rjust(3),'L'.rjust(3),'PCT'.rjust(5), 'GB'.rjust(4), ' WCGB', 'STK',
              'RS'.rjust(3),'RA'.rjust(3))
    for team in div['teamRecords']:
        abbrev = team['team']['abbreviation']
        streak = team['streak']['streakCode'].ljust(3)
        wins = str(team['wins']).rjust(3)
        loss = str(team['losses']).rjust(3)
        pct = team['leagueRecord']['pct'].rjust(5)
        rundiff = team['runDifferential']
        ra = str(team['runsAllowed']).rjust(3)
        rs = str(team['runsScored']).rjust(3)
        gb = team['gamesBack'].rjust(4)
        wcgb = team['wildCardGamesBack'].rjust(5)
        output = output + "%s %s %s %s %s %s %s %s %s\n" %\
                 (abbrev, wins, loss, pct, gb, wcgb, streak, rs, ra)
    output = output + "```"
    print(output)
    return output

if __name__ == "__main__":
    #make_mlb_schedule()
    #get_mlb_teams()
    #print(get_single_game("nationals",delta="+1"))
    # print(get_all_game_info(delta='-1'))
    #get_ET_from_timestamp("2018-03-31T20:05:00Z")
    get_div_standings("nle")
    #bs = BoxScore.BoxScore(get_boxscore('529456'))
    #bs.print_box()
