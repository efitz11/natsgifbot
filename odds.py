import utils
import time

def _build_url(sport, league):
    if league is not None:
        return "https://www.bovada.lv/services/sports/event/coupon/events/A/description/%s/%s?marketFilterId=def&lang=en" % (sport, league)
    else:
        return "https://www.bovada.lv/services/sports/event/coupon/events/A/description/%s?marketFilterId=def&lang=en" % (sport)

def _build_url_live(sport, league, live=False):
    if live:
        l = "liveOnly=true"
    else:
        l = "preMatchOnly=true"
    return "https://www.bovada.lv/services/sports/event/coupon/events/A/description/%s/%s?marketFilterId=def&%s&lang=en" % (sport, league, l)

def get_league_odds(league, sport=None):
    if league == "ufc":
        sport = "ufc-mma"
        league = None

    url = _build_url(sport, league=league)
    odds = utils.get_json(url)[0]['events']
    return get_odds_games(odds)

def get_league_odds_table(league, sport=None, team=None):
    games = get_league_odds(league, sport=sport)

    labels = ["status", "name", "spread", "ml", "total"]
    left = ["status", "name"]

    if team is not None:
        team = team.lower()
        newgames = list()
        for i in range(len(games)):
            if i%3 == 0:
                if team in games[i]['name'].lower() or \
                        team in games[i+1]['name'].lower():
                    if games[i]['status'] == "Live":
                        score = get_game_score(games[i]['eventid'])
                        games[i]['score'] = score['away']
                        games[i+1]['score'] = score['home']
                        games[i]['status'] = score['period']
                        games[i+1]['status'] = score['time']
                        games[i]['name'] = score['awayteam']
                        games[i+1]['name'] = score['hometeam']
                    newgames.append(games[i])
                    newgames.append(games[i+1])
                    newgames.append({})
        labels.insert(1, "score")
        ret = utils.format_table(labels, newgames, left_list=left).rstrip()
    else:
        ret = utils.format_table(labels, games, left_list=left).rstrip()
    return ret


def get_nba_odds():
    urlpre = _build_url_live("basketball", "nba")
    urllive = _build_url_live("basketball", "nba", live=True)
    try:
        odds = utils.get_json(urlpre)[0]['events']
    except IndexError:
        odds = []
    try:
        odds2 = utils.get_json(urllive)[0]['events']
    except IndexError:
        odds2 = []
    return get_odds_games(odds2) + get_odds_games(odds)

def get_nhl_odds():
    url = _build_url("hockey", "nhl")
    odds = utils.get_json(url)[0]['events']
    return get_odds_games(odds)

def get_nfl_odds(superbowl=False):
    if superbowl:
        url = _build_url("football", "super-bowl")
    else:
        url = _build_url("football", "nfl")
    odds = utils.get_json(url)[0]['events']
    return get_odds_games(odds)

def get_cbb_odds():
    url = _build_url("basketball", "college-basketball")
    odds = utils.get_json(url)[0]['events']
    return get_odds_games(odds)

def get_xfl_odds():
    url = _build_url("football", "xfl")
    odds = utils.get_json(url)[0]['events']
    return get_odds_games(odds)

def get_game_score(id):
    url = "https://services.bovada.lv/services/sports/results/api/v1/scores/%s" % id
    data = utils.get_json(url)
    score = dict()
    score['away'] = data['latestScore']['visitor']
    score['home'] = data['latestScore']['home']
    score['period'] = data['clock']['period']
    score['time'] = data['clock']['gameTime']
    for team in data['competitors']:
        if team['homeOrVisitor'] == "home":
            score['hometeam'] = team['abbreviation']
        else:
            score['awayteam'] = team['abbreviation']
    return score

def get_odds_games(odds):
    games = []
    for event in odds:
        home = dict()
        away = dict()
        for team in event['competitors']:
            if team['home']:
                home['name'] = team['name']
            else:
                away['name'] = team['name']

        away['eventid'] = event['id']
        home['eventid'] = event['id']

        groups = event['displayGroups']
        for group in groups:
            for market in group['markets']:
                if event['live']:
                    if market['period']['live']:
                        away['status'] = "Live"
                    else:
                        away['status'] = market['period']['abbreviation']
                elif not market['period']['live']:
                    starttime = event['startTime']/1000
                    date = time.strftime("%m/%d/%y", time.localtime(starttime))
                    local = time.strftime("%I:%M %p", time.localtime(starttime))
                    away['status'] = date
                    home['status'] = local
                else:
                    away['status'] = market['period']['abbreviation']
                if market['description'] == "Point Spread":
                    for outcome in market['outcomes']:
                        spread = outcome['price']['handicap']
                        if float(spread) > 0:
                            spread = "+" + spread
                        if outcome['type'] == "A":
                            away['spread'] = "%s (%s)" % (spread, outcome['price']['american'])
                        else:
                            home['spread'] = "%s (%s)" % (spread, outcome['price']['american'])
                elif market['description'] in ["Moneyline", "Fight Winner"]:
                    for outcome in market['outcomes']:
                        if outcome['type'] == "A":
                            away['ml'] = outcome['price']['american']
                        else:
                            home['ml'] = outcome['price']['american']
                elif market['description'] == "Total":
                    for outcome in market['outcomes']:
                        if outcome['type'] == "O":
                            home['total'] = "U%s (%s)" % (outcome['price']['handicap'], outcome['price']['american'])
                        else:
                            away['total'] = "O%s (%s)" % (outcome['price']['handicap'], outcome['price']['american'])
        games.append(away)
        games.append(home)
        games.append(dict())
    return games

def get_odds_pp(league, team=None):
    if league == "nba":
        games = get_nba_odds()
    elif league == "nhl":
        games = get_nhl_odds()
    elif league == "xfl":
        games = get_xfl_odds()
    elif league == "nfl":
        if team == "super bowl":
            games = get_nfl_odds(superbowl=True)
            team = None
        else:
            games = get_nfl_odds()
    elif league == "cbb":
        if team is None:
            return "cbb team is required"
        games = get_cbb_odds()

    labels = ["status", "name", "spread", "ml", "total"]
    left = ["status", "name"]

    if team is not None:
        team = team.lower()
        newgames = list()
        for i in range(len(games)):
            if i%3 == 0:
                if team in games[i]['name'].lower() or \
                        team in games[i+1]['name'].lower():
                    if games[i]['status'] == "Live":
                        score = get_game_score(games[i]['eventid'])
                        games[i]['score'] = score['away']
                        games[i+1]['score'] = score['home']
                        games[i]['status'] = score['period']
                        games[i+1]['status'] = score['time']
                        games[i]['name'] = score['awayteam']
                        games[i+1]['name'] = score['hometeam']
                    newgames.append(games[i])
                    newgames.append(games[i+1])
                    newgames.append({})
        labels.insert(1, "score")
        ret = utils.format_table(labels, newgames, left_list=left).rstrip()
    else:
        ret = utils.format_table(labels, games, left_list=left).rstrip()
    return ret

if __name__ == "__main__":
    # print(get_odds_pp(sport="nba", team="wiz"))
    # print(get_odds_pp("nhl", team="capitals"))
    # print(get_odds_pp("nba"))
    print(get_odds_pp("nba", team="new"))
    # print(get_league_odds_table('xfl'))
