import mlbgame
from datetime import datetime, timedelta
from urllib.error import HTTPError
from urllib.request import urlopen
import lxml.etree as etree

BASE_URL = ('http://gd2.mlb.com/components/game/mlb/'
            'year_{0}/month_{1:02d}/day_{2:02d}/')
GAME_URL = BASE_URL + '/gid_{3}/{4}'

def get_date_from_game_id(game_id):
    year, month, day, _discard = game_id.split('_', 3)
    return int(year), int(month), int(day)

def get_overview(game_id):
    """Return the linescore file of a game with matching id."""
    year, month, day = get_date_from_game_id(game_id)
    try:
        return urlopen(GAME_URL.format(year, month, day,
                                       game_id,
                                       'linescore.xml'))
    except HTTPError:
        raise ValueError('Could not find a game with that id.')

def retoverview(game_id):
    """Gets the overview information for the game with matching id."""
    # get data
    data = get_overview(game_id)
    # parse data
    parsed = etree.parse(data)
    root = parsed.getroot()
    #print(parsed.find("current_batter").get("last_name"))
    output = {}
    # get overview attributes
    for x in root.attrib:
        output[x] = root.attrib[x]
    if parsed.find("current_batter") != None:
        output['current_batter'] = parsed.find("current_batter").get("last_name")
        output['current_pitcher'] = parsed.find("current_pitcher").get("last_name")
    if parsed.find('home_probable_pitcher') != None:
        output['home_probable_pitcher'] = parsed.find('home_probable_pitcher').get("last_name")
        output['away_probable_pitcher'] = parsed.find('away_probable_pitcher').get("last_name")
    return output