import utils

def get_todays_scores(team=None):
    url = "https://worldcup.sfg.io/matches/today"
    games = utils.get_json(url)
    gameslist = []
    for game in games:
        if team is not None:
            if team.lower() in game['home_team']['code'].lower() or \
              team.lower() in game['away_team']['code'].lower() or \
              team.lower() in game['home_team']['country'].lower() or \
              team.lower() in game['away_team']['country'].lower():
                if game['status'] != 'future':
                    return format_single_game(game)
            else:
                continue
        else:
            if game['status'] != 'future' and len(games) == 1:
                return format_single_game(game)

        home = dict()
        away = dict()
        home['team'] = game['home_team']['code']
        away['team'] = game['away_team']['code']
        if game['status'] == 'future':
            home['score'] = ""
            away['score'] = ""
        else:
            home['score'] = game['home_team']['goals']
            away['score'] = game['away_team']['goals']
        if game['status'] == 'completed' or game['time'] == 'full-time':
            away['time'] = 'Final'
        elif game['time'] is not None:
            away['time'] = "%s" % game['time']
        elif game['status'] == 'future':
            away['time'] = utils.get_ET_from_timestamp(game['datetime'])
        # else:
        #     away['time'] =
        gameslist.append(away)
        gameslist.append(home)
    labels = ['team', 'score','time']
    return utils.format_table(labels,gameslist, showlabels=False, linebreaknum=2)

def format_single_game(game):
    line = dict()
    line['5'] = game['home_team']['code']
    line['1'] = game['away_team']['code']
    line['4'] = game['home_team']['goals']
    line['2'] = game['away_team']['goals']
    if game['status'] == 'completed' or game['time'] == 'full-time':
        line['time'] = ' | Final | '
    elif game['time'] is not None:
        line['time'] = " | %s | " % game['time']
    elif game['status'] == 'future':
        line['time'] = utils.get_ET_from_timestamp(game['datetime'])

    rows = [line]

    home_goals = []
    away_goals = []
    for event in game['home_team_events']:
        if 'goal' in event['type_of_event']:
            if event['type_of_event'] == 'goal':
                home_goals.append("%s (%s)" % (event['player'], event['time']))
            if event['type_of_event'] == 'goal-penalty':
                home_goals.append("%s (%s PEN)" % (event['player'], event['time']))
    for event in game['away_team_events']:
        if 'goal' in event['type_of_event']:
            if event['type_of_event'] == 'goal':
                away_goals.append("%s (%s)" % (event['player'], event['time']))
            if event['type_of_event'] == 'goal-penalty':
                away_goals.append("%s (%s-PEN)" % (event['player'], event['time']))
    lines = max(len(home_goals), len(away_goals))
    for i in range(lines):
        a = dict()
        if i < len(away_goals):
            a['1'] = away_goals[i]
        if i < len(home_goals):
            a['5'] = home_goals[i]
        rows.append(a)

    labels = ['1','2','time','4','5']
    return utils.format_table(labels, rows, showlabels=False, left_list=['5'])




if __name__ == "__main__":
    print(get_todays_scores(team='usa'))
