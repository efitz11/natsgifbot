from urllib.request import urlopen, Request
import urllib
import json
import utils, mymlbstats

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

def get_last_five(game_json):
    ev = game_json['exit_velocity']
    events = []
    for i in range(1, min(len(ev), 6)):
        idx = -i
        events.append(ev[idx])

    cols = ['batter_name', 'result','hit_speed','hit_distance','hit_angle','xba']
    repl = {'batter_name':'batter','hit_speed':'EV','hit_distance':'dist','hit_angle':'LA'}
    left = ['batter_name', 'result']
    output = "```python\n%s```" % utils.format_table(cols,events,repl_map=repl,left_list=left)
    return output

def get_player(game_json, playerid):
    ev = game_json['exit_velocity']
    events = []
    for e in ev:
        if e['batter'] == playerid:
            events.append(e)

    cols = ['batter_name', 'result','hit_speed','hit_distance','hit_angle','xba']
    repl = {'batter_name':'batter','hit_speed':'EV','hit_distance':'dist','hit_angle':'LA'}
    left = ['batter_name', 'result']
    output = "```python\n%s```" % utils.format_table(cols,events,repl_map=repl,left_list=left)
    return output

def print_last_five_batters(team, delta=None):
    return get_last_five(get_game(find_gamepks(team, delta=delta)[0]))

def print_player_abs(player):
    p = mymlbstats._get_player_search(player)
    if p is None:
        return "No matching player found"
    teamid = int(p['team_id'])
    return get_player(get_game(find_gamepks(None,teamid=teamid)[0]), int(p['player_id']))

if __name__ == "__main__":
    # print(find_gamepks('wsh'))
    print(print_player_abs("soto"))
    # print(get_last_five(get_game(find_gamepks('wsh')[0])))
