from urllib.request import urlopen, Request
from datetime import datetime, timedelta
import json, os

def get_schedule():
    now = datetime.now() - timedelta(hours=5)
    date = str(now.year) + "-" + str(now.month).zfill(2) + "-" + str(now.day).zfill(2)
    schd = "mlb" + os.sep + date + ".txt"
    return schd

def make_mlb_schedule(date=None):
    if date is None:
        now = datetime.now() - timedelta(hours=5)
        date = str(now.year) + "-" + str(now.month).zfill(2) + "-" + str(now.day).zfill(2)
    schd = "mlb" + os.sep + date + ".txt"
    if not os.path.isfile(schd):
        teams = []
        with open('mlb/teams.txt','r') as f:
            for line in f:
                teams.append(line.strip().split(','))

        print(teams)
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

def get_all_game_info():
    now = datetime.now() - timedelta(hours=5)
    date = str(now.year) + "-" + str(now.month).zfill(2) + "-" + str(now.day).zfill(2)
    url = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=" + date
    req = Request(url, headers={'User-Agent' : "ubuntu"})
    s = json.loads(urlopen(req).read().decode("utf-8"))
    games = s['dates'][0]['games']
    for game in games:
        awayteam = game['teams']['away']['name']
        hometeam = game['teams']['home']['name']

def get_single_game(team):
    schd = get_schedule()
    game = ""
    with open(schd,'r') as f:
        for line in f:
            if team.lower() in line.lower():
                game = line.split(' ')[0]
    print(game)
    #if game != "":


if __name__ == "__main__":
    make_mlb_schedule()
    #get_mlb_teams()
    #get_single_game("phi")
