import urllib.parse
import json
import utils
from datetime import datetime
from bs4 import BeautifulSoup

def _new_player_search(name):
    #url = "https://suggest.mlb.com/svc/suggest/v1/min_all/%s/99999" % urllib.parse.quote(name)
    url = "https://typeahead.mlb.com/api/v1/typeahead/suggestions/%s" % urllib.parse.quote(name)
    #players = utils.get_json(url)['suggestions']
    players = utils.get_json(url)['players']
    if len(players) > 0:
        p = players[0]['playerId']
        for player in players:
            if player['teamId'] == 120:
                p = player['playerId']
        url = "https://statsapi.mlb.com/api/v1/people/%s?hydrate=currentTeam,team,stats(type=[yearByYear,yearByYearAdvanced,careerRegularSeason,careerAdvanced,availableStats](team(league)),leagueListId=mlb_hist)" % p
        return utils.get_json(url)['people'][0]

def _get_player_info_line(player):
    pos = player['primaryPosition']['abbreviation']
    bats = player['batSide']['code']
    throws = player['pitchHand']['code']
    height = player['height']
    weight = player['weight']

    bdate = player['birthDate'].split("-")
    bdatetime = datetime.strptime(player['birthDate'], "%Y-%m-%d")
    today = datetime.today()
    age = today.year - bdatetime.year - ((today.month, today.day) < (bdatetime.month, bdatetime.day))

    ret = "%s | B/T: %s/%s | %s | %s | %s" % (pos, bats, throws, height, weight, age)


    if int(bdate[1]) == today.month and int(bdate[2]) == today.day:
        ret += " | **HAPPY BIRTHDAY**"
    return ret

def get_player_season_stats(name, type=None, year=None, career=None, reddit=None):
    player = _new_player_search(name)
    if player is None:
        return "No matching player found"
    # teamid = player['currentTeam']['id']
    teamabv = player['currentTeam']['abbreviation']
    # pid = player['id']
    disp_name = player['fullName']
    pos = player['primaryPosition']['abbreviation']
    infoline = _get_player_info_line(player)
    now = datetime.now()
    # birthdate = player['birthDate']
    # birthdate = birthdate[:birthdate.find('T')]
    # birth = birthdate.split('-')

    if year is None:
        year = str(now.year)
        year2 = year
    elif '-' in year:
        years = year.split('-')
        year = years[0]
        year2 = years[1]
    else:
        year2 = year

    # d = None
    # if year == None:
    #     d = now.year - int(birth[0]) - ((now.month, now.day) < (int(birth[1]), int(birth[2])))
    # elif year is not None:
    #     d = int(year) - int(birth[0]) - ((7,1) < (int(birth[1]), int(birth[2])))
    # if d is not None:
    #     infoline = "%s | Age: %d" % (infoline, d)
    # if now.month == int(birth[1]) and now.day == int(birth[2]):
    #     infoline = infoline + "  **HAPPY BIRTHDAY**"

    if type is None and pos == 'P':
        type = "pitching"
    elif type is None and pos != 'P':
        type = "hitting"

    stattype = 'yearByYear'
    if career:
        stattype = "career"

    seasons = []
    teams = []
    for stat in player['stats']:
        if stat['type']['displayName'] == stattype and 'displayName' in stat['group'] and stat['group']['displayName'] == type:
            if career:
                for cstat in player['stats']:
                    if cstat['type']['displayName'] == 'yearByYear' and 'displayName' in cstat['group'] and cstat['group']['displayName'] == type:
                        years = "%s-%s" % (cstat['splits'][0]['season'], cstat['splits'][-1]['season'])
            for split in stat['splits']:
                if stattype == 'yearByYear':
                    if int(split['season']) < int(year) or int(split['season']) > int(year2):
                        continue
                season = split['stat']
                if 'season' in split:
                    season['season'] = split['season']
                if 'team' in split:
                    season['team'] = split['team']['abbreviation']
                    teams.append(season['team'])
                else:
                    season['team'] = split['sport']['abbreviation']
                seasons.append(split['stat'])
    if type == "hitting":
        stats = ['atBats', 'hits', 'doubles', 'triples', 'homeRuns', 'runs', 'rbi', 'baseOnBalls', 'strikeOuts', 'stolenBases', 'caughtStealing', 'avg', 'obp', 'slg' ,'ops']
    elif type == "pitching":
        stats = ['wins', 'losses', 'gamesPlayed', 'gamesStarted', 'saveOpportunities', 'saves', 'inningsPitched', 'strikeOuts', 'baseOnBalls', 'homeRuns', 'era', 'whip']
    if len(seasons) > 1:
        stats = ['season', 'team'] + stats
    repl = {'atBats':'ab', 'plateAppearances':'pa','hits':'h','doubles':'2B','triples':'3b','homeRuns':'hr', 'runs':'r', 'baseOnBalls':'bb','strikeOuts':'so', 'stolenBases':'sb', 'caughtStealing':'cs',
            'wins':'w', 'losses':'l', 'gamesPlayed':'g', 'gamesStarted':'gs', 'saveOpportunities':'svo', 'saves':'sv', 'inningsPitched':'ip'}

    if year == year2:
        if year == str(now.year) and len(teams) == 0 and 'currentTeam' in player:
            teamabv = player['currentTeam']['abbreviation']
        else:
            teamabv = '/'.join(teams)
        output = "%s season stats for %s (%s):" % (year, disp_name, teamabv)
    else:
        output = "%s-%s seasons stats for %s:" % (year, year2, disp_name)
    if career:
        output = "Career stats for %s (%s):" % (disp_name, years)
    output = "%s\n\t%s\n\n" % (output, infoline)
    output = output + utils.format_table(stats, seasons, repl_map=repl, reddit=reddit)
    return output

def get_scoring_plays(gamepk):
    url = "https://statsapi.mlb.com/api/v1/game/%s/playByPlay" % str(gamepk)
    data = utils.get_json(url)
    playslist = list()
    for play in data['scoringPlays']:
        playslist.append(data['allPlays'][play])
    return playslist

def print_contract_info(name, year=None):
    # find player
    player = _new_player_search(name)
    pname = player['fullName'].lower().replace(' ', '-')

    url = "https://www.spotrac.com/search/results/%s/" % (pname)
    html, returl = utils.get_page(url, return_url=True)

    if returl != url:
        return get_player_contract_table(html, url)
    else:
        ret = _parse_contract_search(html)
        if ret is not None:
            html, returl = utils.get_page(ret, return_url=True)
            return get_player_contract_table(html, returl)
        else:
            return "Could not find player"

def get_player_contract_table(html, url):
    # html = utils.get_page(url)
    # with open('spotrac.txt', 'r') as w:
    #     html = w.read()
    bs = BeautifulSoup(html, 'html.parser')
    blurb = bs.find("p", {"class":"currentinfo"})
    output = ""
    if blurb is not None:
        output = blurb.get_text() + "\n\n"
    table = bs.find("table", {"class":"salaryTable salaryInfo current visible-xs"})
    rows = table.find_all("tr")
    contract_table = []
    for row in rows:
        cells = row.find_all('td')
        r = {'0':cells[0].get_text(), '1':cells[1].get_text()}
        contract_table.append(r)
    output = output + "```python\n%s```" % utils.format_table(['0','1'], contract_table, showlabels=False)

    table = bs.find("table", {"class":"salaryTable current"})
    rows = table.find_all("tr")
    salary_table = []
    salary_th = []
    for header in rows[0].find_all('th'):
        salary_th.append(header.get_text())
    for row in rows[1:]:
        year_row = {}
        cells = row.find_all('td')
        # print(cells)
        for i in range(len(salary_th)):
            try:
                if 'noborder' not in cells[i]['class'] or 'fayear' in cells[i]['class']:
                    data = cells[i].get_text().lstrip()
                    if data.startswith('$'):
                        data = utils.human_format(data)
                    year_row[salary_th[i]] = data
            except:
                pass
        if len(year_row.keys()) > 0:
            salary_table.append(year_row)
    labs = ['Year', 'Age', 'Base Salary','Luxury Tax Salary','Payroll  Salary']
    repl = {"Base Salary":"Base", "Luxury Tax Salary":"Luxury Tax", "Payroll  Salary":"Payroll"}
    output = output + "\n```python\n%s```" % utils.format_table(labs, salary_table, repl_map=repl)
    output = output + "\n<%s>" % url
    return output

def _parse_contract_search(html):
    bs = BeautifulSoup(html, 'html.parser')
    div = bs.find_all("div", {"class":"teamlist"})
    # print(div)
    positions = ["Starting Pitcher", "Relief Pitcher", "1st Base", "2nd Base", "3rd Base", "Catcher",
                 "Outfielder", "Outfielders", "Shortstop", "Right Field", "Center Field", "Left Field",
                 "Pitcher", "Pitchers"]
    items = div[0].find_all("div", {"class":"teamitem"})
    for item in items:
        pos = item.find_all("div", {"class":"teamoptions"})[0]
        print(pos.get_text())
        if pos.get_text() in positions:
            return item.find_all("a")[0]['href']

if __name__ == "__main__":
    # print(get_player_season_stats("rendon", year="2016-2019"))
    # print(get_player_season_stats("rendon", career=True))
    # print(get_player_season_stats('daniel hudson'))
    # print(print_contract_info("max scherzer"))
    # print(get_player_contract_table(""))
    get_scoring_plays(630851)
