from urllib.request import urlopen, Request
import time, json,html
from datetime import datetime
import utils
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

type = "80" # 80 = FBS
# Other leagues go here

groupmap = {"acc":"1", 
            "american":"151", "aac":"151",
            "big 12":"4", 
            "big ten":"5", "big 10":"5",
            "c-usa":"12", "cusa":"12",
            "independent":"18","indep":"18",
            "mac":"15",
            "mw":"17",
            "pac 12":"9", "pac-12":"9",
            "sec":"8",
            "sun belt":"37",
            "big south":"40",
            "caa":"48",
            "ivy":"22",
            "meac":"24",
            "mvfc":"21",
            "nec":"25",
            "ovc":"26",
            "patriot":"27",
            "pioneer":"28",
            "swac":"31",
            "southern":"29",
            "southland":"30"}

def get_game(team, delta=0,fcs=False):
    if team == "conferences":
        output = ""
        for t in groupmap:
            output = output + t + ", "
        return output

    seasontype = "2"
    now = datetime.now()
    year = now.year
    if (now.month == 12 and now.day > 20) or (now.month == 1):
        seasontype = "3"
        if now.month == 1:
            year = now.year-1
    week2 = datetime(2020,9,8)
    week = int(2 + (now - week2).days/7 + delta)

    # url = "http://espn.go.com/college-football/scoreboard/_/group/" + type + "/year/"+str(year)+"/seasontype/"+seasontype+"/?t=" + str(time.time())
    url = "http://espn.go.com/college-football/scoreboard/_/group/" + type + "/year/"+str(year)+"/seasontype/"+seasontype
    all = False
    conf = False
    if team == None or team == "":
        url = "http://www.espn.com/college-football/scoreboard/_/year/" + str(year)+"/seasontype/"+seasontype
        all = True
    elif fcs:
        url = "http://www.espn.com/college-football/scoreboard/_/group/81/year/"+str(year)+"/seasontype/"+seasontype
    elif team.lower() in groupmap:
        url = "http://www.espn.com/college-football/scoreboard/_/group/" + groupmap[team.lower()] + "/year/"+str(year)+"/seasontype/"+seasontype
        # all = True
        conf = True

    if delta != 0:
        url = url + "/week/" + str(week)
    url = url + "/?t=" + str(time.time())

    print(url)
    req = Request(url)
    req.headers["User-Agent"] = "windows 10 bot"
    # Load data
    scoreData = urlopen(req).read().decode("utf-8")
    # searchstr = 'window.espn.scoreboardData 	= '
    searchstr = "window['__espnfitt__']="
    scoreData = scoreData[scoreData.find(searchstr)+len(searchstr):]
    scoreData = scoreData[:scoreData.find('};')+1]
    # scoreData = scoreData[scoreData.find('window.espn.scoreboardData 	= ')+len('window.espn.scoreboardData 	= '):]
    with open("espnout.txt", 'w') as f:
        f.write(scoreData)
    scoreData = json.loads(scoreData)['page']['content']['scoreboard']
    # print(scoreData)
    # f = open('espnout.txt','w')
    # f.write(json.dumps(scoreData))
    # f.close()

    if conf:
        return "```python\n%s\n```" % get_game_str(scoreData)
    if not all:
        return "```python\n%s\n```" % get_game_str(scoreData, team=team)

    games = []
    # for event in scoreData['events']:
    for event in scoreData['evts']:
        game = dict()

        game["date"] = event['date']
        # status = event['status']['type']['state']
        status = event['status']['state']
        if status == "pre":
            game['status'] = GAME_STATUS_PRE
            # game['time'] = event['status']['type']['shortDetail']
            game['time'] = event['status']['detail']
        elif status == "in":
            game['status'] = GAME_STATUS_IN
            # game['time'] = event['status']['type']['shortDetail']
            game['time'] = event['status']['detail']
        else:
            game['status'] = GAME_STATUS_POST
            game['time'] = "FINAL"
        # team1 = html.unescape(event['competitions'][0]['competitors'][0]['team']['location'])
        # tid1 = event['competitions'][0]['competitors'][0]['id']
        # score1 = event['competitions'][0]['competitors'][0]['score']
        # team1abv = event['competitions'][0]['competitors'][0]['team']['abbreviation']
        # team2 = html.unescape(event['competitions'][0]['competitors'][1]['team']['location'])
        # tid2 = event['competitions'][0]['competitors'][1]['id']
        # score2 = event['competitions'][0]['competitors'][1]['score']
        # team2abv = event['competitions'][0]['competitors'][1]['team']['abbreviation']
        team1 = html.unescape(event['competitors'][0]['location'])
        tid1 = event['competitors'][0]['id']
        if 'score' in event['competitors'][0]:
            score1 = str(event['competitors'][0]['score'])
            score2 = str(event['competitors'][1]['score'])
        else:
            score1 = ""
            score2 = ""
        team1abv = event['competitors'][0]['abbrev']
        team2 = html.unescape(event['competitors'][1]['location'])
        tid2 = event['competitors'][1]['id']
        team2abv = event['competitors'][1]['abbrev']
        
        # rank1 = event['competitors'][0]['curatedRank']
        # rank2 = event['competitors'][1]['curatedRank']
        rank1 = event['competitors'][0]['rank']
        rank2 = event['competitors'][1]['rank']
        
        game['odds'] = ""
        if 'odds' in event:
            if 'details' in event['odds']:
                game['odds'] = " - " + event['odds']['details']
        
        # Hawaii workaround
        if team1 == "Hawai'i":
            team1 = "Hawaii"
        if team2 == "Hawai'i":
            team2 = "Hawaii"
            
        # homestatus = event['competitions'][0]['competitors'][0]['homeAway']
        homestatus = event['competitors'][0]['isHome']
        
        if homestatus == 'home':
            game['hometeam'], game['homeid'], game['homeabv'], game['homescore'], game['awayteam'], game['awayid'], game['awayabv'], game['awayscore'], game['homerank'], game['awayrank']=\
                team1, tid1, team1abv, score1, team2, tid2, team2abv, score2, rank1, rank2
        else:
            game['hometeam'], game['homeid'], game['homeabv'], game['homescore'], game['awayteam'], game['awayid'], game['awayabv'], game['awayscore'], game['homerank'], game['awayrank'] = \
                team2, tid2, team2abv, score2, team1, tid1, team1abv, score1, rank2, rank1
            
        #print (game)
        games.append(game)
    if all:
        output = "```python\n"
        for game in games:
            # awayr = "("+str(game['awayrank']['current'])+")" if game['awayrank']['current'] <= 25 else ""
            # homer = "("+str(game['homerank']['current'])+")" if game['homerank']['current'] <= 25 else ""
            awayr = "("+str(game['awayrank'])+")" if game['awayrank'] <= 25 else ""
            homer = "("+str(game['homerank'])+")" if game['homerank'] <= 25 else ""
            output = output +  "%s %s %s @ %s %s %s # %s%s\n" % (awayr.rjust(4),game['awayabv'].ljust(5), game['awayscore'].rjust(2), homer.rjust(4),game['homeabv'].ljust(5), game['homescore'].rjust(2), game['time'],game['odds'])
        return (output+"```")
    for game in games:
        if game['hometeam'].lower() == team.lower() or game['homeabv'].lower() == team.lower() or game['awayteam'].lower() == team.lower() or game['awayabv'].lower() == team.lower():
            # awayr = "("+str(game['awayrank']['current'])+") " if game['awayrank']['current'] <= 25 else ""
            # homer = "("+str(game['homerank']['current'])+") " if game['homerank']['current'] <= 25 else ""
            awayr = "("+str(game['awayrank'])+")" if game['awayrank'] <= 25 else ""
            homer = "("+str(game['homerank'])+")" if game['homerank'] <= 25 else ""
            return "```python\n%s%s %s @ %s%s %s # %s%s```" % (awayr,game['awayabv'], game['awayscore'], homer,game['homeabv'], game['homescore'], game['time'], game['odds'])
    return "game not found"

def _fix_rank(rank):
    """erases rank if >25 and returns a string"""
    if rank > 25:
        return ""
    else:
        return "(%d)" % rank

def _add_linescores(d, teamjson):
    if 'linescores' in teamjson:
        count = 1
        for score in teamjson['linescores']:
            letter = 'q'
            if count > 4:
                letter = 'o'
            d[letter + str(count)] = score['value']
            count += 1
    return d

def _add_linescores_side(d, quarters):
    count = 1
    for quarter in quarters:
        letter = 'q'
        if count > 4:
            letter = 'o'
        d[letter + str(count)] = quarter
        count += 1
    return d


def get_game_str(scoreData, team=None):
    output = ""
    teamlistpre = []
    teamlistin = []
    teamlistpost = []
    longest_qtr = 0 # number of quarters in the longest game so far
    for event in scoreData['evts']:
        # teams = [html.unescape(event['competitions'][0]['competitors'][0]['team']['location']).lower(),
                 # html.unescape(event['competitions'][0]['competitors'][1]['team']['location']).lower(),
                 # event['competitions'][0]['competitors'][0]['team']['abbreviation'].lower(),
                 # event['competitions'][0]['competitors'][1]['team']['abbreviation'].lower()]
        teams = [html.unescape(event['competitors'][0]['location']).lower(),
                 html.unescape(event['competitors'][1]['location']).lower(),
                 event['competitors'][0]['abbrev'].lower(),
                 event['competitors'][1]['abbrev'].lower()]
        teams = [t.replace("hawai'i","hawaii") for t in teams]
        if team is not None:
            team = team.lower()
        if team is None or team in teams:
            away = dict()
            home = dict()

            # game = event['competitions'][0]
            game = event
            # if game['competitors'][0]['isHome'] == 'away':
            if not game['competitors'][0]['isHome']:
                awayjson = game['competitors'][0]
                homejson = game['competitors'][1]
                away['name'], home['name'] = teams[0], teams[1]
                away['abv'], home['abv'] = teams[2].upper(), teams[3].upper()
            else:
                awayjson = game['competitors'][1]
                homejson = game['competitors'][0]
                away['name'], home['name'] = teams[1], teams[0]
                away['abv'], home['abv'] = teams[3].upper(), teams[2].upper()

            away['id'], home['id'] = awayjson['id'], homejson['id']
            # away['rank'], home['rank'] = _fix_rank(awayjson['curatedRank']['current']), _fix_rank(homejson['curatedRank']['current'])
            away['rank'], home['rank'] = _fix_rank(awayjson['rank']), _fix_rank(homejson['rank'])

            if 'lnescrs' in game:
                away = _add_linescores_side(away, game['lnescrs']['awy'])
                home = _add_linescores_side(home, game['lnescrs']['hme'])
            # away = _add_linescores(away, awayjson)
            # home = _add_linescores(home, homejson)
            # if 'score' in away:
            if 'score' in awayjson:
                away['score'] = awayjson['score']
                home['score'] = homejson['score']
            else:
                away['score'] = ""
                home['score'] = ""
            away['sep'], home['sep'] = '│','│'
            try:
                home['status'] = ''
                # if game['situation']['possession'] == away['id']:
                if game['situation']['possesion'] == 'away':
                    home['status'] = "%s 🏈" % away['abv']
                # elif game['situation']['possession'] == home['id']:
                elif game['situation']['possesion'] == 'home':
                    home['status'] = "%s 🏈" % home['abv']
                # home['status'] = "%s %s" % (home['status'], game['situation']['downDistanceText'])
                home['status'] = "%s %s" % (home['status'], game['situation']['downAndDistance'])
            except KeyError:
                pass

            # g = [away, home]
            # status = event['status']['type']['state']
            status = event['status']['state']
            # away['status'] = event['status']['type']['shortDetail']
            away['status'] = event['status']['detail']
            if status == 'pre':
                if 'odds' in game:
                    # home['status'] = game['odds'][0]['details']
                    if 'details' in game['odds']:
                        home['status'] = game['odds']['details']
                teamlistpre.extend([away,home])
            else:
                # if 'linescores' in awayjson:
                #     longest_qtr = max(longest_qtr, len(awayjson['linescores']))
                if 'lnescrs' in game:
                    longest_qtr = max(longest_qtr, len(game['lnescrs'])+1)
                if status == 'in':
                    teamlistin.extend([away,home])
                else:
                    teamlistpost.extend([away,home])

            # if status == 'pre':
            #     if 'odds' in game:
            #         home['status'] = game['odds'][0]['details']
            #     labels = ['rank','abv','sep','status']
            # elif status == 'in' or status == 'post':
            #     labels = ['rank','abv','score','pos','sep']
            #     quarters = ['q1','q2','q3','q4','o1','o2','o3','o4','o5','o6']
            #     #add overtimes to labels if necessary
            #     if 'linescores' in awayjson:
            #         labels.extend(quarters[:len(awayjson['linescores'])])
            #     labels.extend(['sep','status'])
            # output = output + utils.format_table(labels,g, showlabels=False)
            # if team is None:
            #     output += LINE_SEP

    labels_pre = ['rank','abv','sep','status']
    labels_post = ['rank','abv','score','pos','sep']
    quarters = ['q1','q2','q3','q4','o1','o2','o3','o4','o5','o6']
    left = ['status']
    labels_post.extend(quarters[:longest_qtr])
    labels_post.extend(['sep','status'])
    if len(teamlistin) > 0:
        output = output + utils.format_table(labels_post, teamlistin, showlabels=False, linebreaknum=2, linebreak=LINE_SEP, left_list=left)
        if len(teamlistpost) > 0 or len(teamlistpre) > 0:
            output = output + "\n" + LINE_SEP + "\n"
    if len(teamlistpre) > 0:
        output = output + utils.format_table(labels_pre, teamlistpre, showlabels=False, linebreaknum=2, linebreak=LINE_SEP)
        if len(teamlistpost) > 0:
            output = output + "\n" + LINE_SEP + "\n"
    if len(teamlistin) + len(teamlistpost) + len(teamlistpre) == 0:
        output = "error finding team"
    else:
        output = output + utils.format_table(labels_post, teamlistpost, showlabels=False, linebreaknum=2, linebreak=LINE_SEP)

    # if team is None:
    #     output = output[:-len(LINE_SEP)]
    return output


if __name__ == "__main__":
    print(get_game("stan"))
    # print(get_game("vt",delta=-2))
    # print(get_game("vt",delta=1))
