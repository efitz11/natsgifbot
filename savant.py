import utils, mymlbstats
from datetime import datetime, timedelta

def find_gamepks(team, delta=None, teamid=None):
    if teamid is None:
        teamid = mymlbstats.get_teamid(team)
    s = mymlbstats.get_day_schedule(delta=delta, teamid=teamid)

    gamepks = []

    games = s['dates'][0]['games']
    for game in games:
        gamepks.append(game['gamePk'])
    return gamepks

def get_game(gamepk):
    url = "https://baseballsavant.mlb.com/gf?game_pk=%s" % str(gamepk)
    return utils.get_json(url)

def get_info_str(game_json):
    home = dict()
    away = dict()
    home['team'] = game_json['home_team_data']['abbreviation']
    away['team'] = game_json['away_team_data']['abbreviation']
    home['r'] = game_json['scoreboard']['linescore']['teams']['home']['runs']
    home['h'] = game_json['scoreboard']['linescore']['teams']['home']['hits']
    home['e'] = game_json['scoreboard']['linescore']['teams']['home']['errors']
    home['lob'] = game_json['scoreboard']['linescore']['teams']['home']['leftOnBase']
    if 'home' in game_json['scoreboard']['stats']['exitVelocity']['xbaTeam']:
        home['xba'] = game_json['scoreboard']['stats']['exitVelocity']['xbaTeam']['home']['xba']
    away['r'] = game_json['scoreboard']['linescore']['teams']['away']['runs']
    away['h'] = game_json['scoreboard']['linescore']['teams']['away']['hits']
    away['e'] = game_json['scoreboard']['linescore']['teams']['away']['errors']
    away['lob'] = game_json['scoreboard']['linescore']['teams']['away']['leftOnBase']
    away['xba'] = game_json['scoreboard']['stats']['exitVelocity']['xbaTeam']['away']['xba']
    if len(game_json['scoreboard']['stats']['wpa']['gameWpa']) > 0:
        home['wp'] = round(game_json['scoreboard']['stats']['wpa']['gameWpa'][-1]['homeTeamWinProbability'], 2)
        away['wp'] = round(game_json['scoreboard']['stats']['wpa']['gameWpa'][-1]['awayTeamWinProbability'], 2)

    cols = ['team','r','h','e','lob','xba','wp']
    left = ['team']
    dicts = [away, home]

    # WPA leaders
    lastplays = game_json['scoreboard']['stats']['wpa']['lastPlays']
    for p in lastplays:
        p['wpa'] = round(p['wpa'], 2)
    topwpa = game_json['scoreboard']['stats']['wpa']['topWpaPlayers']
    for i in range(len(topwpa)):
        lastplays[i]['top_name'] = topwpa[i]['name']
        lastplays[i]['topwpa'] = round(topwpa[i]['wpa'], 2)
        lastplays[i]['space'] = ' | '
    labs = ['name', 'wpa', 'space', 'top_name', 'topwpa']
    repl_map = {'name':'Last 3 WPA', 'wpa':'', 'top_name':'WPA Leaders','topwpa':'','space':''}

    return (utils.format_table(cols,dicts,left_list=left),
            utils.format_table(labs, lastplays, left_list=['name','top_name'], repl_map=repl_map))

def get_last_five(game_json):
    ev = game_json['exit_velocity']
    events = []
    for event in ev[-5:]:
        events.append(event)
    events.reverse()

    cols = ['batter_name', 'result','hit_speed','hit_distance','hit_angle','xba']
    repl = {'batter_name':'last bb','hit_speed':'EV','hit_distance':'dist','hit_angle':'LA'}
    left = ['batter_name', 'result']
    return "```python\n%s```" % utils.format_table(cols,events,repl_map=repl,left_list=left)

def get_top_five(game_json):
    ev = game_json['exit_velocity']
    ev = sorted(ev, key=lambda k: float(k['hit_speed']), reverse=True)[:5]
    # for event in ev:
    #     events.append(event)
    # events.reverse()

    cols = ['batter_name', 'result','hit_speed','hit_distance','hit_angle','xba']
    repl = {'batter_name':'Top EV','hit_speed':'EV','hit_distance':'dist','hit_angle':'LA'}
    left = ['batter_name', 'result']
    return "```python\n%s```" % utils.format_table(cols,ev,repl_map=repl,left_list=left)

def get_five(game_json):
    info = get_info_str(game_json)
    output = "```python\n%s```" % info[0]
    output = output + "```python\n%s```" % info[1]
    if game_json['scoreboard']['status']['statusCode'] == 'F':
        output = output + get_top_five(game_json)
    else:
        output = output + get_last_five(game_json)
    return output

def get_player(game_json, playerid):
    ev = game_json['exit_velocity']
    events = []
    for e in ev:
        if e['batter'] == playerid:
            events.append(e)

    cols = ['inning','batter_name', 'result','hit_speed','hit_distance','hit_angle','xba']
    repl = {'inning':'inn','batter_name':'batter','hit_speed':'EV','hit_distance':'dist','hit_angle':'LA'}
    left = ['batter_name', 'result']
    output = "```python\n%s```" % utils.format_table(cols,events,repl_map=repl,left_list=left)
    return output

def print_last_five_batters(team, delta=None):
    return get_last_five(get_game(find_gamepks(team, delta=delta)[0]))

def print_player_abs(player, delta=None):
    p = mymlbstats._get_player_search(player)
    if p is None:
        return "No matching player found"
    teamid = int(p['team_id'])
    return get_player(get_game(find_gamepks(None,teamid=teamid, delta=delta)[0]), int(p['player_id']))

def print_player_or_team(query, delta=None):
    teamid = mymlbstats.get_teamid(query)
    if teamid is None:
        p = mymlbstats._get_player_search(query)
        if p is None:
            return "Query did not match team or player"
        teamid = int(p['team_id'])
        return get_player(get_game(find_gamepks(None, teamid=teamid, delta=delta)[0]), int(p['player_id']))
    else:
        return get_five(get_game(find_gamepks(None, teamid=teamid, delta=delta)[0]))

def get_oaa_leaders(year=None):
    now = datetime.now()
    if year is None:
        year = now.year
    url = "https://baseballsavant.mlb.com/outs_above_average?type=player&year=%s&min=q&csv=true" % (str(year))
    players = utils.csv_to_dicts(url)[:10]
    cols = ['last_name', 'name_abbrev','oaa']
    replace = {'last_name':'player', 'name_abbrev':'team'}
    left = ['last_name','name_abbrev']
    return "```python\n%s```" % utils.format_table(cols, players,repl_map=replace, left_list=left)

if __name__ == "__main__":
    # print(find_gamepks('wsh'))
    # print(print_player_abs("soto"))
    # print(get_last_five(get_game(find_gamepks('wsh')[0])))
    print(print_player_or_team("col"))
    # print(get_oaa_leaders())