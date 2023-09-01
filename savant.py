import loosejson, json
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
    teamid = int(p['currentTeam']['id'])
    return get_player(get_game(find_gamepks(None,teamid=teamid, delta=delta)[0]), int(p['id']))

def print_player_or_team(query, delta=None):
    teamid = mymlbstats.get_teamid(query)
    if teamid is None:
        p = mymlbstats._get_player_search(query)
        if p is None:
            return "Query did not match team or player"
        teamid = int(p['currentTeam']['id'])
        return get_player(get_game(find_gamepks(None, teamid=teamid, delta=delta)[0]), int(p['id']))
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

def get_player_savant_json():
    with open("test/fake.json", 'r') as f:
        fixed = loosejson.parse_loosely_defined_json(f.read())
        return fixed

def get_player_savant_stats(player):
    p = mymlbstats._get_player_search(player)
    if p is None:
        return "No matching player found"
    url = f"https://baseballsavant.mlb.com/savant-player/{p['id']}"
    page = utils.get_page(url)
    page = page[page.rfind("var serverVals = {"):]
    page = page[page.find('{'):page.rfind("};\n")+1]
    return loosejson.parse_loosely_defined_json(page)

def print_savant_advanced_stats(savant_json, year=None, reddit=None):
    type = None
    print(json.dumps(savant_json['statcast'], indent=2))
    if savant_json['statcast'][0]['grouping_cat'] == "Batter":
        labels = ['ba','xba','woba','xwoba','wobadiff','bb_percent','k_percent']
        type = "batting"
    elif savant_json['statcast'][0]['grouping_cat'] == "Pitcher":
        labels = ['woba','xwoba','wobadiff','bb_percent','k_percent','era','xera']
        type = "pitching"
    if type is None:
        return "Error getting advanced stats"

    repls = {'bb_percent':'bb%','k_percent':'k%'}
    this_year = datetime.now().year
    stats = None
    if year is None:
        year = this_year
        for year_entry in savant_json['statcast']:
            if year_entry['aggregate'] == "0" and this_year == int(year_entry['year']):
                stats = [year_entry]
    else:
        if '-' in year:
            startyear, stopyear = year.split('-')
            labels.insert(0,'year')
        else:
            startyear, stopyear = year, year
        startyear = int(startyear)
        stopyear = int(stopyear)
        stats = list()
        for year_entry in savant_json['statcast']:
            if year_entry['aggregate'] == "0" and \
                int(year_entry['year']) >= startyear and \
                int(year_entry['year']) <= stopyear:
                stats.append(year_entry)

    player_line = f"{year} {type} advanced stats for {savant_json['playerName']}"
    if stats is None:
        return "Cannot find year in stats"

    return "```python\n%s\n\n%s```" % (player_line, utils.format_table(labels, stats, repl_map=repls, reddit=reddit))

def print_player_advanced_stats(player, year=None, reddit=None):
    return print_savant_advanced_stats(get_player_savant_stats(player), year=year, reddit=reddit)

def print_player_rankings(player, year=None):
    savant_json = get_player_savant_stats(player)
    type = savant_json['statcast'][0]['grouping_cat']
    stats = None
    if type == "Pitcher":
        stats = ["percent_rank_exit_velocity_avg",
                 "percent_rank_launch_angle_avg",
                 "percent_rank_barrel_batted_rate",
                 "percent_rank_xwoba",
                 "percent_rank_xera",
                 "percent_rank_k_percent",
                 "percent_rank_bb_percent",
                 "percent_rank_chase_percent",
                 "percent_rank_groundballs_percent",
                 "percent_rank_whiff_percent",
                 "percent_rank_pitch_run_value_fastball",
                 "percent_rank_pitch_run_value_breaking",
                 "percent_rank_pitch_run_value_offspeed"
                 ]
    elif type == "Batter":
        stats = ["percent_rank_exit_velocity_avg",
                 "percent_rank_barrel_batted_rate",
                 "percent_rank_xwoba",
                 "percent_rank_xba",
                 "percent_rank_k_percent",
                 "percent_rank_bb_percent",
                 "percent_rank_chase_percent",
                 "percent_rank_whiff_percent",
                 "percent_rank_sprint_speed",
                 "percent_speed_order",
                 "percent_rank_oaa",
                 "percent_rank_fielding_run_value",
                 "percent_rank_swing_take_run_value",
                 "percent_rank_runner_run_value",
                 "percent_rank_framing"]
    if stats is None:
        return "error getting player rankings"
    if year is None:
        year = datetime.now().year
    stats_dict = None
    for year_stats in savant_json['statcast']:
        if year_stats['aggregate'] == "0" and int(year) == int(year_stats['year']):
            stats_dict = year_stats
    if stats_dict is None:
        return f"No stats for {year}"
    # build dict for table
    table_rows = list()
    for stat in stats:
        if stat in stats_dict and stats_dict[stat] is not None:
            d = dict()
            d['stat'] = stat.replace("percent_rank_", "").replace("percent_speed_order","sprint_speed")
            d['stat'] = d['stat'].replace("swing_take","batting")
            d['value'] = int(stats_dict[stat])
            table_rows.append(d)
    # sort by value (desc)
    table_rows = sorted(table_rows, key=lambda i: i["value"], reverse=True)
    player_line = f"{year} {type} percentile rankings for {savant_json['playerName']}"
    table_output = utils.format_table(['stat','value'], table_rows, showlabels=False)
    return f"```python\n{player_line}\n\n{table_output}```"

if __name__ == "__main__":
    # print(find_gamepks('wsh'))
    # print(print_player_abs("soto"))
    # print(get_last_five(get_game(find_gamepks('wsh')[0])))
    # print(print_player_or_team("col"))
    # print(get_oaa_leaders())
    # print(print_savant_advanced_stats(get_player_savant_json(),year="2016-2021"))
    # print(print_savant_advanced_stats(get_player_savant_stats("josh bell")))
    # print(print_player_advanced_stats("juan soto"))
    print(print_player_rankings("juan soto"))
