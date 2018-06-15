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
    return datetime.strftime(utc, "%I:%M ET")

def get_mlb_teams():
    url = "http://statsapi.mlb.com/api/v1/teams?sportId=1"
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    s = json.loads(urlopen(req).read().decode("utf-8"))
    teams = s['teams']
    teammap = {}
    for s in teams:
        # print("%s - %s" % (s['id'],s['name']))
        teammap[s['id']] = s['name']
    for s in sorted(teammap):
        print(s,teammap[s])

def get_single_game_info(gamepk, gamejson, show_on_deck=False, liveonly=False):
    game = gamejson
    output = ""
    abstractstatus = game['status']['abstractGameState']
    detailstatus = game['status']['detailedState']
    awayabv = game['teams']['away']['team']['abbreviation'].ljust(3)
    homeabv = game['teams']['home']['team']['abbreviation'].ljust(3)
    # print(gamepk)
    if abstractstatus == "Live":
        # ls = get_linescore(gamepk)
        ls = game['linescore']
        if ls['isTopInning']:
            inninghalf = "Top"
        else:
            inninghalf= "Bot"
        # inning = inning + " " + ls["currentInningOrdinal"]
        inning = ls["currentInningOrdinal"]
        outs = ls['outs']
        strikes = ls['strikes']
        balls = ls['balls']
        awayruns = ls['teams']['away']['runs']
        homeruns = ls['teams']['home']['runs']
        awayhits = ls['teams']['away']['hits']
        homehits = ls['teams']['home']['hits']
        awayerrs = ls['teams']['away']['errors']
        homeerrs = ls['teams']['home']['errors']
        bases = "---"
        if 'first' in ls['offense']:
            bases = "1" + bases[1:]
        if 'second' in ls['offense']:
            bases = bases[:1] + "2" + bases[2:]
        if 'third' in ls['offense']:
            bases = bases[:2] + "3"
        batter = ls['offense']['batter']['lastName']
        ondeck = "OD: " + ls['offense']['onDeck']['lastName']
        if not show_on_deck:
            ondeck = ""
        try:
            pitcher = ls['defense']['pitcher']['lastName']
        except:
            pitcher = ""
        outjust = 3
        if ls['currentInning'] > 9:
            outjust = 4
        count = "(%s-%s)" % (balls, strikes)
        output = "%s %s %2d %d | %s %s | %s | %s\n" % (awayabv, str(awayruns).rjust(2), awayhits, awayerrs, inninghalf, inning,
                                                     bases.center(5), "P: " + pitcher)
        output = output + "%s %s %2d %d |  %s %s  | %s | %s %s\n" % (homeabv, str(homeruns).rjust(2), homehits, homeerrs,
                                                                     outs, "out".ljust(outjust), count, "B: " + batter, ondeck)
        special = None
        if game['flags']['noHitter']:
            special = "NO H*TTER"
        if game['flags']['perfectGame']:
            special = "P*RFECT GAME"
        if special is not None and awayhits == 0:
            output = output + "\t##############################\n"
            output = output + "\t" + homeabv + " IS THROWING A %s\n" % (special)
            output = output + "\t##############################\n"
        if special is not None and homehits == 0:
            output = output + "\t##############################\n"
            output = output + "\t" + awayabv + " IS THROWING A %s\n" % (special)
            output = output + "\t##############################\n"
    elif liveonly:
        return ""
    elif abstractstatus == "Preview":
        awaywins = game['teams']['away']['leagueRecord']['wins']
        awayloss = game['teams']['away']['leagueRecord']['losses']
        homewins = game['teams']['home']['leagueRecord']['wins']
        homeloss = game['teams']['home']['leagueRecord']['losses']
        if 'probablePitcher' in game['teams']['away']:
            probaway = game['teams']['away']['probablePitcher']['lastName']
            for statgroup in game['teams']['away']['probablePitcher']['stats']:
                if statgroup['type']['displayName'] == "statsSingleSeason" and \
                        statgroup['group']['displayName'] == "pitching":
                    wins = statgroup['stats']['wins']
                    losses = statgroup['stats']['losses']
                    era = statgroup['stats']['era']
                    aprecord = "(%d-%d) %s" % (wins,losses,era)
                    break
        else:
            probaway = "TBD"
            aprecord = ""
        if 'probablePitcher' in game['teams']['home']:
            for statgroup in game['teams']['home']['probablePitcher']['stats']:
                if statgroup['type']['displayName'] == "statsSingleSeason" and \
                        statgroup['group']['displayName'] == "pitching":
                    probhome = game['teams']['home']['probablePitcher']['lastName']
                    wins = statgroup['stats']['wins']
                    losses = statgroup['stats']['losses']
                    era = statgroup['stats']['era']
                    hprecord = "(%d-%d) %s" % (wins,losses,era)
        else:
            probhome = "TBD"
            hprecord = ""
        arecord = "(%s-%s)" % (awaywins, awayloss)
        hrecord = "(%s-%s)" % (homewins, homeloss)
        arecord = arecord.center(7)
        hrecord = hrecord.center(7)
        time = get_ET_from_timestamp(game['gameDate']).ljust(9)
        detailstatus = detailstatus.ljust(9)
        probaway = probaway.ljust(10)
        probhome = probhome.ljust(10)
        # output = output + "%s %s @ %s %s # %s - %s\n" % (awayabv, arecord, homeabv, hrecord, time,detailstatus)
        # output = output + "\t# %s %s v %s %s\n" % (probaway, aprecord, probhome, hprecord)
        output = "%s %s | %s | %s %s\n" % (awayabv, arecord, detailstatus, probaway, aprecord)
        output = output + "%s %s | %s | %s %s\n" % (homeabv, hrecord, time, probhome, hprecord)
    elif abstractstatus == "Final":
        awaywins = game['teams']['away']['leagueRecord']['wins']
        awayloss = game['teams']['away']['leagueRecord']['losses']
        homewins = game['teams']['home']['leagueRecord']['wins']
        homeloss = game['teams']['home']['leagueRecord']['losses']
        arecord = "(%s-%s)" % (awaywins, awayloss)
        hrecord = "(%s-%s)" % (homewins, homeloss)
        arecord = arecord.center(7)
        hrecord = hrecord.center(7)
        try:
            aruns = str(game['teams']['away']['score']).rjust(2)
            hruns = str(game['teams']['home']['score']).rjust(2)
            ls = game['linescore']
            if 'hits' in ls['teams']['away']:
                awayhits = ls['teams']['away']['hits']
                homehits = ls['teams']['home']['hits']
                awayerrs = ls['teams']['away']['errors']
                homeerrs = ls['teams']['home']['errors']
                line1 = "%s %s %2d %d %s" % (awayabv, aruns, awayhits, awayerrs, arecord,)
                line2 = "%s %s %2d %d %s" % (homeabv, hruns, homehits, homeerrs, hrecord)
            else:
                line1 = "%s %s %s" % (awayabv, aruns, arecord,)
                line2 = "%s %s %s" % (homeabv, hruns, hrecord)
            if 'decisions' in game:
                decisions = game['decisions']
                wp = decisions['winner']['lastName']
                lp = decisions['loser']['lastName']
                wprec = ""
                lprec = ""
                for stat in decisions['winner']['stats']:
                    if 'gameLog' == stat['type']['displayName'] and \
                        'pitching' == stat['group']['displayName'] and \
                        'note' in stat['stats']:
                        wprec = stat['stats']['note']
                for stat in decisions['loser']['stats']:
                    if 'gameLog' == stat['type']['displayName'] and \
                            'pitching' == stat['group']['displayName'] and \
                            'note' in stat['stats']:
                        lprec = stat['stats']['note']
                # output = output + "\t WP: %s LP: %s" % (wp.ljust(12), lp.ljust(12))
                save = ""
                rec = ""
                if 'save' in decisions:
                    for stat in decisions['save']['stats']:
                        if 'gameLog' == stat['type']['displayName'] and \
                                'pitching' == stat['group']['displayName'] and \
                                'note' in stat['stats']:
                            rec = stat['stats']['note']
                    # output = output + "\t SV: %s" % (get_last_name(decisions['save']['fullName']))
                    save = "SV: %s" % (decisions['save']['lastName'])
                # output = output + "\n"
                wpdisp = "%s %s" % (wp, wprec)
                line1 = line1 + " | WP: %s %s %s" % (wpdisp.ljust(20), save, rec)
                line2 = line2 + " | LP: %s %s" % (lp, lprec)
            output = output + line1 + "\n" + line2 + "\n"
        except KeyError as e:
            print(e)
            # no score - game was probably postponed
            # output = output + "%s %s @ %s %s # %s\n" % (awayabv, arecord, homeabv, hrecord, detailstatus)
            output = "%s %s | %s\n" % (awayabv, arecord, detailstatus)
            output = output + "%s %s |\n" % (homeabv, hrecord)

    return output

def get_all_game_info(delta=None, liveonly=False):
    """delta is + or - a number of days"""
    s = get_day_schedule(delta)
    games = s['dates'][0]['games']

    output = ""
    if delta is not None:
        now = _get_date_from_delta(delta)
        import calendar
        output = "For %s, %d/%d/%d:\n\n" % (calendar.day_name[now.weekday()],now.month,now.day,now.year)
    for game in games:
        gamepk = str(game['gamePk'])
        out = get_single_game_info(gamepk, game, liveonly=liveonly)
        if len(out) > 0:
            output = output + out + "\n"
    return output

def get_linescore(gamepk):
    url = "https://statsapi.mlb.com/api/v1/game/" + gamepk + "/linescore"
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    s = json.loads(urlopen(req).read().decode("utf-8"))
    return s

def get_boxscore(gamepk):
    url = "https://statsapi.mlb.com/api/v1/game/" + gamepk + "/boxscore?hydrate=person"
    # print(url)
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    s = json.loads(urlopen(req).read().decode("utf-8"))
    return s

def get_game_feed(gamepk):
    url = "https://statsapi.mlb.com/api/v1/game/" + gamepk + "/feed/live"
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    s = json.loads(urlopen(req).read().decode("utf-8"))
    return s

def get_team_info(teamid):
    url = "http://statsapi.mlb.com/api/v1/teams/%d/roster?hydrate=person(stats(splits=statsSingleSeason))" % teamid
    # print(url)
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    s = json.loads(urlopen(req).read().decode("utf-8"))
    return s

def get_day_schedule(delta=None,teamid=None,scoringplays=False):
    now = _get_date_from_delta(delta)
    date = str(now.year) + "-" + str(now.month).zfill(2) + "-" + str(now.day).zfill(2)
    hydrates = "&hydrate=probablePitcher,person,decisions,team,stats,flags,linescore(matchup,runners),previousPlay"
    if scoringplays:
        hydrates = hydrates + ",scoringplays"
    team = ""
    if teamid is not None:
        team = "&teamId=" + str(teamid)
    url = "https://statsapi.mlb.com/api/v1/schedule?sportId=1" + team + "&date=" + date + hydrates
    print(url)
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    s = json.loads(urlopen(req).read().decode("utf-8"))
    return s

def get_pbp(gamepk):
    url = "https://statsapi.mlb.com/api/v1/game/" + gamepk + "/playByPlay"
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    s = json.loads(urlopen(req).read().decode("utf-8"))
    return s

def print_box(team,part, delta=None):
    s = get_day_schedule(delta=delta)
    games = s['dates'][0]['games']
    useabv = False
    for game in games:
        if team == game['teams']['away']['team']['abbreviation'].lower() or \
                team == game['teams']['home']['team']['abbreviation'].lower():
            useabv = True
    for game in games:
        awayname = game['teams']['away']['team']['name'].lower()
        homename = game['teams']['home']['team']['name'].lower()
        awayabv = game['teams']['away']['team']['abbreviation'].lower()
        homeabv = game['teams']['home']['team']['abbreviation'].lower()
        match = False
        if useabv:
            if team == awayabv or team == homeabv:
                match = True
        else:
            if team in awayname or team in homename:
                match = True
        if match:
            side = None
            if team == homeabv or team in homename:
                side = 'home'
            elif team == awayabv or team in awayname:
                side = 'away'
            if side is not None:
                gamepk = str(game['gamePk'])
                bs = BoxScore.BoxScore(get_boxscore(gamepk))
                out = bs.print_box(side=side, part=part)
                return out

def print_linescore(team, delta=None):
    s = get_day_schedule(delta=delta)
    games = s['dates'][0]['games']
    useabv = False
    for game in games:
        if team == game['teams']['away']['team']['abbreviation'].lower() or \
                team == game['teams']['home']['team']['abbreviation'].lower():
            useabv = True
    out = ""
    for game in games:
        awayname = game['teams']['away']['team']['name'].lower()
        homename = game['teams']['home']['team']['name'].lower()
        awayabv = game['teams']['away']['team']['abbreviation'].lower()
        homeabv = game['teams']['home']['team']['abbreviation'].lower()
        match = False
        if useabv:
            if team == awayabv or team == homeabv:
                match = True
        else:
            if team in awayname or team in homename:
                match = True
        if match:
            line0 = "   "
            line1 = awayabv.upper().ljust(3)
            line2 = homeabv.upper().ljust(3)
            inningslist = game['linescore']['innings']
            for inning in inningslist:
                if 'runs' in inning['away']:
                    ar = str(inning['away']['runs'])
                else:
                    ar = " "
                if 'runs' in inning['home']:
                    hr = str(inning['home']['runs'])
                else:
                    hr = " "
                lenstr = max(len(ar),len(hr))
                line0 = "%s %s" % (line0, str(inning['num']).rjust(lenstr))
                line1 = "%s %s" % (line1, ar.rjust(lenstr))
                line2 = "%s %s" % (line2, hr.rjust(lenstr))
            away = game['linescore']['teams']['away']
            home = game['linescore']['teams']['home']
            (ar, hr) = (str(away['runs']), str(home['runs']))
            (ah, hh) = (str(away['hits']), str(home['hits']))
            (ae, he) = (str(away['errors']), str(home['errors']))
            rlen = max(len(ar),len(hr))
            hlen = max(len(ah),len(hh))
            elen = max(len(ae),len(he))
            line0 = line0 + " | %s %s %s\n" % ('R'.rjust(rlen),'H'.rjust(hlen), 'E'.rjust(elen))
            line1 = line1 + " | %s %s %s\n" % (ar.rjust(rlen), ah.rjust(hlen), ae.rjust(elen))
            line2 = line2 + " | %s %s %s\n\n" % (hr.rjust(rlen), hh.rjust(hlen), he.rjust(elen))
            out = out + line0 + line1 + line2
    if out == "":
        out = "No matching games found"
    return out

def get_lg_standings(lgid, wc=False):
    now = datetime.now()
    type = "regularSeason"
    if wc:
        type = "wildCard"
    url = "https://statsapi.mlb.com/api/v1/standings/" + type + "?" \
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
        now = _get_date_from_delta(delta)
        import calendar
        output = "For %s, %d/%d/%d:\n\n" % (calendar.day_name[now.weekday()],now.month,now.day,now.year)
    useabv = False
    for game in games:
        if team == game['teams']['away']['team']['abbreviation'].lower() or \
            team == game['teams']['home']['team']['abbreviation'].lower():
            useabv = True
    for game in games:
        gamepk = str(game['gamePk'])
        awayabv = game['teams']['away']['team']['abbreviation'].lower()
        homeabv = game['teams']['home']['team']['abbreviation'].lower()
        awayname = game['teams']['away']['team']['name'].lower()
        homename = game['teams']['home']['team']['name'].lower()
        match = False
        if useabv:
            if team == awayabv or team == homeabv:
                match = True
        else:
            if team in awayname or team in homename:
                match = True
        if match:
            output = output + get_single_game_info(gamepk,game, show_on_deck=True) + "\n"
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
                    output = output + "Last Play: With " + pitch + " pitching, " + desc + "\n\n"
                    if 'pitchData' in lastplay['playEvents'][-1]:
                        data = lastplay['playEvents'][-1]
                        output = output + "Pitch: %s, %d mph\n" % (data['details']['type']['description'],
                                                                   data['pitchData']['startSpeed'])
                    if 'hitData' in lastplay['playEvents'][-1]:
                        data = lastplay['playEvents'][-1]['hitData']
                        output = output + "Statcast: %d ft, %d mph, %d degrees\n" % (data['totalDistance'],
                                                                       data['launchSpeed'],
                                                                       data['launchAngle'])
                except Exception as e:
                    print(e)
    return output

def list_scoring_plays(team,delta=None,lastonly=False):
    s = get_day_schedule(delta,scoringplays=True)
    team = team.lower()
    games = s['dates'][0]['games']
    plays = []
    for game in games:
        aname = game['teams']['away']['team']['name'].lower()
        hname = game['teams']['home']['team']['name'].lower()
        aabrv = game['teams']['away']['team']['abbreviation'].lower()
        habrv = game['teams']['home']['team']['abbreviation'].lower()
        if team in aname or team in hname or team in aabrv or team in habrv:
            for i in game['scoringPlays']:
                inning = i['about']['halfInning'].upper() + " " + str(i['about']['inning'])
                desc = "With " + i['matchup']['pitcher']['fullName'] + " pitching, " + i['result']['description']
                if 'awayScore' in i['result']:
                    desc = desc + "(%s-%s)" % (i['result']['awayScore'], i['result']['homeScore'])
                    if 'hitData' in i['playEvents'][-1]:
                        data = i['playEvents'][-1]['hitData']
                        desc = desc + "\n\tStatcast: %d ft, %d mph, %d degrees\n" % (data['totalDistance'],
                                                                                     data['launchSpeed'],
                                                                                     data['launchAngle'])
                plays.append((inning, desc))
    if lastonly:
        return [plays[-1]]
    return plays

def get_div_standings(div):
    wc = False
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
    elif div == "nlwc":
        id = 104
        idx=0
        wc = True
    elif div == "alwc":
        id = 103
        idx=0
        wc = True
    else:
        return

    standings = get_lg_standings(id,wc=wc)
    div = standings['records'][idx]
    output = "```python\n"
    output = output + "%s %s %s %s %s %s %s %s %s %s %s\n" %\
             (' '.rjust(3),'W'.rjust(3),'L'.rjust(3),'PCT'.rjust(5), 'GB'.rjust(4), ' WCGB', 'L10',
              'STK', 'RD'.rjust(3),'RS'.rjust(4),'RA'.rjust(4))
    for team in div['teamRecords']:
        abbrev = team['team']['abbreviation'].ljust(3)
        streak = team['streak']['streakCode'].ljust(3)
        wins = str(team['wins']).rjust(3)
        loss = str(team['losses']).rjust(3)
        pct = team['leagueRecord']['pct'].rjust(5)
        rd = str(team['runDifferential']).rjust(3)
        ra = str(team['runsAllowed']).rjust(4)
        rs = str(team['runsScored']).rjust(4)
        gb = team['gamesBack'].rjust(4)
        wcgb = team['wildCardGamesBack'].rjust(5)
        lastten = ""
        for split in team['records']['splitRecords']:
            if split['type'] == "lastTen":
                lastten = "%s-%s" % (split['wins'],split['losses'])
        output = output + "%s %s %s %s %s %s %s %s %s %s %s\n" %\
                 (abbrev, wins, loss, pct, gb, wcgb, lastten, streak, rd, rs, ra)
    output = output + "```"
    return output

def get_stat_leader(stat):
    statmap = {'avg':'battingAverage',
               'obp':'onBasePercentage',
               'slg':'sluggingPercentage',
               'ops':'onBasePlusSlugging',
               'rbi':'runsBattedIn',
               'r':'runs',
               'sb':'stolenBases',
               'cs':'caughtStealing',
               'h':'hits',
               '2b':'doubles',
               '3b':'triples',
               'bb':'walks',
               'so':'strikeouts',
               'hr':'homeRuns'
    }
    stat = stat.lower()
    if stat in statmap:
        cat = statmap[stat]
    else:
        return []

    url = "https://statsapi.mlb.com/api/v1/stats/leaders?leaderCategories=" + cat + "&hydrate=person,team&limit=10"
    # print(url)
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    s = json.loads(urlopen(req).read().decode("utf-8"))
    leaders = s['leagueLeaders'][0]['leaders']
    players = []
    for leader in leaders:
        players.append((leader['person']['lastFirstName'], leader['team']['abbreviation'],
                        leader['value']))
    return players

def _get_player_search(name, active='Y'):
    # find player id
    name = name.replace(' ', '+').upper()
    url = "http://lookup-service-prod.mlb.com/json/named.search_player_all.bam?sport_code=%27mlb%27&name_part=%27"+ \
          name+"%25%27&active_sw=%27" + active + "%27"
    print(url)
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    s = json.loads(urlopen(req).read().decode("latin1"))
    result = s['search_player_all']['queryResults']
    size = int(result['totalSize'])
    if size > 1:
        return result['row'][0]
    elif size == 1:
        return result['row']
    else:
        return None

def get_player_line(name, delta=None):
    player = _get_player_search(name)
    if player is None:
        return "No matching player found"
    teamid = int(player['team_id'])
    pid = player['player_id']
    disp_name = player['name_display_first_last']
    s = get_day_schedule(delta,teamid=teamid)
    try:
        game = s['dates'][0]['games'][0]
    except IndexError:
        return "Couldn't find a game for player %s" % (disp_name)
    gamepk = game['gamePk']
    if game['teams']['away']['team']['id'] == teamid:
        opp = game['teams']['home']['team']['abbreviation']
        side = 'away'
    else:
        opp = game['teams']['away']['team']['abbreviation']
        side = 'home'
    useDH = False
    if game['teams']['home']['team']['league']['id'] == 103:
        useDH = True
    box = get_boxscore(str(gamepk))
    try:
        stats = box['teams'][side]['players']['ID' + str(pid)]['stats']
    except KeyError:
        return "No stats found for player %s" % disp_name
    d = _get_date_from_delta(delta)
    output = "%s %d/%d vs %s:\n\n" % (disp_name, d.month, d.day, opp.upper())
    hasstats = False
    pitcher = False
    if 'inningsPitched' in stats['pitching']:
        hasstats = True
        pitcher = True
        s = stats['pitching']
        dec = ""
        if 'note' in s:
            dec = s['note']
        output = output + " IP  H  R ER HR BB SO  P-S\n"
        output = output + "%s %2d %2d %2d %2d %2d %2d %2d-%d %s\n\n" % (s['inningsPitched'],
                                                               s['hits'],
                                                               s['runs'],
                                                               s['earnedRuns'],
                                                               s['homeRuns'],
                                                               s['baseOnBalls'],
                                                               s['strikeOuts'],
                                                               s['pitchesThrown'],
                                                               s['strikes'],
                                                               dec)
    if 'atBats' in stats['batting'] and (not pitcher or (pitcher and not useDH)):
        hasstats=True
        s = stats['batting']
        output = output + "AB H 2B 3B HR R RBI BB SO SB CS\n"
        output = output + "%2d %d %2d %2d %2d %d %3d %2d %2d %2d %2d\n" % (
            s['atBats'],
            s['hits'],
            s['doubles'],
            s['triples'],
            s['homeRuns'],
            s['runs'],
            s['rbi'],
            s['baseOnBalls'],
            s['strikeOuts'],
            s['stolenBases'],
            s['caughtStealing'])
    if not hasstats:
        return "No stats for %s on %d/%d vs %s" % (disp_name, d.month, d.day, opp.upper())
    return output


def get_ohtani_line(delta=None):
    return get_player_line("shohei ohtani", delta=delta)

def get_player_season_stats(name, type=None, year=None, active='Y', career=False):
    player = _get_player_search(name, active=active)
    if player is None:
        return "No matching player found"
    if year == None and active == 'N':
        career = True
    teamid = int(player['team_id'])
    teamabv = player['team_abbrev']
    pid = int(player['player_id'])
    disp_name = player['name_display_first_last']
    pos = player['position']
    bats = player['bats']
    throws = player['throws']
    height = "%s'%s\"" % (player['height_feet'], player['height_inches'])
    weight = "%s lbs" % (player['weight'])
    infoline = "%s | B/T: %s/%s | %s | %s" % (pos, bats,throws, height, weight)
    # print(pos)
    if type is None and pos == 'P':
        type = "pitching"
    elif type is None and pos != 'P':
        type = "hitting"
    url = "http://lookup-service-prod.mlb.com/json/named.sport_" + type + "_composed.bam?game_type=%27R%27&league_list_id=%27mlb_hist%27&player_id=" + str(pid)
    print(url)
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    s = json.loads(urlopen(req).read().decode("utf-8"))
    sport = "sport_"
    if career:
        sport = "sport_career_"
    if s['sport_'+type+'_composed'][sport+type+"_agg"]["queryResults"]["totalSize"] == "0":
        return "No stats for %s" % disp_name
    seasonstats = s['sport_'+type+'_composed'][sport+type+"_agg"]["queryResults"]["row"]
    seasons = s['sport_'+type+'_composed']["sport_"+type+"_agg"]["queryResults"]["row"]
    sport_tm = s['sport_'+type+'_composed']['sport_'+type+"_tm"]['queryResults']['row']
    now = datetime.now()
    if year is None:
        year = str(now.year)
    s = None
    if not career:
        if "season" in seasonstats:
            if seasonstats["season"] == year:
                s = seasonstats
            if sport_tm['season'] == year:
                teamabv = sport_tm['team_abbrev']
            else:
                return "No stats for %s" % disp_name
        else:
            for season in seasonstats:
                if season["season"] == year:
                    s = season
            for r in sport_tm:
                if r['season'] == year:
                    teamabv = r['team_abbrev']
            if s is None:
                return "No stats for %s" % disp_name
        output = "%s season stats for %s (%s):" % (year, disp_name, teamabv)
    else:
        if "season" in seasons:
            years = seasons["season"]
        else:
            years = "%s-%s" % (seasons[0]["season"], seasons[-1]["season"])
        s = seasonstats
        output = "Career stats for %s (%s):" % (disp_name,years)
    output = "%s\n\t%s\n\n" % (output, infoline)

    if type == "hitting":
        stats = ['ab','h','d','t','hr','r','rbi','bb','so','sb','cs','avg','obp','slg']
    elif type == "pitching":
        stats = ['w','l','g','sv','ip','so','bb','hr','era','whip']
    output = output + _print_labeled_list(stats,s)
    return output
            # print(season)
    # roster = get_team_info(teamid)['roster']
    # for person in roster:
    #     p = person['person']
    #     if p['id'] == pid:
    #         output = "Season stats for %s (%s):\n\n" % (disp_name, teamabv)
    #         s = p['stats'][0]['splits'][0]['stat']
    #         if p['stats'][0]['group']['displayName'] == 'hitting':
    #             output = output + " AB   H 2B 3B HR   R RBI  BB  SO SB CS  AVG  OBP  SLG\n"
    #             output = output + "%3d %3d %2d %2d %2d %3d %3d %3d %3d %2d %2d %s %s %s" % (s['atBats'],
    #                                                                                         s['hits'],
    #                                                                                         s['doubles'],
    #                                                                                         s['triples'],
    #                                                                                         s['homeRuns'],
    #                                                                                         s['runs'],
    #                                                                                         s['rbi'],
    #                                                                                         s['baseOnBalls'],
    #                                                                                         s['strikeOuts'],
    #                                                                                         s['stolenBases'],
    #                                                                                         s['caughtStealing'],
    #                                                                                         s['avg'],
    #                                                                                         s['obp'],
    #                                                                                         s['slg']
    #                                                                                         )
    #         elif p['stats'][0]['group']['displayName'] == 'pitching':
    #             output = output + " W  L  G SV    IP  SO  BB HR  ERA WHIP\n"
    #             output = output + "%2d %2d %2d %2d %s %3d %3d %2d %s %s" % (s['wins'],
    #                                                                         s['losses'],
    #                                                                         s['gamesPitched'],
    #                                                                         s['saves'],
    #                                                                         s['inningsPitched'].rjust(5),
    #                                                                         s['strikeOuts'],
    #                                                                         s['baseOnBalls'],
    #                                                                         s['homeRuns'],
    #                                                                         s['era'],
    #                                                                         s['whip']
    #                                                                         )
    #         return output

def _print_labeled_list(labels, dict):
    repl_map = {'d':'2B','t':'3B'}
    line1 = ""
    line2 = ""
    for label in labels:
        r = str(dict[label])
        if label in repl_map:
            label = repl_map[label]
        l = max(len(r), len(label))
        line1 = "%s %s" % (line1, label.rjust(l).upper())
        line2 = "%s %s" % (line2, r.rjust(l))
    return "%s\n%s" % (line1, line2)

if __name__ == "__main__":
    #make_mlb_schedule()
    #get_mlb_teams()
    # print(get_single_game("chc"))
    # print(print_linescore("chc"))
    # print(get_single_game("wsh"))
    # print(get_single_game("nationals",delta="+1"))
    # print(get_all_game_info(delta='-1'))
    # print(get_all_game_info(liveonly=True))
    # print(get_all_game_info())
    #get_ET_from_timestamp("2018-03-31T20:05:00Z")
    # get_div_standings("nle")
    #bs = BoxScore.BoxScore(get_boxscore('529456'))
    #bs.print_box()
    # print(get_stat_leader('sb'))
    # print(list_scoring_plays('chc'))
    # print(get_ohtani_stats())
    print(get_player_season_stats("adam eaton", career=True))
    # print(get_player_season_stats("adam eaton", year="2017"))
    # print(get_player_season_stats("shohei ohtani", career=True))
    # print(get_player_season_stats("shohei ohtani", type="pitching"))
    # print(get_player_season_stats("jose guillen"))
    # print(get_player_line("cole"))
    # print(get_player_line("ryan zimmerman", delta="-4382"))
    # print(print_box('nationals','batting',delta="-1"))
