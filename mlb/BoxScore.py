import json
from urllib.request import urlopen, Request

class BoxScore:
    def __init__(self,json,gamepk=None):
        if gamepk is not None:
            self.__retrieve_json(gamepk)
        else:
            self.box = json
        self.players = {}
        self.__create_box()

    def __retrieve_json(self,gamepk):
        url = "https://statsapi.mlb.com/api/v1/game/" + gamepk + "/boxscore?hydrate=person"
        print(url)
        req = Request(url, headers={'User-Agent' : "ubuntu"})
        self.box = json.loads(urlopen(req).read().decode("utf-8"))

    def __create_box(self):
        for t in self.box['teams']:
            for p in self.box['teams'][t]['players']:
                pid = self.box['teams'][t]['players'][p]['person']['id']
                self.players[pid] = self.box['teams'][t]['players'][p]

    def print_box(self, side="home", part="batting", display_pitches=False, oldboxes=[], playerid=None):
        output = None
        if part == "batting":
            output = "%s %s %s %s %s %s %s %s %s %s %s\n" % ("".ljust(18),'AB','R','H','RBI','BB','SO','LOB',' AVG', ' OBP',' SLG')
            lastbatter = None
            count = 0
            for batter in self.box['teams'][side]['batters']:
                player = self.players[batter]
                if playerid is not None:
                    if player['person']['id'] != playerid:
                        continue
                if lastbatter not in self.box['teams'][side]['battingOrder'] and lastbatter is not None:
                    name = " " + player['person']['boxscoreName']
                else:
                    name = player['person']['boxscoreName']
                    if count == 9:
                        break
                    count += 1
                lastbatter = batter
                # pos = player['position']['abbreviation']
                pos = ""
                for p in player['allPositions']:
                    pos = pos + p['abbreviation'] + "-"
                pos = pos[:-1]
                namepos = (name + " " + pos).ljust(18)
                battingstats = player['stats']['batting']
                abs = str(battingstats['atBats']).rjust(2)
                runs = str(battingstats['runs'])
                hits = str(battingstats['hits'])
                rbi = str(battingstats['rbi']).rjust(3)
                bb = str(battingstats['baseOnBalls']).rjust(2)
                so = str(battingstats['strikeOuts']).rjust(2)
                lob = str(battingstats['leftOnBase']).rjust(3)
                avg = player['seasonStats']['batting']['avg']
                obp = player['seasonStats']['batting']['obp']
                slg = player['seasonStats']['batting']['slg']
                outlist = [abs, runs, hits, rbi, bb, so, lob, avg, obp, slg]
                output = output + namepos
                for s in outlist:
                    output = output + " " + s
                output = output + "\n"
        elif part == "pitching":
            output = "%s %s %s %s %s %s %s %s %s %s %s\n" % ("".ljust(15)," IP"," H"," R","ER","BB","SO","HR", "  ERA","  P", " S")
            for pitcher in self.box['teams'][side]['pitchers']:
                player = self.players[pitcher]
                if playerid is not None:
                    if player['person']['id'] != playerid:
                        continue
                name = player['person']['boxscoreName']
                pos = player['position']['abbreviation']
                output = output + name.ljust(15)

                pstats = player['stats']['pitching']
                ip = pstats['inningsPitched']
                hits = str(pstats['hits']).rjust(2)
                runs = str(pstats['runs']).rjust(2)
                er = str(pstats['earnedRuns']).rjust(2)
                bb = str(pstats['baseOnBalls']).rjust(2)
                so = str(pstats['strikeOuts']).rjust(2)
                hr = str(pstats['homeRuns']).rjust(2)
                era = player['seasonStats']['pitching']['era'].rjust(5)
                pitches = str(pstats['pitchesThrown']).rjust(3)
                strikes = str(pstats['strikes']).rjust(2)
                outlist = [ip, hits, runs, er, bb, so, hr, era, pitches, strikes]
                for s in outlist:
                    output = output + " " + s

                output = output + "\n"
        elif part == 'bullpen':
            teamid = self.box['teams'][side]['team']['id']
            table = []
            for playerid in self.box['teams'][side][part]:
                player = self.players[playerid]
                data = dict()
                data['name'] = player['person']['boxscoreName']
                data['era'] = player['seasonStats']['pitching']['era']
                data['t'] = player['person']['pitchHand']['code']
                for box in oldboxes:
                    oldside = 'away'
                    if box.box['teams']['home']['team']['id'] == teamid:
                        oldside = 'home'
                    try:
                        data[box.box['date']] = box.box['teams'][oldside]['players']["ID" + str(playerid)]['stats']['pitching']['pitchesThrown']
                    except:
                        data[box.box['date']] = ""
                table.append(data)
            import sys, os
            sys.path.insert(1, os.path.join(sys.path[0],'..'))
            import mymlbstats
            labels = ['name','t','era']
            leftlist = ['name']
            for b in oldboxes:
                labels.append(b.box['date'])
            # print(labels)
            # print(mymlbstats._print_table(labels, table))
            import utils
            return utils.format_table(labels, table, left_list=leftlist, def_repl=False)

        elif part in ['bench','bullpen']:
            if part == 'bench':
                output = "%s %s %s %s\n" % ("".ljust(15),"B","Pos"," AVG")
            elif part == 'bullpen':
                np = " NP" if display_pitches else ""
                output = "%s %s %s  %s\n" % ("".ljust(15),"T","ERA", np)
                if display_pitches:
                    teamid = self.box['teams'][side]['team']['id']
                    url = "http://mlb.mlb.com/pubajax/wf/flow/stats.splayer?season=2018&sort_order=%27asc%27&sort_column=%27era%27&stat_type=pitching&page_type=SortablePlayer" \
                          "&team_id=" + str(teamid) + "&game_type=%27R%27&last_x_days=3&player_pool=ALL&season_type=ANY&sport_code=%27mlb%27&results=1000&position=%271%27&recSP=1&recPP=50"
                    req = Request(url, headers={'User-Agent' : "ubuntu"})
                    last3 = json.loads(urlopen(req).read().decode("utf-8"))['stats_sortable_player']['queryResults']['row']
            for player in self.box['teams'][side][part]:
                player = self.players[player]
                name = player['person']['boxscoreName']
                pos = player['position']['abbreviation'].rjust(3)
                output = output + name.ljust(15)
                if part == 'bench':
                    data = player['seasonStats']['batting']
                    statlist = ['avg','obp','slg','ops']
                    bat = player['person']['batSide']['code']
                    output = output + " %s %s " % (bat,pos)
                elif part == 'bullpen':
                    data = player['seasonStats']['pitching']
                    throw = player['person']['pitchHand']['code']
                    statlist = ['era']
                    output = output + " %s " % throw
                for stat in statlist:
                    try:
                        output = output + data[stat] + " "
                    except KeyError:
                        pass
                if part == 'bullpen' and display_pitches:
                    plid = player['person']['id']
                    for p in last3:
                        if int(p['player_id']) == plid:
                            output = "%s%3d" % (output, int(p['np']))
                            # output = output + p['np']
                output = output + "\n"
        elif part == "notes":
            notes = self.box['teams'][side]['info']
            output = ""
            for i in notes:
                # if part == "batting" and (i['title'] == "BATTING" or i['title'] == "FIELDING" ):
                # if part == "batting" and (i['title'] in ['BATTING', 'FIELDING', 'BASERUNNING']):
                output = output + "\n" + i['title'] + ":\n"
                for f in i['fieldList']:
                    output = output + "%s: %s\n" % (f['label'], f['value'])
        elif part == 'info':
            info = self.box['info']
            output = ""
            for i in info:
                out = i['label']
                if 'value' in i:
                    out = "%s: %s" % (out, i['value'])
                output = output + "%s\n\n" % (out)
        if part == "pitching":
            output = output + "\n"
            for i in self.box['pitchingNotes']:
                output = output + "%s\n" % (i)
        # print(output)
        # if part == 'bullpen' and display_pitches:
        #     output = output + "NP is pitches thrown in the last 3 days.\n"
        return output

if __name__ == "__main__":
    bs = BoxScore("",gamepk="530598")
    print(bs.print_box('away',part="bench"))
