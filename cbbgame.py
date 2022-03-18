from urllib.request import urlopen, Request
import time, json,html
from datetime import datetime, timedelta
import odds
'''
borrowed some code from /r/cfb's IRC bot, thank you
https://github.com/diagonalfish/FootballBotX2
'''


#Constants
MODE_ACTIVE = 0
MODE_INACTIVE = 1
GAME_STATUS_PRE = 0
GAME_STATUS_IN = 1
GAME_STATUS_POST = 2

LINE_SEP = "──────────────────────────────────────"

base_url = "http://espn.go.com/mens-college-basketball/scoreboard/_/"

TYPE = "50"
# Other leagues go here

groupmap = {
            "atlantic 10":"3", "a10":"3",
            "asun":"46","a-sun":"46",
            "acc":"2", 
            "am-east":"1","ameast":"1",
            "american":"62", "aac":"62",
            "big 12":"8", 
            "big east":"4",
            "big sky":"5",
            "big south":"6",
            "big ten":"7", "big 10":"7",
            "big west":"9",
            "c-usa":"11", "cusa":"11",
            "caa":"10",
            "horizon":"45",
            "ivy":"12",
            "maac":"13",
            "mac":"14",
            "meac":"16",
            "mvc":"18",
            "mw":"44",
            "nec":"19",
            "ovc":"20",
            "pac 12":"21", "pac-12":"21",
            "patriot":"22",
            "sec":"23",
            "swac":"26",
            "southern":"24",
            "southland":"25",
            "summit":"49",
            "sun belt":"27",
            "wac":"30",
            "wcc":"29"}

def get_game(team,delta=None,runagain=True,type=TYPE,liveonly=False):
    if team == "conferences":
        output = ""
        for t in groupmap:
            output = output + t + ", "
        return output
        
    now = datetime.now()
    
    all = False
    if delta is not None:
        now = now + timedelta(days=delta)
        url = base_url + "group/" + type + "/date/"+ str(now.year) + str(now.month).zfill(2) + str(now.day).zfill(2)
        if team is None or team.lower() == "none" or team.lower() == "all":
            all = True
            url = base_url + "date/"+ str(now.year) + str(now.month).zfill(2) + str(now.day).zfill(2)
        elif team.lower() in groupmap:
            group = groupmap[team.lower()]
            url = base_url + "group/" + group + "/date/"+ str(now.year) + str(now.month).zfill(2) + str(now.day).zfill(2)
            all = True 
    else:        
        url = "http://espn.go.com/mens-college-basketball/scoreboard/_/group/" + type + "/year/"+str(now.year)+"/seasontype/2/?t=" + str(time.time())
        if team == None or team == "" or team.lower() == "none":
            url = "http://www.espn.com/mens-college-basketball/scoreboard/_/year/" + str(now.year)+"/seasontype/2"
            all = True
        elif team.lower() in groupmap:
            url = "http://www.espn.com/mens-college-basketball/scoreboard/_/group/" + groupmap[team.lower()] + "/year/"+str(now.year)+"/seasontype/2/"
            all = True

    # for printing a team's odds
    if not all and team.startswith("odds"):
        team = team[4:].strip()
        if len(team) == 0:
            return "cbb team is required"
        ret = odds.get_odds_pp("cbb", team=team)
        if '#' in ret:
            return "```%s```" % ret
        else:
            return "```python\n%s```" % ret

    print(url)
    req = Request(url)
    req.headers["User-Agent"] = "windows 10 bot"
    # Load data
    scoreData = urlopen(req).read().decode("utf-8")
    scoreData = scoreData[scoreData.find('window[\'__espnfitt__\']=')+len('window[\'__espnfitt__\']='):]
    scoreData = json.loads(scoreData[:scoreData.find('};')+1])['page']['content']['scoreboard']
    # print(scoreData)
    #f = open('espnout.txt','w')
    #f.write(json.dumps(scoreData))
    #f.close()

    games = []
    if delta is None:
        try:
            date = scoreData['evts'][0]['date']
        except IndexError:
            if runagain:
                return get_game(team, delta, runagain=False, type="100")
        date = date[:date.find('T')].split('-')
        date = date[1] + "/" + date[2] + "/" + date[0]
    else:
        date = str(now.month) + "/" + str(now.day) + "/" + str(now.year)
    for event in scoreData['evts']:
        game = dict()

        game["date"] = event['date']
        status = event['status']['state']
        game['odds'] = ""
        if liveonly and status != "in":
            continue
        if status == "pre":
            game['status'] = GAME_STATUS_PRE
            game['time'] = event['status']['detail']

            if 'odds' in event:
                game['odds'] = " - " + event['odds'].get('details', 'no odds')
        elif status == "in":
            game['status'] = GAME_STATUS_IN
            game['time'] = event['status']['detail']
        else:
            game['status'] = GAME_STATUS_POST
            game['time'] = "FINAL"
        team1 = html.unescape(event['competitors'][0]['location'])
        tid1 = event['competitors'][0]['id']
        score1 = event['competitors'][0].get('score','')
        team1abv = event['competitors'][0]['abbrev']
        team2 = html.unescape(event['competitors'][1]['location'])
        tid2 = event['competitors'][1]['id']
        score2 = event['competitors'][1].get('score','')
        try:
            team2abv = event['competitors'][1]['abbrev']
        except KeyError:
            continue

        rank1 = event['competitors'][0].get('rank','')
        rank2 = event['competitors'][1].get('rank','')

        # Hawaii workaround
        if team1 == "Hawai'i":
            team1 = "Hawaii"
        if team2 == "Hawai'i":
            team2 = "Hawaii"
            
        homestatus = 'home' if event['competitors'][0]['isHome'] else 'away'
        game['link'] = "https://espn.com" + event['link']
        game['broadcast'] = ""
        for b in event['broadcasts']:
            if b['market'] == 'National':
                game['broadcast'] = " - " + b['name']
                break

        if homestatus == 'home':
            game['hometeam'], game['homeid'], game['homeabv'], game['homescore'], game['awayteam'], game['awayid'], game['awayabv'], game['awayscore'], game['homerank'], game['awayrank']=\
                team1, tid1, team1abv, score1, team2, tid2, team2abv, score2, rank1, rank2
        else:
            game['hometeam'], game['homeid'], game['homeabv'], game['homescore'], game['awayteam'], game['awayid'], game['awayabv'], game['awayscore'], game['homerank'], game['awayrank'] = \
                team2, tid2, team2abv, score2, team1, tid1, team1abv, score1, rank2, rank1
            
        #print (game)
        games.append(game)
    #output = "Games on " + str(now.month) + "/" + str(now.day) + "/" + str(now.year)
    dateline = "Games on " + date
    if all:
        output = ""
        for game in games:
            ar = game['awayrank']['current']
            hr = game['homerank']['current']
            awayr = "("+str(ar)+")" if (ar <= 25 and ar > 0) else ""
            homer = "("+str(hr)+")" if (hr <= 25 and hr > 0) else ""
            if len(games) >= 10:
                output = output + "%s %s %s @ %s %s %s # %s%s%s\n" % (awayr.rjust(4),game['awayabv'].rjust(5), game['awayscore'].rjust(2), homer.rjust(4),game['homeabv'].rjust(5), game['homescore'].rjust(2), game['time'],game['broadcast'],game['odds'])
            else:
                output = output + pretty_print_game(game)
                if game != games[-1] :
                    output = "%s%s\n" % (output, LINE_SEP)
        return dateline + "\n```python\n" + output+"```"

    for game in games:
        if game['hometeam'].lower() == team.lower() or game['homeabv'].lower() == team.lower() or game['awayteam'].lower() == team.lower() or game['awayabv'].lower() == team.lower():
            # ar = game['awayrank']['current']
            # hr = game['homerank']['current']
            # awayr = "("+str(ar)+")" if (ar <= 25 and ar > 0) else ""
            # homer = "("+str(hr)+")" if (hr <= 25 and hr > 0) else ""
            # return output + "\n```python\n%s%s %s @ %s%s %s # %s%s```" % (awayr,game['awayabv'], game['awayscore'], homer,game['homeabv'], game['homescore'], game['time'], game['odds'])
            output = pretty_print_game(game)
            if 'link' in game:
                link = "<" + game['link'] + ">"
            else:
                link = ""
            return (dateline + " - " + link + "\n```python\n" + output + "```")
    if runagain:
        return get_game(team, delta, runagain=False, type="100")
    return "game not found"

def pretty_print_game(game):
    ar = game['awayrank']
    hr = game['homerank']
    awayr = "("+str(ar)+")" if (ar <= 25 and ar > 0) else ""
    homer = "("+str(hr)+")" if (hr <= 25 and hr > 0) else ""
    namejust = max(len(game['awayabv']), len(game['homeabv']))
    if '-' in game['time']:
        gdate = game['time'].split('-')[0]
        gtime = game['time'].split('- ')[1]
    else:
        gdate = ""
        gtime = game['time']
    game['awayscore'] = str(game['awayscore'])
    game['homescore'] = str(game['homescore'])
    output = "%s %s %s # %s\n%s %s %s # %s%s%s\n" % (awayr.rjust(4),game['awayabv'].rjust(namejust), game['awayscore'].rjust(2), gdate, homer.rjust(4),game['homeabv'].rjust(namejust), game['homescore'].rjust(2), gtime, game['broadcast'], game['odds'])
    return output
    
def pretty_print_games(games):
    started = []
    pregame = []
    final = []
    for game in games:
        if game['status'] == GAME_STATUS_PRE:
            started.append(game)
        else:
            pregame.append(game)

if __name__ == "__main__":
    print(get_game("md"))
