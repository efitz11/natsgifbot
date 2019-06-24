import utils

def get_todays_scores():
    url = "https://worldcup.sfg.io/matches/today"
    games = utils.get_json(url)
    output = ""
    gameslist = []
    for game in games:
        home = dict()
        away = dict()
        home['team'] = game['home_team']['code']
        away['team'] = game['away_team']['code']
        home['score'] = game['home_team']['goals']
        away['score'] = game['away_team']['goals']
        if game['status'] == 'completed':
            away['time'] = 'Final'
        elif game['time'] is not None:
            away['time'] = game['time']
        elif game['status'] == 'future':
            away['time'] = utils.get_ET_from_timestamp(game['datetime'])
        # else:
        #     away['time'] =
        gameslist.append(away)
        gameslist.append(home)
    labels = ['team', 'score','time']
    return utils.format_table(labels,gameslist, showlabels=False, linebreaknum=2)

if __name__ == "__main__":
    print(get_todays_scores())
