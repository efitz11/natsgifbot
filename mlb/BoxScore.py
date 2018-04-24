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

    def print_box(self, side="home", part="batting"):
        output = None
        if part == "batting":
            output = "%s %s %s %s %s %s %s %s %s\n" % ("Batters".ljust(18),'AB','R','H','RBI','BB','SO','LOB',' AVG')
            lastbatter = None
            for batter in self.box['teams'][side]['batters']:
                player = self.players[batter]
                if lastbatter not in self.box['teams'][side]['battingOrder'] and lastbatter is not None:
                    name = " " + player['person']['boxscoreName']
                else:
                    name = player['person']['boxscoreName']
                lastbatter = batter
                pos = player['position']['abbreviation']
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
                outlist = [abs, runs, hits, rbi, bb, so, lob, avg]
                output = output + namepos
                for s in outlist:
                    output = output + " " + s
                output = output + "\n"
        elif part == "pitching":
            output = "%s %s %s %s %s %s %s %s %s\n" % ("Pitchers".ljust(15)," IP"," H"," R","ER","BB","SO","HR","  ERA")
            for pitcher in self.box['teams'][side]['pitchers']:
                player = self.players[pitcher]
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
                outlist = [ip, hits, runs, er, bb, so, hr, era]
                for s in outlist:
                    output = output + " " + s

                output = output + "\n"

        notes = self.box['teams'][side]['info']
        for i in notes:
            if part == "batting" and (i['title'] == "BATTING" or i['title'] == "FIELDING"):
                output = output + "\n" + i['title'] + ":\n"
                for f in i['fieldList']:
                    output = output + "%s: %s\n" % (f['label'], f['value'])
        if part == "pitching":
            output = output + "\n"
            for i in self.box['pitchingNotes']:
                output = output + "%s\n" % (i)
        # print(output)
        return output

if __name__ == "__main__":
    bs = BoxScore("",gamepk="529744")
    bs.print_box('away',part="pitching")
