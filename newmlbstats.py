import urllib.parse
import json
import utils
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import mymlbstats
import calendar

API_LINK = 'https://statsapi.mlb.com/api/v1/'

def _get_common_replace_map():
    repl = {'atBats':'ab', 'plateAppearances':'pa','hits':'h','doubles':'2B','triples':'3b','homeRuns':'hr', 'runs':'r',
            'baseOnBalls':'bb','strikeOuts':'so', 'stolenBases':'sb', 'caughtStealing':'cs',
            'wins':'w', 'losses':'l', 'gamesPlayed':'g', 'gamesStarted':'gs', 'saveOpportunities':'svo', 'saves':'sv',
            'inningsPitched':'ip', 'lastName':'name', 'earnedRuns':'er', 'pitchesThrown':'p', 'strikes':'s', 'numberOfPitches':'p'}
    return repl

def _get_common_stats_list(pitching=False, pitching_game=False):
    '''pitching_game returns game level stats instead of season level'''
    if not pitching:
        labels = ['atBats', 'hits', 'doubles', 'triples', 'homeRuns', 'runs', 'rbi', 'baseOnBalls', 'strikeOuts',
              'stolenBases', 'caughtStealing', 'avg', 'obp', 'slg', 'ops']
    elif pitching_game:
        labels = ['inningsPitched', 'hits', 'runs', 'earnedRuns','homeRuns','baseOnBalls', 'strikeOuts', 'pitchesThrown', 'strikes']
    else:
        labels = ['wins', 'losses', 'gamesPlayed', 'gamesStarted', 'saveOpportunities', 'saves', 'inningsPitched',
                  'strikeOuts', 'baseOnBalls', 'homeRuns', 'era', 'whip']
    return labels

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

def _convert_mlb_date_to_datetime(date):
    return datetime.strptime(date, '%Y-%m-%d')

def _find_player_id(name):
    teamid = None
    if "(" in name and ")" in name:
        open = name.find('(')
        close = name.find(')')
        teamsrch = name.split('(', 1)[1].split(')')[0]
        teamid = mymlbstats.get_teamid(teamsrch)
        name = name[:open] + name[close+1:]
        name = name.strip()

    url = "https://typeahead.mlb.com/api/v1/typeahead/suggestions/%s" % urllib.parse.quote(name)
    players = utils.get_json(url)['players']
    if len(players) > 0:
        teamids = mymlbstats.get_mlb_teamid_list()
        p = None
        milb_p = None
        for player in players:
            if teamid is None:
                if player['teamId'] == 120:
                    return player['playerId']
                elif p is None and player['teamId'] in teamids:
                    p = player['playerId'] # don't just return here to keep searching for Nats
                elif milb_p is None:
                    milb_p = player['playerId'] # if we don't match a major leaguer, just return a minor leaguer
            else:
                if player['teamId'] == teamid:
                    return player['playerId']
        if p is None:
            return milb_p
        return p

def _get_player_by_id(id, type=None, milb=False):
    if type is None:
        url = API_LINK + "people/%s?hydrate=currentTeam,team,stats(type=[yearByYear,yearByYearAdvanced,careerRegularSeason,careerAdvanced,availableStats](team(league,sport)),leagueListId=%s)" % (id, 'mlb_milb' if milb else 'mlb_hist')
    else:
        url = API_LINK + "people/%s?hydrate=currentTeam,team,stats(type=[yearByYear,yearByYearAdvanced,careerRegularSeason,careerAdvanced,availableStats](team(league,sport)),leagueListId=%s,group=%s)" % (id, 'mlb_milb' if milb else 'mlb_hist', type)
    return utils.get_json(url)['people'][0]

def _new_player_search(name, type=None):
    post = False
    spring = False
    if 'postseason' in name:
        name = name.replace('postseason', '').strip()
        post = True
    elif 'spring ' in name:
        name = name.replace('spring ', '').strip()
        spring = True
    p = _find_player_id(name)
    if type is None:
        url = API_LINK + "people/%s?hydrate=currentTeam,team,stats(type=[yearByYear,yearByYearAdvanced,careerRegularSeason,careerAdvanced,availableStats](team(league)),leagueListId=mlb_hist)" % p
    else:
        url = API_LINK + "people/%s?hydrate=currentTeam,team,stats(type=[yearByYear,yearByYearAdvanced,careerRegularSeason,careerAdvanced,availableStats](team(league)),leagueListId=mlb_hist,group=%s)" % (p, type)
    player = utils.get_json(url)['people'][0]
    # for backwards compat
    player['player_id'] = str(player['id'])
    if post:
        url = API_LINK + "people/%s/stats?stats=yearByYear,career&gameType=P&leagueListId=mlb_hist&hydrate=team" % p
        stats = utils.get_json(url)
        player['stats'] = stats['stats']
    elif spring:
        url = API_LINK + "people/%s/stats?stats=yearByYear,career&gameType=S&leagueListId=mlb_hist&hydrate=team" % p
        stats = utils.get_json(url)
        player['stats'] = stats['stats']
    return player

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

def _get_multiple_stats_string(playerlist, group=None, include_gp=False, reddit=False, include_team=False):
    output = ""
    while group is None:
        if 'stats' in playerlist[0]:
            group = playerlist[0]['stats'][0]['group']['displayName']
        else:
            output += "No stats for %s\n" % playerlist[0]['fullName']
            playerlist.pop(0)

    if group == "hitting":
        labels = ['atBats', 'hits', 'doubles', 'triples', 'homeRuns', 'runs', 'rbi', 'baseOnBalls', 'strikeOuts', 'stolenBases', 'caughtStealing', 'avg', 'obp', 'slg' ,'ops']
    elif group == "pitching":
        labels = ['wins', 'losses', 'gamesPlayed', 'gamesStarted', 'saveOpportunities', 'saves', 'inningsPitched', 'strikeOuts', 'baseOnBalls', 'homeRuns', 'era', 'whip']

    repl = {'atBats':'ab', 'plateAppearances':'pa','hits':'h','doubles':'2B','triples':'3b','homeRuns':'hr', 'runs':'r', 'baseOnBalls':'bb','strikeOuts':'so', 'stolenBases':'sb', 'caughtStealing':'cs',
            'wins':'w', 'losses':'l', 'gamesPlayed':'g', 'gamesStarted':'gs', 'saveOpportunities':'svo', 'saves':'sv', 'inningsPitched':'ip', 'lastName':'name'}
    left = ['lastName', 'season']

    if include_gp:
        labels.insert(0, 'gamesPlayed')
    if len(playerlist) > 1:
        labels.insert(0, 'lastName')

    statrows = []
    removelist = []
    insert_season = False
    for player in playerlist:
        if 'stats' in player:
            for g in player['stats']:
                rnge = [0]
                if len(playerlist) == 1 and len(g['splits']) > 2:
                    rnge = range(len(g['splits']))
                    insert_season = True

                for i in rnge:
                    # if g['group']['displayName'] == group and ('sport' not in g['splits'][i] or g['splits'][i]['sport']['id'] != 0):
                    if g['group']['displayName'] == group:
                        row = g['splits'][i]['stat']
                        # row['season'] = g['splits'][i]['season']
                        row['lastName'] = player['lastName']
                        if not reddit:
                            row['lastName'] = row['lastName'][:5]
                        if 'team' in g['splits'][i]:
                            row['team'] = g['splits'][i]['team']['abbreviation']
                        else:
                            row['team'] = g['splits'][i]['sport']['abbreviation']
                        statrows.append(row)
        else:
            output += "No stats for %s\n" % player['fullName']
            removelist.append(player)

    if len(statrows) > 1 and statrows[0]['team'] != statrows[1]['team']:
        labels.insert(0, 'team')
    if insert_season and 'season' in statrows[0]:
        labels.insert(0, 'season')
    for player in removelist:
        playerlist.remove(player)

    if len(output) > 0:
        output += "\n"

    bold = False
    if len(playerlist) > 1:
        bold = True

    return output + utils.format_table(labels, statrows, repl_map=repl, left_list=left, reddit=reddit, bold=bold)

def get_player_stats(name, group=None, stattype=None, startDate=None, endDate=None, lastgames=None, playerid=None):
    if stattype is None:
        return None
    if playerid is None:
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
        roster = None
        team = None
        players = list()
        if '/' not in name:
            teamid, team = mymlbstats.get_teamid(name, extradata=True)
            if teamid is not None:
                roster = mymlbstats.get_team_info(teamid)['roster']
                if group is None:
                    group = 'hitting'
                for player in roster:
                    if group == 'hitting' and player['person']['primaryPosition']['code'] != '1':
                        p = get_player_stats("", playerid=player['person']['id'], group=group, stattype=stattype, startDate=startDate, endDate=endDate, lastgames=lastgames)
                        if 'stats' in p:
                            if len(p['stats'][0]['splits']) == 0:
                                d = {'stat':{'plateAppearances':0}}
                                p['stats'][0]['splits'].append(d)
                            players.append(p)
                    elif group == 'pitching' and player['person']['primaryPosition']['code'] == '1':
                        p = get_player_stats("", playerid=player['person']['id'], group=group, stattype=stattype, startDate=startDate, endDate=endDate, lastgames=lastgames)
                        if 'stats' in p and len(p['stats'][0]['splits']) > 0:
                            if 'inningsPitched' not in p['stats'][0]['splits'][0]['stat']:
                                p['stats'][0]['splits'][0]['stat']['inningsPitched'] = 0
                            players.append(p)
                if group == 'hitting':
                    players = sorted(players, key = lambda k: k['stats'][0]['splits'][0]['stat']['plateAppearances'], reverse=True)
                elif group == 'pitching':
                    players = sorted(players, key = lambda k: k['stats'][0]['splits'][0]['stat']['inningsPitched'], reverse=True)

        if roster is None:
            names = name.split('/')
            for name in names:
                player = get_player_stats(name, group=group, stattype=stattype, startDate=startDate, endDate=endDate, lastgames=lastgames)
                if player != "Couldn't find player":
                    players.append(player)
                else:
                    return player

        statsstr = _get_multiple_stats_string(players, group=group, include_gp=True, reddit=reddit)
        output = ""
        namesliststr = ""
        if roster is None:
            for player in players:
                namesliststr += "%s, " % player['fullName']
            namesliststr = namesliststr[:-2]
        else:
            print(team)
            namesliststr = team['abbreviation']
        if stattype == "byDateRange":
            print(startDate, endDate)
            output = "%s to %s for %s:\n\n" % (startDate, endDate, namesliststr)
            start = _convert_mlb_date_to_datetime(startDate)
            end = _convert_mlb_date_to_datetime(endDate)
            if len(players) > 1 and start.year != end.year:
                output += "These stats only show the first season in the date range. To get all seasons, search each player individually.\n\n"
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
    # url = API_LINK + "teams/%s" % teamid
    results = utils.get_json(url)
    if len(results['teams']) > 0:
        return results['teams'][0]

def get_player_season_stats(name, type=None, year=None, career=None, reddit=None, milb=False):
    postseason = True if 'postseason' in name else False
    spring = True if 'spring ' in name else False
    if not milb:
        try:
            player = _new_player_search(name, type=type)
            teamid = player['currentTeam']['id']
            # team = get_team_info(teamid)
        except:
            return "Error finding player %s" % name
    else:
        player = mymlbstats.milb_player_search(name)
        player = _get_player_by_id(player["player_id"], milb=True)
    if player is None:
        return "No matching player found"

    #teamabv = player['currentTeam']['abbreviation']
    # pid = player['id']
    disp_name = player['fullName']
    pos = player['primaryPosition']['abbreviation']
    # if milb:
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
                # if 'team' in split:
                if not milb:
                    if 'team' in split:
                        season['team'] = split['team']['abbreviation']
                        teams.append(season['team'])
                    else:
                        season['team'] = "MLB"
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
        if milb:
            stats = ['season', 'team'] + stats
        else:
            stats = ['season', 'team'] + stats
    repl = {'atBats':'ab', 'plateAppearances':'pa','hits':'h','doubles':'2B','triples':'3b','homeRuns':'hr', 'runs':'r', 'baseOnBalls':'bb','strikeOuts':'so', 'stolenBases':'sb', 'caughtStealing':'cs',
            'wins':'w', 'losses':'l', 'gamesPlayed':'g', 'gamesStarted':'gs', 'saveOpportunities':'svo', 'saves':'sv', 'inningsPitched':'ip'}

    stats_type = "season"
    if postseason:
        stats_type = "postseason"
    elif spring:
        stats_type = "spring"
    if year == year2:
        if year == str(now.year) and len(teams) == 0 and 'currentTeam' in player:
            teamabv = player['currentTeam']['abbreviation']
            if player['currentTeam']['sport']['id'] != 1:
                parent = get_team_info(player['currentTeam']['parentOrgId'])
                milb = get_team_info(player['currentTeam']['id'])
                teamabv += " - %s %s" % (parent['abbreviation'], milb['sport']['abbreviation'])
        else:
            teamabv = '/'.join(teams)
        output = "%s %s stats for %s (%s):" % (year, stats_type, disp_name, teamabv)
    else:
        output = "%s-%s %s stats for %s:" % (year, year2, stats_type, disp_name)
    if career:
        output = "Career %s stats for %s (%s):" % (stats_type, disp_name, years)
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
    if 'date' in statquery_list or 'dates' in statquery_list:
        stattype = 'byDateRange'
        if 'date' in statquery_list:
            statquery_list.remove('date')
        elif 'dates' in statquery_list:
            statquery_list.remove('dates')
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

    pool = None
    if "all" in statquery_list:
        pool = "all"
        statquery_list.remove('all')
    elif "rookies" in statquery_list:
        pool = "qualified_rookies"
        statquery_list.remove('rookies')
    elif "qualified" in statquery_list:
        pool = "qualified"
        statquery_list.remove('qualified')

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

    positions = ['c','1b','2b','3b','ss','if','lf','cf','rf','of','p','dh']
    pos = None
    for i in statquery_list:
        if i.lower() in positions:
            pos = i.upper()
            statquery_list.remove(i)

    stat = statquery_list.pop()
    team = None
    if len(statquery_list) > 0:
        team = mymlbstats.get_teamid(' '.join(statquery_list))

    return (league, want_group, pos, team, stat, stattype, date1, date2, pool)

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

def get_sorted_stats(statinfo, season=None, league=None, position=None, teamid=None, teams=False, group=None, reverse=False, stats='season', date1=None, date2=None, pool=None):
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
        inf = ['C','1B','2B','3B','SS']
        if position == 'OF':
            position = ','.join(of)
        elif position == 'IF':
            position = ','.join(inf)
        params['position'] = position
    if teamid is not None:
        params['teamId'] = teamid
    if group is None:
        params['group'] = statinfo['statGroups'][0]['displayName']
    else:
        params['group'] = group
    if reverse:
        params['order'] = 'descending'
    if pool is not None:
        params['playerPool'] = pool

    url += urllib.parse.urlencode(params, safe=',')
    return utils.get_json(url)['stats']

def print_sorted_stats(statquery_list, season=None, reverse=False, delta=None):
    teams = False
    if statquery_list[0] == "teams":
        teams = True

    league, group, position, team, stat, stattype, date1, date2, pool = _get_stats_query_params(statquery_list, delta=delta)
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
                             group=group, reverse=reverse, stats=stattype, date1=date1, date2=date2, pool=pool)
    if len(stats) == 0:
        return "Leaders search query returned an empty list"
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

    rows = list()
    num = 10
    if teams:
        num = 15
    for player in stats['splits']:
        if group == 'hitting' and player['stat']['plateAppearances'] == 0:
            continue
        row = dict()
        row = player['stat']
        row['team'] = player['team']['abbreviation']
        if teams:
            row['name'] = player['team']['teamName']
        else:
            row['name'] = player['player']['fullName']
        row[statinfo['name']] = player['stat'][statname]
        rows.append(row)
        if len(rows) >= num:
            break

    if 'games' in rows[0]:
        gamesplayed = "games"
    else:
        gamesplayed = "gamesPlayed"
    labels = ['team', 'name', gamesplayed, statinfo['name']]
    repl = {'gamesPlayed':'gp', 'atBats':'ab', 'plateAppearances':'pa', 'inningsPitched':'ip', 'games':'g'}
    left = ['team', 'name']

    if group == 'hitting':
        labels.insert(3,'plateAppearances')
    elif group == 'pitching':
        labels.insert(3,'inningsPitched')

    output = ""
    if stattype == 'byDateRange':
        if date1 is None:
            output = "Stats from today\n"
        elif date2 is None:
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

def print_birthdays(team, delta=None, reddit=False):
    birthdays = list()
    if delta is None:
        today = datetime.today()
        todayyear = 2021 # use this until it's actually updated to 2021 i guess
    else:
        today = mymlbstats._get_date_from_delta(delta, offset=False)
    todaystr = "%02d-%02d" % (today.month, today.day)

    if len(team) == 0:
        url = API_LINK + "sports/1/players?fields=id,people,person,firstLastName,birthDate,currentTeam&season=%d" % todayyear
        players = utils.get_json(url)['people']
        teams = dict()
        for player in players:
            if 'birthDate' in player:
                p = dict()
                if player['birthDate'][5:] == todaystr:
                    p['age'] = today.year - int(player['birthDate'][:4])
                    p['name'] = player['firstLastName']
                    curteamid = player['currentTeam']['id']

                    if curteamid in teams:
                        p['team'] = teams[curteamid]['abbreviation']
                        if reddit:
                            p['team'] = "[](/%s)%s" % (p['team'], p['team'])

                    else:
                        teaminfo = get_team_info(curteamid)
                        teams[curteamid] = teaminfo
                        p['team'] = teaminfo['abbreviation']
                        if reddit:
                            p['team'] = "[](/%s)%s" % (p['team'], p['team'])

                    birthdays.append(p)
    else:
        teamid, teamdata = mymlbstats.get_teamid(team, extradata=True)
        if teamid is None:
            return "could not find team"
        roster = get_40man(teamid) + get_coaches(teamid)
        for player in roster:
            if 'birthDate' in player['person']:
                p = dict()
                player = player['person']
                if player['birthDate'][5:] == todaystr:
                    p['age'] = today.year - int(player['birthDate'][:4])
                    p['name'] = player['firstLastName']
                    birthdays.append(p)
    if delta is None:
        todaystr = "today"
    else:
        todaystr = 'on ' + todaystr.replace('-','/')
    if len(birthdays) > 0:
        if len(team) > 0:
            return "%s birthdays %s:\n\n" % (teamdata['teamName'], todaystr) + utils.format_table(['name', 'age'], birthdays, left_list=['name'], reddit=reddit)
        else:
            return "All player birthdays %s:\n\n%s" % (todaystr, utils.format_table(['team','name','age'], birthdays, left_list=['team','name'], reddit=reddit))
         # return "All player birthdays %s:\n\n%s" % (todaystr, utils.format_table(['name','age'], birthdays, left_list=['name'], reddit=reddit))
    else:
        if len(team) > 0:
            return "No %s birthdays on %s" % (teamdata['teamName'], todaystr)
        else:
            return "No birthdays %s" % todaystr

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

    if season is None:
        now = datetime.now()
        season = str(now.year)
    player_info = "%s pitch arsenal for %s (%s)\n\n" % (season, player['fullName'], player['currentTeam']['abbreviation'])

    pitches = get_pitch_arsenal(player['id'], season=season)
    pitches = sorted(pitches, key = lambda k: float(k['percentage']), reverse=True)

    labels = ['description', 'percentage', 'averageSpeed']
    left = ['description']
    repl = {'description':'pitch', 'percentage':'%', 'averageSpeed':'avg mph'}

    return "```python\n%s%s```" % (player_info, utils.format_table(labels, pitches, left_list=left, repl_map=repl, reddit=reddit))

def get_stat_streaks(streak_type, streak_filter="overall", span=None, season=None):
    """
    :param streak_type: hitting, onbase
    :param streak_filter: overall, home, away
    :param span: career, season, currentStreakInSeason, notable, notableInSeason
    :param season:
    :return:
    """
    url = API_LINK + "stats/streaks?"
    params = {'sportId':1, 'limit':10, 'gameType':'R'}
    params['hydrate'] = "person"
    if streak_type == "hitting":
        params['streakType'] = "hittingStreak"
    elif streak_type == "onbase":
        params['streakType'] = "onBase"
    else:
        return None
    if streak_filter is None:
        streak_filter = "overall"
    params['streakType'] += streak_filter.title()

    if span is not None:
        params['streakSpan'] = span
    else:
        if season is None:
            params['streakSpan'] = 'currentStreakInSeason'
        else:
            params['streakSpan'] = 'season'
    if season is not None:
        params['season'] = season
    else:
        now = datetime.now()
        params['season'] = now.year

    return utils.get_json(url+urllib.parse.urlencode(params, safe=','))

def print_stat_streaks(query_list, season=None, reddit=False, redditpost=False):
    streak_type = query_list.pop(0)
    span = None
    filter = None
    filters = ['home', 'away', 'overall']
    for l in query_list:
        if l in filters:
            filter = l
            query_list.remove(l)
            break
    spans = ['career', 'season', 'currentStreak', 'notable', 'notableInSeason']
    for l in query_list:
        if l in spans:
            span = l
            query_list.remove(l)
            break

    streaks = get_stat_streaks(streak_type, streak_filter=filter, span=span, season=season)
    players = list()
    if streaks is not None:
        streaks = streaks['streaks'][:10]
        for streak in streaks:
            stats = streak['stats']
            stats['name'] = streak['player']['boxscoreName']
            stats['team'] = streak['team']['abbreviation']
            if redditpost:
                stats['team'] = "[](/%s)%s" % (stats['team'], stats['team'])
            stats['start'] = streak['startDate'][5:10]
            stats['end'] = streak['endDate'][5:10]
            players.append(stats)
    if redditpost:
        return _print_stats_game_line(players, include_gp=True, include_slash=True, include_start_end=True, reddit=True)
    return "```python\n%s```" %_print_stats_game_line(players, include_gp=True, include_slash=True, include_start_end=True, reddit=reddit)

def _print_stats_game_line(list_of_stats, type='hitting', include_gp=False, include_slash=False, include_start_end=False, reddit=False):
    """
    print stats game-line style:
    [GP] [S E] AB H 2B 3B HR R RBI BB SO SB CS [AVG OBP SLG]
    """
    labels = ['atBats', 'hits', 'doubles', 'triples', 'homeRuns', 'baseOnBalls', 'strikeOuts']
    if 'stolenBases' in list_of_stats[0]:
        labels.append('stolenBases')
    if 'caughtStealing' in list_of_stats[0]:
        labels.append('caughtStealing')
    if include_slash:
        slash = ['avg','obp','slg']
        for s in slash:
            if s in list_of_stats[0]:
                labels.append(s)
    if include_start_end:
        labels.insert(0, 'end')
        labels.insert(0, 'start')
    if include_gp:
        labels.insert(0, 'gamesPlayed')
    if len(list_of_stats) > 1:
        labels.insert(0, 'name')
        labels.insert(0, 'team')

    replace = _get_common_replace_map()
    left = ['name', 'team']
    return utils.format_table(labels, list_of_stats, repl_map=replace, left_list=left, reddit=reddit)

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

def get_schedule(date, endDate=None, teamid=None):
    # if it's a string then it's a delta
    if date is None:
        date = mymlbstats._get_date_from_delta("+0")
    elif isinstance(date, str):
        date = mymlbstats._get_date_from_delta(date)
    d = str(date.year) + "-" + str(date.month).zfill(2) + "-" + str(date.day).zfill(2)
    hydrates = "&hydrate=probablePitcher,person,decisions,team,stats,flags,lineups,linescore(matchup,runners),previousPlay"
    team = ""
    if teamid is not None:
        team = "&teamId=" + str(teamid)
    if endDate is None:
        datestr = "&date=%s" % d
    else:
        enddate_mlbstr = str(endDate.year) + "-" + str(endDate.month).zfill(2) + "-" + str(endDate.day).zfill(2)
        datestr = "&startDate=%s&endDate=%s" % (d, enddate_mlbstr)

    url = "https://statsapi.mlb.com/api/v1/schedule?sportId=1" + team + datestr +  hydrates
    return utils.get_json(url)['dates']

def print_games(args, delta=None):
    lgs = {'alwc':103,'nlwc':104}
    divs = {'nle':204,'nlc':205,'nlw':203,'ale':201,'alc':202,'alw':200}
    if isinstance(args, list):
        args = ' '.join(args)

    all_games = get_schedule(delta)[0]['games']
    games = list()
    add_last_play = False

    if 'close' in args:
        for game in all_games:
            if game['status']['abstractGameCode'] == "L" :
                awayruns = game['linescore']['teams']['away']['runs']
                homeruns = game['linescore']['teams']['home']['runs']
                if game['linescore']['currentInning'] >= 7 and abs(awayruns-homeruns) <= 2:
                    games.append(game)
        if len(games) == 0:
            return "No close (7th inning or later within 2 runs) games at the moment."
    elif 'live' in args:
        for game in all_games:
            if game['status']['abstractGameCode'] == "L":
                games.append(game)
        if len(games) == 0:
            return "No live games at the moment."
    elif args in lgs:
        standings = mymlbstats.get_lg_standings(lgs[args],wc=True)['records'][0]['teamRecords']
        wcteams = []
        for i in range(5):
            wcteams.append(standings[i]['team']['id'])
        for game in all_games:
            away = game['teams']['away']['team']['id']
            home = game['teams']['home']['team']['id']
            if away in wcteams or home in wcteams:
                games.append(game)
    elif args in divs:
        for game in all_games:
            awaydiv = game['teams']['away']['team']['division']['id']
            homediv = game['teams']['home']['team']['division']['id']
            if awaydiv == divs[args] or homediv == divs[args]:
                games.append(game)
        if len(games) == 0:
            return "No games for division found"
    elif len(args) > 0:
        add_last_play = True
        teamid = mymlbstats.get_teamid(args)
        print(teamid)
        if teamid is None:
            return "Could not find team", 0
        else:
            for game in all_games:
                away = game['teams']['away']['team']['id']
                home = game['teams']['home']['team']['id']
                if away == teamid or home == teamid:
                    games.append(game)
            if len(games) == 0:
                return "No games found for %s" % args, 0
            # check doubleheader
            is_dh_live = False
            for game in games:
                if game['doubleHeader'] == "Y" and game['status']['abstractGameCode'] == 'L':
                    is_dh_live = True
            if is_dh_live:
                for game in games:
                    if game['doubleHeader'] == "Y" and game['status']['abstractGameCode'] != 'L':
                        games.remove(game)

    output = ""
    show_on_deck = False
    if len(games) == 0:
        games = all_games
    elif len(games) == 1:
        show_on_deck = True
    for game in games:
        output += mymlbstats.get_single_game_info(game['gamePk'], gamejson=game, show_on_deck=show_on_deck) + "\n"
        if add_last_play:
            output += _add_last_play_info(game)
    return output, len(games)

def print_team_schedule(team, num, forward=True):
    """print next/previous <num> days for a team"""
    teamid = mymlbstats.get_teamid(team)
    if teamid is None:
        return "Could not find team"

    today = mymlbstats._get_date_from_delta("+0")
    plus = "+" if forward else "-"
    date2 = mymlbstats._get_date_from_delta(plus + str(int(num) + 3))
    if forward:
        dates = get_schedule(today, endDate=date2, teamid=teamid)
    else:
        dates = get_schedule(date2, endDate=today, teamid=teamid)

    output = ""
    games = list()
    for date in dates:
        for game in date['games']:
            if 'status' in game:
                code = game['status']['abstractGameCode']
                if forward and code in ['F']:
                    continue
                elif forward and code == 'L' and game['status']['codedGameState'] != 'U':  # suspended
                    continue
                elif not forward and code in ['L', 'P']:
                    continue
            games.append(game)

    if forward:
        games = games[:num]
    else:
        games = games[-num:]

    for game in games:
        date = game['officialDate'][:10]
        dt = datetime.strptime(date, "%Y-%m-%d")
        if today.day-dt.day == 0:
            day = "Today"
        elif not forward:
            if today.day-dt.day == 1:
                day = "Yesterday"
            else:
                day = calendar.day_name[dt.weekday()]
        else:
            if dt.day-today.day == 1:
                day = "Tomorrow"
            else:
                day = calendar.day_name[dt.weekday()]
        output = output + date + " (%s):\n" % (day)
        output += mymlbstats.get_single_game_info(game['gamePk'], gamejson=game) + "\n"

    if len(output) == 0:
        return "no games found"
    else:
        return output

def _add_last_play_info(game):
    output = ""
    gamepk = game['gamePk']
    abstractstatus = game['status']['abstractGameState']
    detailedstatus = game['status']['detailedState']
    if abstractstatus == "Live" and detailedstatus != 'Delayed':
        pbp = mymlbstats.get_pbp(gamepk)
        try:
            if 'description' not in pbp['allPlays'][-1]['result']:
                lastplay = pbp['allPlays'][-2]
            else:
                lastplay = pbp['allPlays'][-1]
            desc = lastplay['result']['description']
            pitch = lastplay['matchup']['pitcher']['fullName']
            if desc.startswith('Pitching Change:'):
                output = output + desc + "\n\n"
            else:
                output = output + "Last Play: With " + pitch + " pitching, " + desc + "\n\n"
            if 'pitchData' in lastplay['playEvents'][-1]:
                data = lastplay['playEvents'][-1]
                output = output + "Pitch: %s, %.02f mph\n" % (data['details']['type']['description'],
                                                              data['pitchData']['startSpeed'])
            if 'hitData' in lastplay['playEvents'][-1]:
                data = lastplay['playEvents'][-1]['hitData']
                output = output + "Statcast: %.02f ft, %.02f mph, %.02f degrees\n\n" % (data['totalDistance'],
                                                                                        data['launchSpeed'],
                                                                                        data['launchAngle'])
        except Exception as e:
            # print("Error in parsing game %d" % gamepk)
            print(e)
    return output

if __name__ == "__main__":
    # get_schedule("-1")
    # print(print_games('wsh'))
    # print(print_games("lad"))
    # print(print_stat_streaks(['hitting'], redditpost=True))
    # print(get_player_season_stats("starling marte"))
    print(_new_player_search("will smith (lad)"))
