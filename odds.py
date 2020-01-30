import utils
import time

def _build_url(sport, league):
    return "https://www.bovada.lv/services/sports/event/coupon/events/A/description/%s/%s?marketFilterId=def&lang=en" % (sport, league)

def get_nba_odds():
    url = "https://www.bovada.lv/services/sports/event/coupon/events/A/description/basketball/nba?marketFilterId=def&lang=en"
    odds = utils.get_json(url)[0]['events']
    return get_odds_games(odds)

def get_nhl_odds():
    url = _build_url("hockey", "nhl")
    odds = utils.get_json(url)[0]['events']
    return get_odds_games(odds)

def get_cbb_odds():
    url = _build_url("basketball", "college-basketball")
    odds = utils.get_json(url)[0]['events']
    return get_odds_games(odds)

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

        groups = event['displayGroups']
        for group in groups:
            for market in group['markets']:
                if market['period']['description'] == "Live Match":
                    away['status'] = "Live"
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
                        if outcome['type'] == "A":
                            away['spread'] = "%s (%s)" % (outcome['price']['handicap'], outcome['price']['american'])
                        else:
                            home['spread'] = "%s (%s)" % (outcome['price']['handicap'], outcome['price']['american'])
                elif market['description'] == "Moneyline":
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
    print(team)
    if league == "nba":
        games = get_nba_odds()
    elif league == "nhl":
        games = get_nhl_odds()
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
                    newgames.append(games[i])
                    newgames.append(games[i+1])
                    break
        ret = utils.format_table(labels, newgames, left_list=left).rstrip()
    else:
        ret = utils.format_table(labels, games, left_list=left).rstrip()
    return ret

if __name__ == "__main__":
    # print(get_odds_pp(sport="nba", team="wiz"))
    print(get_odds_pp(sport="nhl"))