import urllib.parse
import json
import utils
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import mymlbstats

API_LINK = 'https://statsapi.mlb.com/api/v1/'

def _convert_date_to_mlb_str(date):
    """converts mm/dd</yyyy> to yyyy-mm-dd"""
    if isinstance(date, datetime):
        return "%d-%02d-%02d" % (date.year, date.month, date.day)
    if len(date.split('-')) == 3:
        return date
    now = datetime.now().date()
    if isinstance(date, list):
        datelist = date[-1].split('/')
    else:
        datelist = date.split('/')
    if len(datelist) == 2:
        datelist.append(str(now.year))
    if len(datelist[2]) == 2:
        if int("20" + datelist[2]) <= now.year:
            datelist[2] = "20" + datelist[2]
        else:
            datelist[2] = "19" + datelist[2]
    return "%s-%s-%s" % (datelist[2], datelist[0], datelist[1])

def _find_player_id(name):
    url = "https://typeahead.mlb.com/api/v1/typeahead/suggestions/%s" % urllib.parse.quote(name)
    players = utils.get_json(url)['players']
    if len(players) > 0:
        p = players[0]['playerId']
        for player in players:
            if player['teamId'] == 120:
                p = player['playerId']
                break
        return p

def _new_player_search(name):
    p = _find_player_id(name)
    url = API_LINK + "people/%s?hydrate=currentTeam,team,stats(type=[yearByYear,yearByYearAdvanced,careerRegularSeason,careerAdvanced,availableStats](team(league)),leagueListId=mlb_hist)" % p
    return utils.get_json(url)['people'][0]

def _get_stats_string(stats, group=None, include_gp=False):
    if group is None:
        group = stats[0]['group']['displayName']

    if group == "hitting":
        labels = ['atBats', 'hits', 'doubles', 'triples', 'homeRuns', 'runs', 'rbi', 'baseOnBalls', 'strikeOuts', 'stolenBases', 'caughtStealing', 'avg', 'obp', 'slg' ,'ops']
    elif group == "pitching":
       labels = ['wins', 'losses', 'gamesPlayed', 'gamesStarted', 'saveOpportunities', 'saves', 'inningsPitched', 'strikeOuts', 'baseOnBalls', 'homeRuns', 'era', 'whip']

    repl = {'atBats':'ab', 'plateAppearances':'pa','hits':'h','doubles':'2B','triples':'3b','homeRuns':'hr', 'runs':'r', 'baseOnBalls':'bb','strikeOuts':'so', 'stolenBases':'sb', 'caughtStealing':'cs',
            'wins':'w', 'losses':'l', 'gamesPlayed':'g', 'gamesStarted':'gs', 'saveOpportunities':'svo', 'saves':'sv', 'inningsPitched':'ip'}

    if include_gp:
        labels.insert(0, 'gamesPlayed')

    statrows = []
    for g in stats:
        if g['group']['displayName'] == group:
            row = g['splits'][0]['stat']
            row['season'] = g['splits'][0]['season']
            statrows.append(row)

    return utils.format_table(labels, statrows, repl_map=repl)

def _get_multiple_stats_string(playerlist, group=None, include_gp=False, reddit=False):
    if group is None:
        group = playerlist[0]['stats'][0]['group']['displayName']

    if group == "hitting":
        labels = ['atBats', 'hits', 'doubles', 'triples', 'homeRuns', 'runs', 'rbi', 'baseOnBalls', 'strikeOuts', 'stolenBases', 'caughtStealing', 'avg', 'obp', 'slg' ,'ops']
    elif group == "pitching":
        labels = ['wins', 'losses', 'gamesPlayed', 'gamesStarted', 'saveOpportunities', 'saves', 'inningsPitched', 'strikeOuts', 'baseOnBalls', 'homeRuns', 'era', 'whip']

    repl = {'atBats':'ab', 'plateAppearances':'pa','hits':'h','doubles':'2B','triples':'3b','homeRuns':'hr', 'runs':'r', 'baseOnBalls':'bb','strikeOuts':'so', 'stolenBases':'sb', 'caughtStealing':'cs',
            'wins':'w', 'losses':'l', 'gamesPlayed':'g', 'gamesStarted':'gs', 'saveOpportunities':'svo', 'saves':'sv', 'inningsPitched':'ip', 'lastName':'name'}
    left = ['lastName']

    if include_gp:
        labels.insert(0, 'gamesPlayed')
    if len(playerlist) > 1:
        labels.insert(0, 'lastName')

    statrows = []
    for player in playerlist:
        for g in player['stats']:
            if g['group']['displayName'] == group:
                row = g['splits'][0]['stat']
                row['season'] = g['splits'][0]['season']
                row['lastName'] = player['lastName']
                if not reddit:
                    row['lastName'] = row['lastName'][:5]
                statrows.append(row)

    return utils.format_table(labels, statrows, repl_map=repl, left_list=left, reddit=reddit, bold=True)

def get_player_stats(name, group=None, stattype=None, startDate=None, endDate=None, lastgames=None):
    if stattype is None:
        return None
    playerid = _find_player_id(name)
    if playerid is None:
        return "Couldn't find player"
    url = None
    groupstr = ""
    if group is not None:
        groupstr = "group=%s," % group

    if stattype == "byDateRange":
        url = API_LINK + "people/%s?" \
          "hydrate=currentTeam,team,stats(%stype=[byDateRange](team(league)),leagueListId=mlb_hist,startDate=%s,endDate=%s)" \
              % (playerid, groupstr, startDate, endDate)
    elif stattype == "lastXGames":
        url = API_LINK + "people/%s?" \
              "hydrate=currentTeam,team,stats(%stype=[lastXGames](team(league)),leagueListId=mlb_hist,limit=%s)" \
              % (playerid, groupstr, lastgames)
    if url is not None:
        player = utils.get_json(url)['people'][0]
        return player

def print_player_stats(name, group=None, stattype=None, startDate=None, endDate=None, lastgames=None, reddit=False):
    if stattype is not None:
        if startDate is not None and endDate is None:
            endDate = mymlbstats._timedelta_to_mlb(datetime.today())
        names = name.split('/')
        players = list()
        for name in names:
            players.append(get_player_stats(name, group=group, stattype=stattype, startDate=startDate, endDate=endDate, lastgames=lastgames))

        statsstr = _get_multiple_stats_string(players, group=group, include_gp=True, reddit=reddit)
        output = ""
        namesliststr = ""
        for player in players:
            namesliststr += "%s, " % player['fullName']
        namesliststr = namesliststr[:-2]
        if stattype == "byDateRange":
            output = "%s to %s for %s:\n\n" % (startDate, endDate, namesliststr)
        elif stattype == "lastXGames":
            output = "Last %s games for %s:\n\n" % (lastgames, namesliststr)
        output += statsstr
        return output

def print_last_x_days(name, ndays, group=None, reddit=False):
    startDate = mymlbstats._timedelta_to_mlb(datetime.today() - timedelta(days=ndays))
    return print_player_stats(name, group=group, stattype="byDateRange", startDate=startDate, reddit=reddit)

def print_last_x_games(name, ngames, group=None, reddit=False):
    return print_player_stats(name, group=group, stattype="lastXGames", lastgames=ngames, reddit=reddit)

def _get_player_info_line(player, seasons=None):
    pos = player['primaryPosition']['abbreviation']
    bats = player['batSide']['code']
    throws = player['pitchHand']['code']
    height = player['height'].replace(' ','')
    weight = player['weight']

    nick = None
    if 'nickName' in player:
        nick = player['nickName']

    bdate = player['birthDate'].split("-")
    bdatetime = datetime.strptime(player['birthDate'], "%Y-%m-%d")
    today = datetime.today()
    if seasons is None or seasons == str(today.year):
        t = datetime(today.year, 7, 1)
        curage = today.year - bdatetime.year - ((today.month, today.day) < (bdatetime.month, bdatetime.day))
        sznage = t.year - bdatetime.year - ((t.month, t.day) < (bdatetime.month, bdatetime.day))
        if curage != sznage:
            age = "%d (now %d)" % (sznage, curage)
        else:
            age = curage

    elif '-' not in seasons:
        t = datetime(int(seasons), 7, 1)
        age = t.year - bdatetime.year - ((t.month, t.day) < (bdatetime.month, bdatetime.day))
    else:
        season1, season2 = seasons.split('-')
        t1 = datetime(int(season1), 7, 1)
        t2 = datetime(int(season2), 7, 1)
        age1 = t1.year - bdatetime.year - ((t1.month, t1.day) < (bdatetime.month, bdatetime.day))
        age2 = t2.year - bdatetime.year - ((t2.month, t2.day) < (bdatetime.month, bdatetime.day))
        age = "%d-%d" % (age1, age2)

    ret = "%s | %s/%s | %s %s | Age: %s" % (pos, bats, throws, height, weight, age)
    if nick is not None:
        ret += " | \"%s\"" % nick

    if int(bdate[1]) == today.month and int(bdate[2]) == today.day:
        ret += "\n         ****HAPPY BIRTHDAY****"
    return ret

def get_team_info(teamid):
    """
    return stats api data for teamid
    :param teamid:
    :return:
    """
    url = API_LINK + "teams/%s?hydrate=team,sport" % teamid
    results = utils.get_json(url)
    if len(results['teams']) > 0:
        return results['teams'][0]

def get_player_season_stats(name, type=None, year=None, career=None, reddit=None):
    player = _new_player_search(name)
    if player is None:
        return "No matching player found"
    # teamid = player['currentTeam']['id']
    teamabv = player['currentTeam']['abbreviation']
    # pid = player['id']
    disp_name = player['fullName']
    pos = player['primaryPosition']['abbreviation']
    infoline = _get_player_info_line(player, seasons=year)
    now = datetime.now()

    if year is None:
        year = str(now.year)
        year2 = year
    elif '-' in year:
        years = year.split('-')
        year = years[0]
        year2 = years[1]
    else:
        year2 = year

    if type is None and pos == 'P':
        type = "pitching"
    elif type is None and pos != 'P':
        type = "hitting"

    stattype = 'yearByYear'
    if career:
        stattype = "career"

    seasons = []
    teams = []
    for stat in player['stats']:
        if stat['type']['displayName'] == stattype and 'displayName' in stat['group'] and stat['group']['displayName'] == type:
            if career:
                for cstat in player['stats']:
                    if cstat['type']['displayName'] == 'yearByYear' and 'displayName' in cstat['group'] and cstat['group']['displayName'] == type:
                        years = "%s-%s" % (cstat['splits'][0]['season'], cstat['splits'][-1]['season'])
            for split in stat['splits']:
                if stattype == 'yearByYear':
                    if int(split['season']) < int(year) or int(split['season']) > int(year2):
                        continue
                season = split['stat']
                if 'season' in split:
                    season['season'] = split['season']
                if 'team' in split:
                    season['team'] = split['team']['abbreviation']
                    teams.append(season['team'])
                else:
                    if 'sport' in split:
                        season['team'] = split['sport']['abbreviation']
                    else:
                        season['team'] = "MLB"
                seasons.append(split['stat'])
    if type == "hitting":
        stats = ['atBats', 'hits', 'doubles', 'triples', 'homeRuns', 'runs', 'rbi', 'baseOnBalls', 'strikeOuts', 'stolenBases', 'caughtStealing', 'avg', 'obp', 'slg' ,'ops']
    elif type == "pitching":
        stats = ['wins', 'losses', 'gamesPlayed', 'gamesStarted', 'saveOpportunities', 'saves', 'inningsPitched', 'strikeOuts', 'baseOnBalls', 'homeRuns', 'era', 'whip']
    if len(seasons) > 1:
        stats = ['season', 'team'] + stats
    repl = {'atBats':'ab', 'plateAppearances':'pa','hits':'h','doubles':'2B','triples':'3b','homeRuns':'hr', 'runs':'r', 'baseOnBalls':'bb','strikeOuts':'so', 'stolenBases':'sb', 'caughtStealing':'cs',
            'wins':'w', 'losses':'l', 'gamesPlayed':'g', 'gamesStarted':'gs', 'saveOpportunities':'svo', 'saves':'sv', 'inningsPitched':'ip'}

    if year == year2:
        if year == str(now.year) and len(teams) == 0 and 'currentTeam' in player:
            teamabv = player['currentTeam']['abbreviation']
            if player['currentTeam']['sport']['id'] != 1:
                parent = get_team_info(player['currentTeam']['parentOrgId'])
                milb = get_team_info(player['currentTeam']['id'])
                teamabv += " - %s %s" % (parent['abbreviation'], milb['sport']['abbreviation'])
        else:
            teamabv = '/'.join(teams)
        output = "%s season stats for %s (%s):" % (year, disp_name, teamabv)
    else:
        output = "%s-%s seasons stats for %s:" % (year, year2, disp_name)
    if career:
        output = "Career stats for %s (%s):" % (disp_name, years)
    output = "%s\n  %s\n\n" % (output, infoline)
    output = output + utils.format_table(stats, seasons, repl_map=repl, reddit=reddit)
    return output

def get_scoring_plays(gamepk):
    url = "https://statsapi.mlb.com/api/v1/game/%s/playByPlay" % str(gamepk)
    data = utils.get_json(url)
    playslist = list()
    for play in data['scoringPlays']:
        playslist.append(data['allPlays'][play])
    return playslist

def get_stat_leaders(stat, season=None, league=None, position=None, teamid=None):
    with open('mlb/statsapi_json/baseballStats.json', 'r') as f:
        stats = json.loads(''.join(f.readlines()))

    lookup_stat = None

    for s in stats:
        if stat == s['name'].lower() or stat == s['lookupParam']:
            lookup_stat = s

    # for group in statgroups:
    #     for i in statgroups[group]['columns']:
    #         for s in i['groupColumns']:
    #             if stat == s['dataField'].lower() or stat == s['labelBrief'].lower():
    #                 lookup_stat = s

    if lookup_stat is not None:
        season_text = "&season=%s" % season if season is not None else ''
        if league is not None:
            league_text = "&leagueId=%d" % 103 if league == "al" else "&leagueId=%d" % 104
        else:
            league_text = ""
        if position is not None and position == "OF":
            position_text = ""
            for i in ['LF','CF','RF','OF']:
                position_text += "&position=%s" % i
        else:
            position_text = "&position=%s" % position if position is not None else ''
        teamtext = ""
        if teamid is not None:
            teamtext = "&teamId=%d" % teamid
        url = API_LINK + 'stats/leaders?leaderCategories=%s%s%s%s%s&limit=10&hydrate=team' % (lookup_stat['name'], season_text, league_text, position_text, teamtext)
        results = utils.get_json(url)['leagueLeaders']
        return results

def print_stat_leaders(statquery_list, season=None):
    league = None
    if 'al' in statquery_list:
        league = 'al'
        statquery_list.remove('al')
    elif 'nl' in statquery_list:
        league = 'nl'
        statquery_list.remove('nl')

    want_group = None
    groups = ['hitting', 'pitching', 'fielding', 'catching']
    for i in statquery_list:
        if i in groups:
            want_group = i
            statquery_list.remove(i)
            break

    positions = ['c','1b','2b','3b','ss','lf','cf','rf','of','p','dh']
    pos = None
    for i in statquery_list:
        if i.lower() in positions:
            pos = i.upper()
            statquery_list.remove(i)

    stat = statquery_list.pop()
    team = None
    if len(statquery_list) > 0:
        team = mymlbstats.get_teamid(' '.join(statquery_list))

    print(stat)
    leaders = get_stat_leaders(stat, season=season, league=league, position=pos, teamid=team)
    if leaders is None:
        return "Stat not found"
    group = None
    for statgroup in leaders:
        if statgroup['statGroup'] == want_group or want_group is None:
            group = (statgroup['statGroup'], list())
            for leader in statgroup['leaders'][:10]:
                player = dict()
                player['team'] = leader['team']['abbreviation']
                player['name'] = leader['person']['fullName']
                player[stat] = leader['value']
                group[1].append(player)
            break
    if group is not None:
        output = ""
        output += "%s:\n```python\n" % group[0]
        labels = ['team', 'name', 'gamesPlayed', stat]
        left = ['team', 'name']
        output += utils.format_table(labels, group[1], left_list=left)
        output += "```\n"
        return output
    else:
        return "problem finding leaders"

def _get_stats_query_params(statquery_list, delta=None):
    date1, date2 = None, None
    if delta is not None:
        date1 = mymlbstats._get_date_from_delta(delta)
        date2 = date1

    stattype = "season"
    if 'today' in statquery_list:
        stattype = 'byDateRange'
        statquery_list.remove('today')
    if 'date' in statquery_list:
        stattype = 'byDateRange'
        statquery_list.remove('date')
        dates = 0
        for item in statquery_list:
            if '-' in item:
                sp = item.split('-')
                if '/' in sp[0] and '/' in sp[1]:
                    date1, date2 = sp[0], sp[1]
                    statquery_list.remove(item)
                    break
            elif len(item.split('/')) == 2 or len(item.split('/')) == 3:
                if dates == 0:
                    date1 = item
                    dates += 1
                elif dates == 1:
                    date2 = item
                    statquery_list.remove(date1)
                    statquery_list.remove(date2)
                    break

    league = None
    if 'al' in statquery_list:
        league = 'al'
        statquery_list.remove('al')
    elif 'nl' in statquery_list:
        league = 'nl'
        statquery_list.remove('nl')

    want_group = None
    groups = ['hitting', 'pitching', 'fielding', 'catching']
    for i in statquery_list:
        if i in groups:
            want_group = i
            statquery_list.remove(i)
            break

    positions = ['c','1b','2b','3b','ss','lf','cf','rf','of','p','dh']
    pos = None
    for i in statquery_list:
        if i.lower() in positions:
            pos = i.upper()
            statquery_list.remove(i)

    stat = statquery_list.pop()
    team = None
    if len(statquery_list) > 0:
        team = mymlbstats.get_teamid(' '.join(statquery_list))

    return (league, want_group, pos, team, stat, stattype, date1, date2)

def _find_stat_info(stat, retry=False):
    statsfile = 'mlb/statsapi_json/baseballStats.json'
    if retry:
        statsfile = 'mlb/statsapi_json/baseballStats2.json'
    with open(statsfile, 'r') as f:
        stats = json.loads(''.join(f.readlines()))

    for s in stats:
        if stat == s['name'].lower() or ('lookupParam' in s and stat == s['lookupParam']):
            return s
    if not retry:
        return _find_stat_info(stat, retry=True)

def get_sorted_stats(statinfo, season=None, league=None, position=None, teamid=None, teams=False, group=None, reverse=False, stats='season', date1=None, date2=None):
    if teams:
        url = API_LINK + "teams/stats?"
    else:
        url = API_LINK + "stats?"

    params = {'sortStat':statinfo['name'], 'sportIds':1}
    params['stats'] = stats
    params['limit'] = 30
    params['hydrate'] = "player,team"

    if stats == 'byDateRange':
        if date1 is None:
            date1 = mymlbstats._timedelta_to_mlb(datetime.now())
        else:
            date1 = _convert_date_to_mlb_str(date1)
        if date2 is not None:
            date2 = _convert_date_to_mlb_str(date2)
        params['startDate'] = date1
        if date2 is not None:
            params['endDate'] = date2

    if season is not None:
        params['season'] = season
    if league is not None:
        if league == 'nl':
            params['leagueId'] = 104
        elif league == 'al':
            params['leagueId'] = 103
    if position is not None:
        of = ['LF','CF','RF','OF']
        if position == 'OF':
            position = ','.join(of)
        params['position'] = position
    if teamid is not None:
        params['teamId'] = teamid
    if group is None:
        params['group'] = statinfo['statGroups'][0]['displayName']
    else:
        params['group'] = group
    if reverse:
        params['order'] = 'descending'

    url += urllib.parse.urlencode(params, safe=',')
    return utils.get_json(url)['stats']

def print_sorted_stats(statquery_list, season=None, reverse=False, delta=None):
    teams = False
    if statquery_list[0] == "teams":
        teams = True

    league, group, position, team, stat, stattype, date1, date2 = _get_stats_query_params(statquery_list, delta=delta)
    # print(league, group, position, team, stat)

    #teamid = None
    #if team is not None:
    #    teamid = mymlbstats.get_teamid(team)
    statinfo = _find_stat_info(stat)

    if group is not None and group not in ['hitting','pitching','catching','fielding']:
        return "Invalid group"
    if group is None:
        group = statinfo['statGroups'][0]['displayName']

    stats = get_sorted_stats(statinfo, season=season, league=league, position=position, teamid=team, teams=teams,
                             group=group, reverse=reverse, stats=stattype, date1=date1, date2=date2)
    stats = stats[0]

    if statinfo['name'] in stats['splits'][0]['stat']:
        statname = statinfo['name']
    elif statinfo['lookupParam'] in stats['splits'][0]['stat']:
        statname = statinfo['lookupParam']
    elif statinfo['name'].endswith('s') and statinfo['name'][:-1] in stats['splits'][0]['stat']:
        statname = statinfo['name'][:-1]
    elif not statinfo['name'].endswith('s') and statinfo['name']+'s' in stats['splits'][0]['stat']:
        statname = statinfo['name']+'s'
    else:
        return "couldn't find stat %s or stat %s in search results" % (statinfo['name'], statinfo['lookupParam'])

    labels = ['team', 'name', 'gamesPlayed', statinfo['name']]
    repl = {'gamesPlayed':'gp', 'atBats':'ab', 'plateAppearances':'pa', 'inningsPitched':'ip'}
    left = ['team', 'name']

    if group == 'hitting':
        labels.insert(3,'plateAppearances')
    elif group == 'pitching':
        labels.insert(3,'inningsPitched')

    rows = list()
    for player in stats['splits']:
        row = dict()
        row = player['stat']
        row['team'] = player['team']['abbreviation']
        if teams:
            row['name'] = player['team']['teamName']
        else:
            row['name'] = player['player']['fullName']
        row[statinfo['name']] = player['stat'][statname]
        rows.append(row)
        if len(rows) >= 10:
            break
    output = ""
    if stattype == 'byDateRange':
        if date2 is None:
            output = "Stats from %s to today\n" % (date1)
        elif date1 == date2:
            output = "Stats from %s\n" % (date1 if isinstance(date1, str) else _convert_date_to_mlb_str(date1))
        else:
            output = "Stats from %s to %s\n" % (date1, date2)

    output += "%s:\n```python\n" % group
    output += utils.format_table(labels, rows, left_list=left, repl_map=repl)
    output += "```\n"
    return output

def get_40man(teamid):
    url = API_LINK + "teams/%d/roster/40Man?hydrate=person" % teamid
    results = utils.get_json(url)
    if 'roster' in results:
        return results['roster']

def get_coaches(teamid):
    url = API_LINK + "teams/%d/roster/coach?hydrate=person" % teamid
    results = utils.get_json(url)
    if 'roster' in results:
        return results['roster']

def print_birthdays(team, delta=None):
    if len(team) == 0:
        return "No team specified"
    teamid, teamdata = mymlbstats.get_teamid(team, extradata=True)
    if teamid is None:
        return "could not find team"
    roster = get_40man(teamid) + get_coaches(teamid)
    if delta is None:
        today = datetime.today()
    else:
        today = mymlbstats._get_date_from_delta(delta)
    todaystr = "%02d-%02d" % (today.month, today.day)
    birthdays = list()
    for player in roster:
        p = dict()
        player = player['person']
        if player['birthDate'][5:] == todaystr:
            p['age'] = today.year - int(player['birthDate'][:4])
            p['name'] = player['firstLastName']
            birthdays.append(p)
    if delta is None:
        todaystr = "today"
    else:
        todaystr = todaystr.replace('-','/')
    if len(birthdays) > 0:
        return "%s birthdays on %s:\n\n" % (teamdata['teamName'], todaystr) + utils.format_table(['name', 'age'], birthdays, left_list=['name'])
    else:
        return "No %s birthdays on %s" % (teamdata['teamName'], todaystr)

def get_player_headshot_url(player_search):
    player = _new_player_search(player_search)
    if player is not None:
        return "https://securea.mlb.com/mlb/images/players/head_shot/%d@3x.jpg" % player['id']
    return "Could not find player"

def get_pitch_arsenal(pitcherid, season=None):
    url = API_LINK + "people/%s/stats?stats=pitchArsenal&group=pitching" % pitcherid
    if season is not None:
        url += "&season=%s" % season
    results = utils.get_json(url)

    pitches = list()
    for pitch in results['stats'][0]['splits']:
        p = pitch['stat']
        p['code'] = pitch['stat']['type']['code']
        p['description'] = pitch['stat']['type']['description']
        p['percentage'] = '%.1f' % (p['percentage']*100)
        p['averageSpeed'] = '%.1f' % p['averageSpeed']
        pitches.append(p)
    return pitches

def print_pitch_arsenal(pitcher, season=None, reddit=False):
    print(pitcher)
    player = _new_player_search(pitcher)
    if player is None:
        return "could not find pitcher"

    pitches = get_pitch_arsenal(player['id'], season=season)

    labels = ['description', 'percentage', 'averageSpeed']
    left = ['description']
    repl = {'description':'pitch', 'percentage':'%', 'averageSpeed':'avg mph'}

    return "```python\n%s```" % utils.format_table(labels, pitches, left_list=left, repl_map=repl, reddit=reddit)

def print_contract_info(name, year=None):
    # find player
    player = _new_player_search(name)
    pname = player['fullName'].lower().replace(' ', '-')

    url = "https://www.spotrac.com/search/results/%s/" % (pname)
    html, returl = utils.get_page(url, return_url=True)

    if returl != url:
        return get_player_contract_table(html, url)
    else:
        ret = _parse_contract_search(html)
        if ret is not None:
            html, returl = utils.get_page(ret, return_url=True)
            return get_player_contract_table(html, returl)
        else:
            return "Could not find player"

def get_player_contract_table(html, url):
    # html = utils.get_page(url)
    # with open('spotrac.txt', 'r') as w:
    #     html = w.read()
    bs = BeautifulSoup(html, 'html.parser')
    blurb = bs.find("p", {"class":"currentinfo"})
    output = ""
    if blurb is not None:
        output = blurb.get_text() + "\n\n"
    table = bs.find("table", {"class":"salaryTable salaryInfo current visible-xs"})
    rows = table.find_all("tr")
    contract_table = []
    for row in rows:
        cells = row.find_all('td')
        r = {'0':cells[0].get_text(), '1':cells[1].get_text()}
        contract_table.append(r)
    output = output + "```python\n%s```" % utils.format_table(['0','1'], contract_table, showlabels=False)

    table = bs.find("table", {"class":"salaryTable current"})
    rows = table.find_all("tr")
    salary_table = []
    salary_th = []
    for header in rows[0].find_all('th'):
        salary_th.append(header.get_text())
    print(salary_th)
    for row in rows[1:]:
        year_row = {}
        cells = row.find_all('td')
        # print(cells)
        for i in range(len(salary_th)):
            try:
                if 'noborder' not in cells[i]['class'] or 'fayear' in cells[i]['class']:
                    data = cells[i].get_text().lstrip()
                    if data.startswith('$'):
                        if '(' in data:
                            data = data[:data.find('(')]
                        data = utils.human_format(data)
                    year_row[salary_th[i]] = data
            except:
                pass
        if len(year_row.keys()) > 0:
            salary_table.append(year_row)
    print(salary_table)
    labs = ['Year', 'Age', 'Base Salary','Luxury Tax Salary','Payroll  Salary', 'Adjusted Salary', 'Yearly Cash']
    repl = {"Base Salary":"Base", "Luxury Tax Salary":"Luxury Tax", "Payroll  Salary":"Payroll", "Adjusted Salary":"Adjusted", "Yearly Cash":"Take home"}
    output = output + "\n```python\n%s```" % utils.format_table(labs, salary_table, repl_map=repl)
    output = output + "\n<%s>" % url
    return output

def _parse_contract_search(html):
    bs = BeautifulSoup(html, 'html.parser')
    div = bs.find_all("div", {"class":"teamlist"})
    # print(div)
    positions = ["Starting Pitcher", "Relief Pitcher", "1st Base", "2nd Base", "3rd Base", "Catcher",
                 "Outfielder", "Outfielders", "Shortstop", "Right Field", "Center Field", "Left Field",
                 "Pitcher", "Pitchers"]
    items = div[0].find_all("div", {"class":"teamitem"})
    for item in items:
        pos = item.find_all("div", {"class":"teamoptions"})[0]
        print(pos.get_text())
        if pos.get_text() in positions:
            return item.find_all("a")[0]['href']

if __name__ == "__main__":
    # print(get_player_season_stats("rendon", year="2016-2019"))
    # print(get_player_season_stats("rendon", career=True))
    # print(get_player_season_stats('daniel hudson'))
    # print(print_contract_info("max scherzer"))
    # print(get_player_contract_table(""))
    # get_scoring_plays(630851)
    # print(print_stat_leaders('sb', season=2019))
    # print(print_birthdays('lad'))
    # print(print_sorted_stats("pitching nl hr".split(' '), season="2019"))
    # print(print_sorted_stats("teams pitching nl hr".split(' '), season="2019"))
    # print(print_player_stats("judge", stattype="byDateRange", startDate="2020-07-27"))
    # print(get_player_stats("ohtani", stattype="byDateRange", startDate="2020-07-27", endDate="2020-08-03"))
    # print(get_player_stats("ohtani", group="hitting", stattype="byDateRange", startDate="2020-07-27", endDate="2020-08-03"))
    # print(print_last_x_games("judge/castellanos", 6))
    # print(print_last_x_days("judge", 6))
    # print(print_pitch_arsenal('scherzer'))
    # get_sorted_stats(_find_stat_info('tb'), stats='byDateRange')
    print(print_sorted_stats(['today', 'tb'], delta="-1"))
