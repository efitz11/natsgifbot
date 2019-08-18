from urllib.request import urlopen, Request
import urllib
import json
import utils, mymlbstats

def find_gamepks(team, delta=None):
    teamid = mymlbstats.get_teamid(team)
    s = mymlbstats.get_day_schedule(delta=delta, teamid=teamid)

    gamepks = []

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
            gamepks.append(game['gamePk'])
    return gamepks

def get_game(gamepk):
    url = "https://baseballsavant.mlb.com/gf?game_pk=%s" % str(gamepk)
    return utils.get_json(url)

def get_last_five(game_json):
    ev = game_json['exit_velocity']
    events = []
    for i in range(1,6):
        idx = -i
        events.append(ev[idx])

    cols = ['batter_name', 'result','hit_speed','hit_distance','hit_angle','xba']
    repl = {'batter_name':'batter','hit_speed':'EV','hit_distance':'dist','hit_angle':'LA'}
    left = ['batter_name', 'result']
    output = "```python\n%s```" % utils.format_table(cols,events,repl_map=repl,left_list=left)
    return output

def print_last_five_batters(team, delta=None):
    return get_last_five(get_game(find_gamepks(team, delta=delta)[0]))

if __name__ == "__main__":
    # print(find_gamepks('wsh'))
    print(get_last_five(get_game(find_gamepks('wsh')[0])))
