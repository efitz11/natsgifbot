import newmlbstats
import mymlbstats

import csv

bbref_teams = {"LAA":108, "ARI":109, "BAL":110, "BOS":111, "CHC":112, "CIN":113,
               "CLE":114, "COL":115, "DET":116, "HOU":117, "KCR":118, "LAD":119,
               "WSN":120, "NYM":121, "OAK":133, "PIT":134, "SDP":135, "SEA":136,
               "SFG":137, "STL":138, "TBR":139, "TEX":140, "TOR":141, "MIN":142,
               "PHI":143, "ATL":144, "CHW":145, "MIA":146, "NYY":147, "MIL":158}

# read bases loaded no out PAs
with open("nobletiger2018.csv") as f:
    pas = [{k: v for k, v in row.items()}
           for row in csv.DictReader(f, skipinitialspace=True)]

nobletigers = list()
team_nobles = dict()
for pa in pas:
    teamid = bbref_teams[pa['Tm']]
    # print(pa)
    gamenum = 1
    d = pa['Date']
    if "(" in pa['Date']:
        gamenum = int(d[12])
        d = d[:10]
        # print(d, gamenum)
    # print(d, gamenum)
    sched = newmlbstats.get_schedule(newmlbstats._convert_mlb_date_to_datetime(d), teamid=teamid)
    top, inning = pa['Inn'][0] == 't', int(pa['Inn'][1:])
    # print(pa['Inn'], top, inning)
    half = 'away' if teamid == sched[0]['games'][gamenum-1]['teams']['away']['team']['id'] == teamid else 'home'
    runs = sched[0]['games'][gamenum-1]['linescore']['innings'][inning-1][half]['runs']
    # print(runs)
    if runs == 0:
        print(pa)
        print("NOBLETIGER FOUND")
        nobletigers.append(pa)
        if pa['Tm'] in team_nobles:
            team_nobles[pa['Tm']] += 1
        else:
            team_nobles[pa['Tm']] = 1
    # print("========")

print("Summary: %d NOBLETIGERS found in %d PA" % (len(nobletigers), len(pas)))
team_nobles = {k: v for k, v in sorted(team_nobles.items(), key=lambda item: item[1], reverse=True)}
for team in team_nobles:
    print(team, team_nobles[team])

