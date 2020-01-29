import utils

def get_nba_odds():
    url = "https://www.bovada.lv/services/sports/event/coupon/events/A/description/basketball/nba?marketFilterId=def&lang=en"
    return utils.get_json(url)

def get_nba_odds_pp():
    odds = get_nba_odds()[0]['events']
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
                            home['total'] = "O%s (%s)" % (outcome['price']['handicap'], outcome['price']['american'])
                        else:
                            away['total'] = "O%s (%s)" % (outcome['price']['handicap'], outcome['price']['american'])
        games.append(away)
        games.append(home)
        games.append(dict())
    labels = ["status", "name", "spread", "ml", "total"]
    left = ["status", "name"]
    ret = utils.format_table(labels, games, left_list=left)
    return ret

if __name__ == "__main__":
    # print(get_nba_odds())
    print(get_nba_odds_pp())