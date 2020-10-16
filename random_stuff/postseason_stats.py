import newmlbstats
import utils
import unicodedata

def read_csv(filename):
    pitchers = list()
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    for line in lines:
        pitcher = unicodedata.normalize("NFKD", line.split(',')[0])
        pitchers.append({'name':pitcher})
    return pitchers

def get_postseason_stats(playerid):
    url = "https://statsapi.mlb.com/api/v1/people/%s/stats?stats=yearByYear,career,yearByYearAdvanced," \
          "careerAdvanced&gameType=P&leagueListId=mlb_hist&group=pitching&hydrate=team(league)&language=en" % str(playerid)
    stats = utils.get_json(url)['stats']
    for stat in stats:
        if stat['type']['displayName'] == 'career':
            return stat['splits'][0]['stat']

if __name__ == "__main__":
    pitchers = read_csv("post_pitchers.csv")
    for pitcher in pitchers:
        name = pitcher['name']
        player_id = newmlbstats._find_player_id(name)
        if player_id is None:
            print("couldn't find id for %s" % name)
            continue
        pitcher['id'] = player_id
        stats = get_postseason_stats(player_id)
        pitcher.update(stats)
    # sort pitchers by ERA
    pitchers = sorted(pitchers, key=lambda i: i['era'])
    labels = ['name', 'inningsPitched', 'homeRuns', 'era']
    replace = {'inningsPitched':'ip', 'homeRuns':'hr'}
    left = ['name']
    print(utils.format_reddit_table(labels, pitchers,repl_map=replace, left_list=left))
