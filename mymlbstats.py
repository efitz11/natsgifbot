from urllib.request import urlopen, Request
from datetime import datetime, timedelta
import time
import json, os
import mlb.BoxScore as BoxScore
import mlb.getrecaps as recap

def _get_json(url,encoding="utf-8"):
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    return json.loads(urlopen(req).read().decode(encoding))

def _get_date_from_delta(delta=None):
    now = datetime.now() - timedelta(hours=5)
    if delta is not None and (isinstance(delta,int) or (delta.startswith('+') or delta.startswith('-'))):
        delta = int(delta)
        now = now + timedelta(days=delta)
    return now

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
    abbrevmap = {}
    for s in teams:
        teammap[s['name']] = s['id']
        abbrevmap[s['abbreviation'].lower()] = s['id']
    return (abbrevmap, teammap)

def get_teamid(search):
    abvs,names = get_mlb_teams()
    if search in abvs:
        return abvs[search]
    for name in names:
        if search.lower() in name.lower():
            return names[name]

def get_single_game_info(gamepk, gamejson, show_on_deck=False, liveonly=False):
    game = gamejson
    output = ""
    abstractstatus = game['status']['abstractGameState']
    detailstatus = game['status']['detailedState']
    awayabv = game['teams']['away']['team']['abbreviation'].ljust(3)
    homeabv = game['teams']['home']['team']['abbreviation'].ljust(3)
    # print(gamepk)
    pregame_statuses = ['Warmup']
    if abstractstatus == "Live" and detailstatus not in pregame_statuses:
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
            for stats in ls['defense']['pitcher']['stats']:
                if stats['type']['displayName'] == 'gameLog' and stats['group']['displayName'] == 'pitching':
                    # ps = '(%dP %dS)' % (stats['stats']['pitchesThrown'], stats['stats']['strikes'])
                    ps = '(%d P)' % (stats['stats']['pitchesThrown'])
                    pitcher = "%s %s" % (pitcher, ps)
        except:
            pitcher = ""
        outjust = 3
        if ls['currentInning'] > 9:
            outjust = 4
        count = "(%s-%s)" % (balls, strikes)
        output = "%s %s %2d %d | %s %s | %s | %s\n" % (awayabv, str(awayruns).rjust(2), awayhits, awayerrs, inninghalf, inning,
                                                     bases.center(5), "P: " + pitcher)
        if detailstatus != 'Delayed':
            output = output + "%s %s %2d %d |  %s %s  | %s | %s %s\n" % (homeabv, str(homeruns).rjust(2), homehits, homeerrs,
                                                                     outs, "out".ljust(outjust), count, "B: " + batter, ondeck)
        else:
            outs = detailstatus
            output = output + "%s %s %2d %d | %s | %s | %s %s\n" % (homeabv, str(homeruns).rjust(2), homehits, homeerrs,
                                                                         outs, count, "B: " + batter, ondeck)

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
    elif abstractstatus == "Preview" or detailstatus in pregame_statuses:
        awaywins = game['teams']['away']['leagueRecord']['wins']
        awayloss = game['teams']['away']['leagueRecord']['losses']
        homewins = game['teams']['home']['leagueRecord']['wins']
        homeloss = game['teams']['home']['leagueRecord']['losses']
        probaway = "TBD"
        aprecord = ""
        probhome = "TBD"
        hprecord = ""
        if 'probablePitcher' in game['teams']['away']:
            probaway = game['teams']['away']['probablePitcher']['lastName']
            if 'stats' in game['teams']['away']['probablePitcher']:
                for statgroup in game['teams']['away']['probablePitcher']['stats']:
                    if statgroup['type']['displayName'] == "statsSingleSeason" and \
                            statgroup['group']['displayName'] == "pitching":
                        wins = statgroup['stats']['wins']
                        losses = statgroup['stats']['losses']
                        era = statgroup['stats']['era']
                        aprecord = "(%d-%d) %s" % (wins,losses,era)
                        break
        if 'probablePitcher' in game['teams']['home']:
            probhome = game['teams']['home']['probablePitcher']['lastName']
            if 'stats' in game['teams']['away']['probablePitcher']:
                for statgroup in game['teams']['home']['probablePitcher']['stats']:
                    if statgroup['type']['displayName'] == "statsSingleSeason" and \
                            statgroup['group']['displayName'] == "pitching":
                        wins = statgroup['stats']['wins']
                        losses = statgroup['stats']['losses']
                        era = statgroup['stats']['era']
                        hprecord = "(%d-%d) %s" % (wins,losses,era)
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
                wprec,wpw,wpl= "","",""
                lprec,lpw,lpl = "","",""
                for stat in decisions['winner']['stats']:
                    if 'gameLog' == stat['type']['displayName'] and \
                        'pitching' == stat['group']['displayName'] and \
                        'note' in stat['stats']:
                        wprec = stat['stats']['note']
                    if 'statsSingleSeason' == stat['type']['displayName'] and \
                        'pitching' == stat['group']['displayName']:
                        if 'wins' in stat['stats']:
                            wpw = stat['stats']['wins']
                            wpl = stat['stats']['losses']
                for stat in decisions['loser']['stats']:
                    if 'gameLog' == stat['type']['displayName'] and \
                            'pitching' == stat['group']['displayName'] and \
                            'note' in stat['stats']:
                        lprec = stat['stats']['note']
                    if 'statsSingleSeason' == stat['type']['displayName'] and \
                            'pitching' == stat['group']['displayName']:
                        if 'wins' in stat['stats']:
                            lpw = stat['stats']['wins']
                            lpl = stat['stats']['losses']
                if wprec == "":
                    wprec = "(W, %s-%s)" % (wpw, wpl)
                if lprec == "":
                    lprec = "(L, %s-%s)" % (lpw, lpl)
                save = ""
                rec,sv = "",""
                if 'save' in decisions:
                    for stat in decisions['save']['stats']:
                        if 'gameLog' == stat['type']['displayName'] and \
                                'pitching' == stat['group']['displayName'] and \
                                'note' in stat['stats']:
                            rec = stat['stats']['note']
                        if 'statsSingleSeason' == stat['type']['displayName'] and \
                            'pitching' == stat['group']['displayName']:
                            if 'saves' in stat['stats']:
                                sv = stat['stats']['saves']
                    save = "%s" % (decisions['save']['lastName'])
                    if rec == "":
                        rec = "(S, %s)" % sv
                # output = output + "\n"
                wpdisp = "%s %s" % (wp, wprec)
                inning = ls['currentInning']
                res = 'F '
                if inning > 9:
                    inn = str(inning)
                else:
                    inn = "  "

                line1 = line1 + " | %s | %s %s %s" % (res, wpdisp.ljust(20), save, rec)
                line2 = line2 + " | %s | %s %s" % (inn, lp, lprec)
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
    print(url)
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
    print(url)
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    s = json.loads(urlopen(req).read().decode("utf-8"))
    return s

def get_team_dl(team):
    teamid = get_teamid(team)
    # url = "http://statsapi.mlb.com/api/v1/teams/%d/roster/40Man/?hydrate=person(stats(splits=statsSingleSeason))" % teamid
    url = "https://statsapi.mlb.com/api/v1/teams/%d/roster/depthChart/?hydrate=person" % teamid
    print(url)
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    roster = json.loads(urlopen(req).read().decode("utf-8"))['roster']
    output = ""
    map = {}
    for player in roster:
        if player['status']['code'].startswith('D'):
            desc = player['status']['description']
            if desc not in map:
                map[desc] = []
            note = player['note']
            playerid = player['person']['id']
            for p in map[desc]:
                if p['person']['id'] == playerid:
                    if p['note'] == "":
                        p['note'] = note
                    break
            else:  # won't execute if loop was broken
                map[desc].append(player)
            # map[desc].append("%s - %s" % (player['person']['fullName'], player['note']))
    for key in map:
        output = output + key + ":\n"
        for player in map[key]:
            output = output + "  %s" % player['person']['fullName'].ljust(20)
            if player['note'] != "":
                output = output + "%s" % player['note']
            output = output + "\n"
            # output = output + "  %s\n" % player
        output = output + "\n"
    return output

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
    teamid = get_teamid(team)
    s = get_day_schedule(delta=delta, teamid=teamid)
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
                dp = False
                if delta is None:
                    dp = True
                out = bs.print_box(side=side, part=part, display_pitches=dp)
                return out

def print_linescore(team, delta=None):
    teamid = get_teamid(team)
    s = get_day_schedule(delta=delta, teamid=teamid)
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
            try:
                inningslist = game['linescore']['innings']
            except:
                continue

            for inning in inningslist:
                if 'runs' in inning['away']:
                    ar = str(inning['away']['runs'])
                else:
                    ar = " "
                if 'runs' in inning['home']:
                    hr = str(inning['home']['runs'])
                else:
                    hr = " "
                inn = inning['num']
                if inn > 9:
                    inn -= 10
                inn = str(inn)
                lenstr = max(len(ar),len(hr),len(inn))
                line0 = "%s %s" % (line0, inn.rjust(lenstr))
                line1 = "%s %s" % (line1, ar.rjust(lenstr))
                line2 = "%s %s" % (line2, hr.rjust(lenstr))
            away = game['linescore']['teams']['away']
            home = game['linescore']['teams']['home']
            if 'runs' in away:
                (ar, hr) = (str(away['runs']), str(home['runs']))
                (ah, hh) = (str(away['hits']), str(home['hits']))
                (ae, he) = (str(away['errors']), str(home['errors']))
            else:
                continue
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

def get_lg_standings(lgid, wc=False, year=None):
    now = datetime.now()
    y = now.year
    if year is not None:
        y = year
    type = "regularSeason"
    if wc:
        type = "wildCard"
    url = "https://statsapi.mlb.com/api/v1/standings/" + type + "?" \
          "leagueId=" + str(lgid) + "&season=" + str(y) + "&hydrate=team"
    print(url)
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    s = json.loads(urlopen(req).read().decode("utf-8"))
    return s

def get_single_game(team,delta=None,print_statcast=True):
    """delta is + or - a number of days"""
    teamid = get_teamid(team)
    s = get_day_schedule(delta, teamid=teamid)
    if s['totalGames'] == 0:
        return "No games found."
    games = s['dates'][0]['games']
    output = ""
    if delta is not None:
        now = _get_date_from_delta(delta)
        import calendar
        output = "For %s, %d/%d/%d:\n\n" % (calendar.day_name[now.weekday()],now.month,now.day,now.year)
    checkdivs = False
    divs = {'nle':204,'nlc':205,'nlw':203,'ale':201,'alc':202,'alw':200}
    if team in divs:
        checkdivs = True
        divid = divs[team]
        print_statcast = False
    else:
        teamid = get_teamid(team)
    team = team.lower()
    for game in games:
        gamepk = str(game['gamePk'])
        match = False
        if checkdivs:
            awaydiv = game['teams']['away']['team']['division']['id']
            homediv = game['teams']['home']['team']['division']['id']
            if divid == awaydiv or divid == homediv:
                match = True
        else:
            if teamid is not None:
                awayid = game['teams']['away']['team']['id']
                homeid = game['teams']['home']['team']['id']
                if teamid == awayid or teamid == homeid:
                    match = True
            else:
                awayname = game['teams']['away']['team']['name'].lower()
                homename = game['teams']['home']['team']['name'].lower()
                if team in awayname or team in homename:
                    match = True
        if match:
            output = output + get_single_game_info(gamepk,game, show_on_deck=True) + "\n"
            abstractstatus = game['status']['abstractGameState']
            if abstractstatus == "Live" and print_statcast:
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
                        output = output + "Statcast: %d ft, %d mph, %d degrees\n\n" % (data['totalDistance'],
                                                                       data['launchSpeed'],
                                                                       data['launchAngle'])
                except Exception as e:
                    # print("Error in parsing game %d" % gamepk)
                    print(e)
    return output

def get_team_schedule(team, num, backward=True):
    teamid = get_teamid(team)
    if teamid is None:
        return "No matching team found."
    print(teamid)
    if backward:
        num = -num
    then = _get_date_from_delta(num)
    now = _get_date_from_delta(0)
    if backward:
        startdate = str(then.year) + "-" + str(then.month).zfill(2) + "-" + str(then.day).zfill(2)
        enddate = str(now.year) + "-" + str(now.month).zfill(2) + "-" + str(now.day).zfill(2)
    else:
        enddate = str(then.year) + "-" + str(then.month).zfill(2) + "-" + str(then.day).zfill(2)
        startdate = str(now.year) + "-" + str(now.month).zfill(2) + "-" + str(now.day).zfill(2)
    url = "https://statsapi.mlb.com/api/v1/schedule?lang=en&sportId=1&hydrate=team(venue(timezone)),venue(timezone)," \
          "game(seriesStatus,seriesSummary,tickets,promotions,sponsorships,content(summary,media(epg))),seriesStatus," \
          "seriesSummary,tickets,radioBroadcasts,broadcasts(all),probablePitcher,decisions,person,stats,flags,linescore(matchup,runners)&" \
          "season=" + str(now.year) + "&startDate="+str(startdate)+"&endDate=" + str(enddate) + "&teamId=" + str(teamid) + "&" \
          "eventTypes=primary&scheduleTypes=games,events,xref"
    print(url)
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    s = json.loads(urlopen(req).read().decode("utf-8"))
    dates = s['dates']
    output = ""
    for date in dates:
        for game in date['games']:
            output = output + date['date'] + ":\n"
            output = output + get_single_game_info(None, game) + "\n"
    return output

def list_scoring_plays(team,delta=None,lastonly=False):
    teamid = get_teamid(team)
    if teamid is None:
        return []
    s = get_day_schedule(delta, teamid=teamid, scoringplays=True)
    games = s['dates'][0]['games']
    plays = []
    for game in games:
        if game['teams']['away']['team']['id'] == teamid:
            part = 'top'
        else:
            part = 'bottom'
        for i in game['scoringPlays']:
            if i['about']['halfInning'] == part:
                inning = i['about']['halfInning'].upper() + " " + str(i['about']['inning'])
                playevents = i['playEvents']
                if i['about']['isScoringPlay']:
                    desc = "With " + i['matchup']['pitcher']['fullName'] + " pitching, " + i['result']['description']
                    if 'awayScore' in i['result']:
                        desc = desc + "(%s-%s)" % (i['result']['awayScore'], i['result']['homeScore'])
                    playevent = playevents[-1]
                    if 'hitData' in playevent:
                        data = playevent['hitData']
                        desc = desc + "\n\tStatcast: %d ft, %d mph, %d degrees\n" % (data['totalDistance'],
                                                                                     data['launchSpeed'],
                                                                                     data['launchAngle'])
                    plays.append((inning, desc))
                else:
                    for j in playevents:
                        if 'isScoringPlay' in j['details']:
                            if j['details']['isScoringPlay']:
                                desc = "With " + i['matchup']['pitcher']['fullName'] + " pitching, " + j['details']['description']
                                if 'awayScore' in j['details']:
                                    desc = desc + "(%s-%s)" % (j['details']['awayScore'], j['details']['homeScore'])
                                if 'hitData' in j:
                                    data = j['hitData']
                                    desc = desc + "\n\tStatcast: %d ft, %d mph, %d degrees\n" % (data['totalDistance'],
                                                                                                 data['launchSpeed'],
                                                                                                 data['launchAngle'])
                            plays.append((inning, desc))
    if lastonly:
        return [plays[-1]]
    return plays

def get_div_standings(div, year=None):
    wc = False
    div = div.lower()
    idx = []
    if div in ['ale','alc','alw','al','alwc']:
        id = 103
        if div == "ale":
            idx.append(1)
        elif div == "alc":
            idx.append(2)
        elif div == "alw":
            idx.append(0)
        elif div == "al":
            idx.extend([1,2,0])
        elif div == "alwc":
            idx.append(0)
            wc = True
    elif div in ['nle','nlc','nlw','nl','nlwc']:
        id = 104
        if div == "nle":
            idx.append(2)
        elif div == "nlc":
            idx.append(0)
        elif div == "nlw":
            idx.append(1)
        elif div == "nl":
            idx.extend([2,0,1])
        elif div == "nlwc":
            idx.append(0)
            wc = True
    else:
        return

    standings = get_lg_standings(id,wc=wc, year=year)
    output = ""
    for i in idx:
        output = output + "```python\n"
        div = standings['records'][i]
        teams = []
        for team in div['teamRecords']:
            l = dict()
            l['abv'] = team['team']['abbreviation']
            l['w'] = str(team['wins'])
            l['l'] = str(team['losses'])
            l['pct'] = team['leagueRecord']['pct']
            l['gb'] = team['gamesBack']
            l['wcgb'] = team['wildCardGamesBack']
            for split in team['records']['splitRecords']:
                if split['type'] == "lastTen":
                    l['l10'] = "%s-%s" % (split['wins'],split['losses'])
            l['stk'] = team['streak']['streakCode']
            l['rd'] = str(team['runDifferential'])
            l['rs'] = str(team['runsScored'])
            l['ra'] = str(team['runsAllowed'])
            l['e'] = str(team['eliminationNumber'])
            try:
                l['wce'] = str(team['wildCardEliminationNumber'])
            except KeyError:
                l['wce'] = "-"
            teams.append(l)

        repl_map = {'abv':''}
        labs = ['abv','w','l','pct','gb','wcgb','l10','stk','rd','e','wce']
        output = output + _print_table(labs,teams,repl_map=repl_map)
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
        for p in result['row']:
            if p['team_id'] == '120':
                return p
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
    output = ""
    for game in s['dates'][0]['games']:
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
            output = output + "No stats found for player %s" % disp_name
            continue
        d = _get_date_from_delta(delta)
        output = output + "%s %d/%d vs %s:\n\n" % (disp_name, d.month, d.day, opp.upper())
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
            print(output)
        if not hasstats:
            output = output + "No stats for %s on %d/%d vs %s\n" % (disp_name, d.month, d.day, opp.upper())
    return output

def get_ohtani_line(delta=None):
    return get_player_line("shohei ohtani", delta=delta)

def get_player_gamelogs(name, num=5, forcebatting=False):
    # cap at 15
    if num > 15:
        num = 15
    player = _get_player_search(name)
    if player is None:
        return "No matching player found"
    pitching = player['position'] == 'P'
    if forcebatting:
        pitching = False
    url = "http://lookup-service-prod.mlb.com/json/named.sport_hitting_game_log_composed.bam?game_type=%27R%27&league_list_id=%27mlb_hist%27\
            &player_id="+ player['player_id'] +"&season=2018&sit_code=%271%27&sit_code=%272%27&sit_code=%273%27&sit_code=%274%27&sit_code=%275%27&sit_code=%276%27&sit_code=%277%27&sit_code=%278%27&sit_code=%279%27&sit_code=%2710%27&sit_code=%2711%27&sit_code=%2712%27"
    type = "hitting"
    if pitching:
        url = "http://lookup-service-prod.mlb.com/json/named.sport_pitching_game_log_composed.bam?game_type=%27R%27&league_list_id=%27mlb_hist%27" \
              "&player_id=" + player['player_id'] + "&season=2018&sit_code=%271%27&sit_code=%272%27&sit_code=%273%27&sit_code=%274%27&sit_code=%275%27&sit_code=%276%27&sit_code=%277%27&sit_code=%278%27&sit_code=%279%27&sit_code=%2710%27&sit_code=%2711%27&sit_code=%2712%27"
        type = "pitching"
    print(url)
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    s = json.loads(urlopen(req).read().decode("utf-8"))
    gamelog = s['sport_%s_game_log_composed' % type]['sport_%s_game_log' % type]['queryResults']
    totalsize = int(gamelog['totalSize'])
    if totalsize == 0:
        return "No games played"
    games = []
    if totalsize == 1:
        games.append(gamelog['row'])
        num = 1
    else:
        gamelog = gamelog['row']
        if num > len(gamelog):
            num = len(gamelog)
        for i in range(num):
            game = gamelog[-i-1]
            games.append(game)
    output = "Game Log for %s's last %d games:\n\n" % (player['name_display_first_last'], num)
    if not pitching:
        stats = ['game_day','opponent_abbrev','ab','h','d','t','hr','r','rbi','bb','so','sb','cs','avg','obp','slg','ops']
    else:
        stats = ['game_day','opponent_abbrev','w','l','svo','sv','ip','h','r','er','so','bb','hr','era','whip']
    repl_map = {'game_day':'day','opponent_abbrev':'opp', 'd':'2B', 't':'3B'}
    # output = output + _print_labeled_list(stats,game,header=(i==0),repl_map=repl_map) + "\n"
    output = output + _print_table(stats,games,repl_map=repl_map) + "\n"
    return output

def _get_player_info_line(player):
    try:
        pos = player['position']
    except KeyError:
        if player['primary_position'] == 'O':
            pos = 'OF'
        else:
            posits = ['P','C','1B','2B','3B','SS','LF','CF','RF']
            pos = posits[int(player['primary_position'])-1]
    bats = player['bats']
    throws = player['throws']
    height = "%s'%s\"" % (player['height_feet'], player['height_inches'])
    weight = "%s lbs" % (player['weight'])
    return "%s | B/T: %s/%s | %s | %s" % (pos, bats,throws, height, weight)

def batter_or_pitcher_vs(name, team, year=None):
    player = _get_player_search(name)
    if player is None:
        return "No matching player found"
    if player['position'] == 'P':
        return pitcher_vs_team(name,team, player=player)
    else:
        return player_vs_team(name,team, year=year)

def pitcher_vs_team(name, team, player=None):
    teamid = get_teamid(team)
    if player is None:
        player = _get_player_search(name)
    if player is None:
        return "No matching player found"
    now = datetime.now()
    year = str(now.year)
    url = "https://lookup-service-prod.mlb.com/json/named.team_bvp_5y.bam?" \
          "vs_pitcher_id=" + player['player_id'] + "&game_type=%27R%27" \
                                                   "&team_id=" + str(teamid) + "&year=" + year
    print(url)
    res = _get_json(url,encoding="ISO-8859-1")["team_bvp_5y"]["queryResults"]
    batters = []
    empties = []
    if int(res['totalSize']) == 0:
        return "No stats available in the last 5 years."
    elif int(res['totalSize']) == 1:
        batters.append(res['row'])
    else:
        for row in res['row']:
            if row['b_ab'] == '':
                empties.append(row)
            else:
                batters.append(row)
    output = "%s's stats vs batters, last 5 years:\n\n" % (player['name_display_first_last'])
    stats = ['name','b_ab','b_total_hits','b_double','b_triple','b_home_run','b_walk','b_strikeout',
             'b_batting_avg','b_on_base_avg','b_slugging_avg','b_on_base_slg_avg']
    repl_map = {'b_ab':'ab','b_total_hits':'h','b_double':'2b','b_triple':'3b','b_home_run':'hr','b_walk':'bb','b_strikeout':'so',
             'b_batting_avg':'avg','b_on_base_avg':'obp','b_slugging_avg':'slg','b_on_base_slg_avg':'ops'}
    output = output + _print_table(stats,batters,repl_map=repl_map) + "\n\n"
    if len(empties) > 0:
        emplist = "No stats for "
        for e in empties:
            emplist = emplist + e['name'] + "; "
        output = output + emplist[:-2]

    return output

def player_vs_team(name, team, year=None):
    teamid = get_teamid(team)
    player = _get_player_search(name)
    if player is None:
        return "No matching player found"
    if year is None:
        now = datetime.now()
        year = str(now.year)
    url = "http://lookup-service-prod.mlb.com/json/named.stats_batter_vs_pitcher_composed.bam?" \
          "league_list_id=%27mlb_hist%27&game_type=%27R%27&player_id=" + player['player_id'] \
          + "&opp_team_id=" + str(teamid) + "&season=" + year
    pitching = False
    if player['position'] == 'P':
        pitching = True
        url = "http://lookup-service-prod.mlb.com/json/named.stats_batter_vs_pitcher_composed.bam?" \
              "league_list_id=%27mlb_hist%27&game_type=%27R%27&pitcher_id=" + player['player_id'] \
              + "&team_id=" + str(teamid) + "&season=" + year
    print(url)
    json = _get_json(url,encoding="ISO-8859-1")["stats_batter_vs_pitcher_composed"]
    totals = json["stats_batter_vs_pitcher_total"]["queryResults"]["row"]
    json = json["stats_batter_vs_pitcher"]["queryResults"]
    pitchers = []
    if int(json['totalSize']) == 1:
        pitchers.append(json['row'])
    elif int(json['totalSize']) == 1:
        return "No stats for %s." % (player['name_display_first_last'])
    else:
        for row in json['row']:
            pitchers.append(row)
    if not pitching:
        output = "%s's stats vs %s pitchers (%s):\n\n" % (player['name_display_first_last'], pitchers[0]['opponent'], pitchers[0]['season'])
        stats = ['pitcher_first_last_html','ab','h','d','t','hr','bb','so','avg','obp','slg','ops']
    else:
        output = "%s's stats vs %s batters (%s):\n\n" % (player['name_display_first_last'], pitchers[0]['team'], pitchers[0]['season'])
        stats = ['player_first_last_html','ab','h','d','t','hr','bb','so','avg','obp','slg','ops']
    repl_map = {'d':'2B', 't':'3B', 'pitcher_first_last_html':'pitcher', 'player_first_last_html':'batter'}
    output = output + _print_table(stats,pitchers,repl_map=repl_map) + "\n\n"
    if pitching:
        stats = ['team','ab','h','d','t','hr','bb','so','avg','obp','slg','ops']
    else:
        stats = ['opponent','ab','h','d','t','hr','bb','so','avg','obp','slg','ops']
    output = output + _print_labeled_list(stats,totals)
    return output

def get_player_season_splits(name, split, type=None, year=None, active='Y'):
    split = split.lower()
    splitsmap = {'vsl':'vl','vsr':'vr','home':'h','away':'a','grass':'g','turf':'t','day':'d','night':'n',
                 'march':'3','april':'4','may':'5','june':'6','july':'7','august':'8','september':'9','october':'10',
                 'late':'lc','ahead':'ac','behind':'bc','noouts':'o0','oneout':'o1','twoouts':'o2',
                 'b1':'b1','b2':'b2','b3':'b3','b4':'b4','b5':'b5','b6':'b6','b7':'b7','b8':'b8','b9':'b9',
                 'empty':'r0','loaded':'r123','risp':'risp','half1':'preas','half2':'posas'}
    if split in ['list','all','help']:
        output = ""
        for key in splitsmap:
            output = "%s %s," % (output, key)
        return output[:-1]
    if split not in splitsmap:
        return "split not found"
    player = _get_player_search(name, active=active)
    if player is None:
        return "No matching player found"
    if year == None and active == 'N':
        career = True
    if year is None:
        now = datetime.now()
        year = str(now.year)
    pos = player['position']
    type="hitting"
    if pos == 'P':
        type="pitching"
    url = "http://lookup-service-prod.mlb.com/json/named.sport_" + type + "_sits_composed.bam?league_list_id=%27mlb_hist%27&game_type=%27R%27" \
          "&season=" + year + "&player_id=" + player['player_id'] + "&sit_code=%27" + splitsmap[split] + "%27"
    print(url)
    json = _get_json(url)
    results = json['sport_'+type+'_sits_composed']['sport_'+type+'_sits_total']['queryResults']['row']
    output = "%s's %s splits (%s):\n\n" % (player['name_display_first_last'], results['situation'], results['season'])
    if type == "hitting":
        stats = ['ab','h','d','t','hr','r','rbi','bb','so','sb','cs','avg','obp','slg','ops']
    else:
        stats = ['w','l','g','svo','sv','ip','h','r','so','bb','hr','era','whip']
    output = output + _print_labeled_list(stats,results)
    return output

def get_player_trailing_splits(name, days, forcebatting=False):
    player = _get_player_search(name)
    if player is None:
        return "No matching player found"
    pitching = player['position'] == 'P'
    if forcebatting:
        pitching = False
    url = "http://mlb.mlb.com/pubajax/wf/flow/stats.splayer?season=2018&sort_order=%27desc%27&sort_column=%27avg%27&stat_type=hitting&page_type=SortablePlayer" \
          "&team_id=" + player['team_id'] + "&game_type=%27R%27&last_x_days="+str(days)+"&player_pool=ALL&season_type=ANY&sport_code=%27mlb%27&results=1000&recSP=1&recPP=50"
    if pitching:
        url = "http://mlb.mlb.com/pubajax/wf/flow/stats.splayer?season=2018&sort_order=%27asc%27&sort_column=%27era%27&stat_type=pitching&page_type=SortablePlayer" \
          "&team_id=" + player['team_id'] + "&game_type=%27R%27&last_x_days="+str(days)+"&player_pool=ALL&season_type=ANY&sport_code=%27mlb%27&results=1000&position=%271%27&recSP=1&recPP=50"
    print(url)
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    s = json.loads(urlopen(req).read().decode("utf-8"))
    s = s['stats_sortable_player']['queryResults']
    if int(s['totalSize']) == 0:
        return "No matching team found for player " + player['name_display_first_last']
    for p in s['row']:
        if p['player_id'] == player['player_id']:
            output = "Last %d days for %s (%s):\n\n" % (days, player['name_display_first_last'], player['team_abbrev'])
            if not pitching:
                stats = ['g','ab','h','d','t','hr','r','rbi','bb','so','sb','cs','avg','obp','slg','ops']
            else:
                stats = ['w','l','g','svo','sv','ip','so','bb','hr','era','whip']
            repl_map = {'d':'2B','t':'3B'}
            output = output + _print_labeled_list(stats,p,repl_map=repl_map)
            return output
    else:
        return "%s not found on team %s" % (player['name_display_first_last'],player['team_abbrev'])

def milb_player_search(name,parent=None):
    name = name.replace(' ','%25')
    url = "http://lookup-service-prod.bamgrid.com/lookup/json/named.milb_player_search.bam?active_sw=%27Y%27&name_part=%27"+ name +"%25%27"
    print(url)
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    s = json.loads(urlopen(req).read().decode("utf-8"))['milb_player_search']['queryResults']
    if int(s['totalSize']) == 0:
        return None
    elif int(s['totalSize']) == 1:
        return s['row']
    else:
        if parent is not None:
            for player in s['row']:
                if parent.lower() in player['parent_team'].lower():
                    return player
        else:
            for player in s['row']:
                if player['parent_team'].lower() == 'nationals':
                    return player
        return s['row'][0]

def get_milb_season_stats(name, type="hitting",year=None):
    if 'parent=' in name:
        parentteam = name[name.find('=')+1:]
        print(parentteam)
        name = name[:name.find('parent=')]
        player = milb_player_search(name,parentteam)
    else:
        player = milb_player_search(name)
    if player is None:
        return "No player found"
    name = player['name_first_last']
    teamabv = player['team_name_abbrev']
    level = player['level']
    parent = player['parent_team']
    id = player['player_id']
    try:
        pos = int(player['primary_position'])
        if pos == 1:
            type = "pitching"
    except:
        print("%s is an OF" % name)
    url = "http://lookup-service-prod.bamgrid.com/lookup/json/named.sport_"+type+"_composed.bam?" \
          "game_type=%27R%27&league_list_id=%27mlb_milb%27&sort_by=%27season_asc%27&player_id="+ id
    print(url)
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    s = json.loads(urlopen(req).read().decode("utf-8"))['sport_'+type+'_composed']['sport_'+type+'_tm']['queryResults']
    leagues = []
    now = datetime.now()
    season = str(now.year)
    if year is not None:
        season = year
    if s['totalSize'] == "1":
        leagues.append(s['row'])
    else:
        for i in s['row']:
            if i['season'] == str(season) and i['sport'] != "MLB":
                leagues.append(i)
    output = "%s Season stats for %s (%s-%s, %s):\n" % (season, name, teamabv, level, parent)
    teamid = player['team_id']
    url = "http://lookup-service-prod.bamgrid.com/lookup/json/named.roster_all.bam?team_id=" + teamid
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    t = json.loads(urlopen(req).read().decode("utf-8"))['roster_all']['queryResults']['row']
    for player2 in t:
        if player2['player_id'] == id:
            output = output + "  " + _get_player_info_line(player2)
            if year is None:
                output = output + " | Age: " + str(_calc_age(player['player_birth_date'])) + "\n"
            else:
                output = output + " | Age: " + str(_calc_age(player['player_birth_date'],year=season)) + "\n"
    if type == "hitting":
        stats = ['sport','ab','h','d','t','hr','r','rbi','bb','so','sb','cs','avg','obp','slg','ops']
    elif type == "pitching":
        stats = ['sport','w','l','g','svo','sv','ip','so','bb','hr','era','whip']
    output = output + "\n" + _print_table(stats,leagues,repl_map={'d':'2B','t':'3B','sport':'lev'})
    return output

def get_milb_log(name,number=5):
    player = milb_player_search(name)
    if player is None:
        return "No player found"
    name = player['name_first_last']
    teamabv = player['team_name_abbrev']
    level = player['level']
    parent = player['parent_team']
    id = player['player_id']
    try:
        pos = int(player['primary_position'])
        if pos == 1:
            type = "pitching"
        else:
            type = "hitting"
    except:
        print("%s is an OF" % name)
        type = "hitting"
    if number > 15:
        number = 15
    url = "http://lookup-service-prod.bamgrid.com/lookup/json/named.sport_bio_hitting_last_10.bam?results=" + str(number) + "&game_type=%27R%27&game_type=%27F%27&game_type=%27D%27&game_type=%27L%27&game_type=%27W%27&game_type=%27C%27" \
          "&season=2018&player_id="+id+"&league_list_id=%27milb_all%27&sport_hitting_last_x.col_in=game_date&sport_hitting_last_x.col_in=opp&sport_hitting_last_x.col_in=ab&sport_hitting_last_x.col_in=r&sport_hitting_last_x.col_in=h&sport_hitting_last_x.col_in=hr&sport_hitting_last_x.col_in=rbi&sport_hitting_last_x.col_in=bb&sport_hitting_last_x.col_in=so&sport_hitting_last_x.col_in=sb&sport_hitting_last_x.col_in=avg&sport_hitting_last_x.col_in=home_away&sport_hitting_last_x.col_in=game_id&sport_hitting_last_x.col_in=game_type&sport_hitting_last_x.col_in=sport_id&sport_hitting_last_x.col_in=sport"
    if type == "pitching":
        url = "http://lookup-service-prod.bamgrid.com/lookup/json/named.sport_bio_pitching_last_10.bam?results=" + str(number) + "&game_type=%27R%27&game_type=%27F%27&game_type=%27D%27&game_type=%27L%27&game_type=%27W%27&game_type=%27C%27" \
              "&season=2018&player_id="+id+"&league_list_id=%27milb_all%27&sport_pitching_last_x.col_in=game_date&sport_pitching_last_x.col_in=opp&sport_pitching_last_x.col_in=w&sport_pitching_last_x.col_in=l&sport_pitching_last_x.col_in=era&sport_pitching_last_x.col_in=sv&sport_pitching_last_x.col_in=ip&sport_pitching_last_x.col_in=h&sport_pitching_last_x.col_in=er&sport_pitching_last_x.col_in=bb&sport_pitching_last_x.col_in=so&sport_pitching_last_x.col_in=home_away&sport_pitching_last_x.col_in=game_id&sport_pitching_last_x.col_in=game_type&sport_pitching_last_x.col_in=sport_id&sport_pitching_last_x.col_in=sport"
    print(url)
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    s = json.loads(urlopen(req).read().decode("utf-8"))['sport_bio_'+type+'_last_10']['sport_'+type+'_game_log']['queryResults']
    num = int(s['totalSize'])
    gamelog = s['row']
    output = "Game Log for %s's (%s - %s) last %d games:\n\n" % (name, teamabv, level, num)
    games = []
    if num == 1:
        games.append(gamelog)
    else:
        for i in range(num):
            game = gamelog[-i-1]
            games.append(game)
    if type == "hitting":
        stats = ['game_day','opponent_abbrev','ab','h','d','t','hr','r','rbi','bb','so','sb','cs','avg','obp','slg','ops']
    elif type == "pitching":
        stats = ['game_day','opponent_abbrev','w','l','svo','sv','ip','h','r','er','so','bb','hr','era','whip']
    repl_map = {'game_day':'day','opponent_abbrev':'opp', 'd':'2B', 't':'3B'}
    output = output + _print_table(stats,games,repl_map=repl_map) + "\n"
    return output

def _calc_age(birthdate, year=None):
    byear,month,day = birthdate[:birthdate.find('T')].split('-')
    if year is None:
        now = datetime.now()
        return now.year - int(byear) - ((now.month, now.day) < (int(month), int(day)))
    else:
        return int(year) - int(byear) - ((7,1) < (int(month), int(day)))

def compare_player_stats(playerlist,career=False,year=None):
    players = []
    output = ""
    for player in playerlist:
        p = _get_player_search(player)
        if p is not None:
            players.append(p)
            output = output + p['name_display_first_last'] + " vs "
    output = output[:-4] + "\n\n"
    pos = players[0]['position']
    type = 'hitting'
    statlist = ['name','ab','h','d','t','hr','r','rbi','bb','so','sb','cs','avg','obp','slg','ops']
    if pos == 'P':
        type = 'pitching'
        statlist = ['name','w','l','g','svo','sv','ip','so','bb','hr','era','whip']
    errors = ""
    stats = []
    now = datetime.now()
    if year is None:
        year = str(now.year)
    for player in players:
        pid = player['player_id']
        disp_name = player['name_display_first_last']
        url = "http://lookup-service-prod.mlb.com/json/named.sport_" + type + "_composed.bam?game_type=%27R%27&league_list_id=%27mlb_hist%27&player_id=" + str(pid)
        print(url)
        s = _get_json(url)
        sport = "sport_"
        if career:
            sport = "sport_career_"
        if s['sport_'+type+'_composed'][sport+type+"_agg"]["queryResults"]["totalSize"] == "0":
            errors = errors + "No %s stats for %s\n" % (type, disp_name)
            continue
        seasonstats = s['sport_'+type+'_composed'][sport+type+"_agg"]["queryResults"]["row"]
        seasons = s['sport_'+type+'_composed']["sport_"+type+"_agg"]["queryResults"]["row"]
        sport_tm = s['sport_'+type+'_composed']['sport_'+type+"_tm"]['queryResults']['row']
        if not career:
            if "season" in seasonstats:
                if seasonstats["season"] == year:
                    s = seasonstats
                if sport_tm['season'] != year:
                    errors = errors + "No %s stats for %s\n" % (year, disp_name)
                    continue
            else:
                for season in seasonstats:
                    if season["season"] == year:
                        s = season
                if s is None:
                    errors = errors + "No %s stats for %s\n" % (year, disp_name)
                    continue
        else: #career stats
            s = seasonstats
        if 'season' not in s:
            errors = errors + "No %s stats for %s\n" % (year, disp_name)
            continue
        s['name'] = player['name_last'][:5]
        stats.append(s)
    output = output + _print_table(statlist, stats) + "\n\n" + errors
    return output

def get_player_season_stats(name, type=None, year=None, year2=None, active='Y', career=False):
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
    infoline = _get_player_info_line(player)
    now = datetime.now()
    birthdate = player['birth_date']
    birthdate = birthdate[:birthdate.find('T')]
    birth = birthdate.split('-')
    d = None
    if year == None and active == 'Y':
        d = now.year - int(birth[0]) - ((now.month, now.day) < (int(birth[1]), int(birth[2])))
    elif year is not None:
        d = int(year) - int(birth[0]) - ((7,1) < (int(birth[1]), int(birth[2])))
    if d is not None:
        infoline = "%s | Age: %d" % (infoline, d)
    if now.month == int(birth[1]) and now.day == int(birth[2]):
        infoline = infoline + "  **HAPPY BIRTHDAY**"
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
    if year is None:
        year = str(now.year)
    s = []
    if not career:
        if "season" in seasonstats:
            if seasonstats["season"] == year:
                s = [seasonstats]
            if sport_tm['season'] == year:
                teamabv = sport_tm['team_abbrev']
            else:
                return "No stats for %s" % disp_name
        else:
            for season in seasonstats:
                syear = season['season']
                if year2 is None and syear == year:
                        s.append(season)
                elif year2 is not None and int(syear)>= int(year) and int(syear) <= int(year2):
                    s.append(season)
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
        s = [seasonstats]
        output = "Career stats for %s (%s):" % (disp_name,years)
    output = "%s\n\t%s\n\n" % (output, infoline)

    if type == "hitting":
        stats = ['ab','h','d','t','hr','r','rbi','bb','so','sb','cs','avg','obp','slg','ops']
    elif type == "pitching":
        stats = ['w','l','g','gs','svo','sv','ip','so','bb','hr','era','whip']
    if year2 is not None:
        stats = ['season'] + stats
    output = output + _print_table(stats,s, repl_map={'season':'year'})
    return output

def search_highlights(query):
    results = recap.search_video(query)
    if len(results) == 0:
        return "No highlights found"
    first = results[0]
    blurb = first['blurb']
    length = first['duration'][3:]
    date = first['display_timestamp'][:10]
    url = recap.get_direct_video_url(first['url'])
    return "(%s) %s - %s:\n%s" % (date, blurb, length, url)

def get_game_highlights_plays(gamepk):
    url = "https://statsapi.mlb.com/api/v1/game/" + str(gamepk) + "/content"
    print(url)
    items = _get_json(url)['highlights']['live']['items']
    plays = dict()
    for item in items:
        for keyword in item['keywordsAll']:
            if keyword['type'] == "sv_id":
                svid = keyword['value']
                plays[svid] = item
    return plays

def get_inning_plays(team, inning, delta=None):
    teamid = get_teamid(team)
    s = get_day_schedule(teamid=teamid, delta=delta)
    try:
        game = s['dates'][0]['games'][0]
    except IndexError:
        return "Couldn't find game"
    gamepk = game['gamePk']
    if game['teams']['away']['team']['id'] == teamid:
        side = 'top'
    else:
        side = 'bottom'
    highlights = get_game_highlights_plays(gamepk)
    url = "https://statsapi.mlb.com/api/v1/game/" + str(gamepk) + "/playByPlay"
    print(url)
    plays = _get_json(url)
    try:
        playsinning = plays['playsByInning'][inning-1][side]
    except IndexError:
        return "Inning not found."
    output = "%s %d:\n" % (plays['allPlays'][0]['about']['halfInning'].upper(), plays['allPlays'][playsinning[0]]['about']['inning'])
    for idx in playsinning:
        play = plays['allPlays'][idx]
        try:
            curplayevent = play['playEvents'][-1]
            cnt = play['count']
            balls = cnt['balls']
            strikes = cnt['strikes']
            outs = cnt['outs']
            if play['about']['hasOut']:
                outs -= 1
            if curplayevent['details']['isBall']:
                balls -= 1
            if curplayevent['details']['isStrike']:
                strikes -= 1
        except:
            continue
        count = "(%d out, %d-%d)" % (outs, balls, strikes)
        opppitcher = play['matchup']['pitcher']['fullName']
        desc = ""
        if 'description' in play['result']:
            desc = "With %s pitching, %s" % (opppitcher, play['result']['description'])
        pitch = curplayevent['details']['type']['description']
        pspeed = curplayevent['pitchData']['startSpeed']
        data = "(%.1f mph %s" % (pspeed, pitch)
        if 'hitData' in curplayevent:
            hitdata = curplayevent['hitData']
            try:
                dist = str(int(hitdata['totalDistance']))
            except:
                dist = str(hitdata['totalDistance'])
            try:
                speed = "%.1f mph" % hitdata['launchSpeed']
            except:
                speed = str(hitdata['launchSpeed'])
            try:
                angle = "%d" % hitdata['launchAngle']
            except:
                angle = str(hitdata['launchAngle'])
            data = data + " | %s ft, %s mph, %s degrees" % (dist, speed, angle)
        data = data + ")"
        if play['about']['isScoringPlay']:
            desc = desc + "(%d-%d)" % (play['result']['awayScore'], play['result']['homeScore'])
            desc = "**%s**" % desc
        data = data# + "\n"
        output = "%s%s %s %s\n" % (output, count, desc, data)
        # output = output + "\n\n" + desc
        for event in play['playEvents']:
            if 'playId' in event:
                if event['playId'] in highlights:
                    blurb = highlights[event['playId']]['blurb']
                    for playback in highlights[event['playId']]['playbacks']:
                        if playback['name'] == "FLASH_2500K_1280X720":
                            url = playback['url']
                            output = output + " -- %s: <" % blurb + url + ">\n"
        output = output + "\n"
    return output

def print_roster(team,hitters=True):
    teamid = get_teamid(team)
    if teamid == None:
        return "Team not found"
    roster = get_team_info(teamid)['roster']
    pitchers = []
    batters = []
    for player in roster:
        if 'stats' in player['person']:
            s = player['person']['stats'][0]['splits'][0]['stat']
        else:
            s = dict()
        s['name'] = player['person']['fullName']
        s['pos'] = player['position']['abbreviation']
        if int(player['position']['code']) == 1:
            pitchers.append(s)
        else:
            batters.append(s)
    if hitters:
        output = "List of batters:\n\n"
        items = ['name','pos','gamesPlayed','atBats','ops']
        output = output + _print_table(items,batters,repl_map={'gamesPlayed':'G','atBats':'ab'})
    else:
        for p in pitchers:
            print(p['name'])
        output = "List of pitchers:\n\n"
        items = ['name','gamesPlayed','inningsPitched','era','whip']
        output = output + _print_table(items,pitchers,repl_map={'gamesPlayed':'G','inningsPitched':'ip'})
    return output

def _print_table(labels, dicts, repl_map={}):
    repl_map = {'d':'2B','t':'3B', **repl_map}
    lines = ['' for i in range(len(dicts)+1)]
    for label in labels:
        l = label
        if l in repl_map:
            l = repl_map[label]
        length = len(l)
        for d in dicts:
            if label in d:
                r = str(d[label])
            else:
                r = ""
            length = max(length, len(r))
        lines[0] = "%s %s" % (lines[0], l.rjust(length).upper())
        for i in range(len(dicts)):
            if label in dicts[i]:
                r = str(dicts[i][label])
            else:
                r = ""
            lines[i+1] = "%s %s" % (lines[i+1], r.rjust(length))
    return '\n'.join(lines)

def _print_labeled_list(labels, dict, header=True, repl_map={'d':'2B','t':'3B'}):
    line1 = ""
    line2 = ""
    for label in labels:
        if label in dict:
            r = str(dict[label])
        else:
            r = ""
        if label in repl_map:
            label = repl_map[label]
        l = max(len(r), len(label))
        line1 = "%s %s" % (line1, label.rjust(l).upper())
        line2 = "%s %s" % (line2, r.rjust(l))
    if not header:
        return line2
    return "%s\n%s" % (line1, line2)

if __name__ == "__main__":
    #make_mlb_schedule()
    # get_mlb_teams()
    # print(get_single_game("chc"))
    # print(print_linescore("chc"))
    # print(get_single_game("nle"))
    # print(get_single_game("nationals",delta="+1"))
    # print(get_all_game_info(delta='-1'))
    # print(get_all_game_info(liveonly=True))
    # print(get_all_game_info())
    #get_ET_from_timestamp("2018-03-31T20:05:00Z")
    # print(get_div_standings("nle"))
    #bs = BoxScore.BoxScore(get_boxscore('529456'))
    #bs.print_box()
    # print(get_stat_leader('sb'))
    # print(list_scoring_plays('chc'))
    # print(get_ohtani_stats())
    # print(get_player_season_stats("adam eaton", career=True))
    # print(get_player_season_stats("doolittle", year="2015"))
    # print(get_player_season_stats("shohei ohtani", career=True))
    # print(get_player_season_stats("shohei ohtani", type="pitching"))
    # print(get_player_season_stats("jose guillen"))
    # print(get_player_line("cole"))
    # print(get_player_line("ryan zimmerman", delta="-4382"))
    # print(print_box('nationals','batting'))
    # print(get_player_trailing_splits("Adam Eaton", 7))
    # print(get_player_gamelogs("Max Scherzer"))
    # print(get_team_schedule("wsh",3,backward=False))
    # print(get_team_dl('wsh'))
    # print(get_milb_log("koda glover"))
    # print(get_milb_season_stats("alejandro de aza"))
    # print(get_milb_season_stats("carter kieboom",year="2017"))
    # print(search_highlights("Murphy"))
    # print(get_player_season_splits("Bryce Harper","vsl", year="2017"))
    # print(player_vs_team("chris archer","wsh"))
    # print(get_game_highlights_plays("530753"))
    # print(get_inning_plays("col", 7))
    # print(compare_player_stats(["ohtani", "harper"]))
    print(print_roster('wsh',hitters=False))
