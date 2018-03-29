from datetime import datetime, timedelta
from urllib.error import HTTPError
from urllib.request import urlopen
import lxml.etree as etree

BASE_URL = ('http://gd2.mlb.com/components/game/mlb/'
            'year_{0}/month_{1:02d}/day_{2:02d}/')
GAME_URL = BASE_URL + 'gid_{3}/{4}'

basesmap = {'0':'---',
            '1':'1--',
            '2':'-2-',
            '3':'--3',
            '4':'12-',
            '5':'1-3',
            '6':'-23',
            '7':'123'}

def get_date_from_game_id(game_id):
    year, month, day, _discard = game_id.split('_', 3)
    return int(year), int(month), int(day)

def get_overview(game_id):
    """Return the linescore file of a game with matching id."""
    year, month, day = get_date_from_game_id(game_id)
    try:
        #print(GAME_URL.format(year, month, day,
        #                               game_id,
        #                               'linescore.xml'))
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
    if parsed.find('winning_pitcher') != None:
        output['winning_pitcher'] = parsed.find('winning_pitcher').get("last_name")
        output['losing_pitcher'] = parsed.find('losing_pitcher').get("last_name")
        output['save_pitcher'] = parsed.find('save_pitcher').get("last_name")
    return output
    
    
def get_game_str(gameid, lastplay=False):
    overview = retoverview(gameid)
    return get_game_status(overview, lastplay)

def get_game_status(overview, lastplay=False):
    hometeam = overview['home_name_abbrev']
    awayteam = overview['away_name_abbrev']
    status   = overview['status']
    
    if status == 'Pre-Game' or status == 'Warmup' or status == 'Preview' or status == 'Scheduled':
        firstpitch = overview['time']
        awins = overview['away_win']
        aloss = overview['away_loss']
        hwins = overview['home_win']
        hloss = overview['home_loss']
        hrecord = "(%s-%s)" % (hwins,hloss)
        arecord = "(%s-%s)" % (awins,aloss)
        output = "%s %s @ %s %s # %s ET - %s\n\t" % (awayteam.ljust(3), arecord, hometeam.ljust(3), hrecord, firstpitch,status)
        output = output + overview['away_probable_pitcher'] + " v " + overview['home_probable_pitcher']
        return output
        
    homeruns = overview['home_team_runs']
    awayruns = overview['away_team_runs']
    outs     = overview['outs']
    inning   = overview['inning']
    top_inn  = "Top" if overview['top_inning'] == 'Y' else "Bot"
    outs = outs + " out" + ("" if outs == "1" else "s")
    count = "Count: (" + overview['balls'] + "-" + overview['strikes'] + ")"
    
    output = "%s %s @ %s %s" % (awayteam.ljust(3), awayruns, hometeam.ljust(3), homeruns)
    overstatuses = ['Final', 'Game Over', 'Postponed']
    if status not in overstatuses:
        bases = ""
        if 'runner_on_base_status' in overview:
            bases = basesmap[overview['runner_on_base_status']]
        output = output + ":  %s %s - %s %s %s" % (top_inn, inning, outs, bases, count)
    elif status == 'Postponed':
        output = output + " #Postponed"
    else:
        output = output + " (F) "
        wp = overview['winning_pitcher']
        lp = overview['losing_pitcher']
        sp = overview['save_pitcher']
        output = output + "# WP: " + wp.ljust(10) + "\tLP: " + lp.ljust(10) + (("\tSV: " + sp.ljust(10)) if sp != "" else "")
    if 'current_batter' in overview:
        pitcher = overview['current_pitcher'].ljust(12)
        batter = overview['current_batter']
        output = output + "\n\tPitching: %s \tBatting: %s" % (pitcher, batter)
    if lastplay and 'pbp_last' in overview:
        lplay    = overview['pbp_last']
        output = output + "\n\tLast play: " + lplay.strip()
    return output
    
class Updater:
    
    def __init__(self):
        self.lastpbp = ""
        self.updatenext = False
        self.nextupdate = "" 
    def update(self,id):
        output = ""
        overview = retoverview(id)
        #print("updating")
        if self.updatenext: #delay block
            self.updatenext = False
            output = self.nextupdate
        if 'pbp_last' in overview:
            if overview['pbp_last'] != self.lastpbp:
                print (overview['pbp_last'])
                self.lastpbp = overview['pbp_last']
                self.updatenext = True
                self.nextupdate = get_game_status(overview,lastplay=True)
        return output