import discord
from discord.ext import commands

from urllib.request import urlopen, Request
import urllib.parse
from datetime import datetime, timedelta, time

import mlbgame, mymlbgame
import mymlbstats
from bs4 import BeautifulSoup

class Baseball():
    def __init__(self,bot):
        self.bot = bot
        
    @commands.command()
    async def br(self, *query:str):
        """get link to a player's Baseball-Reference page"""
        url = "http://www.baseball-reference.com/search/search.fcgi?search=%s&results=" % urllib.parse.quote_plus(' '.join(query))
        req = Request(url, headers={'User-Agent' : "ubuntu"})
        res = urlopen(req)
        await self.bot.say(res.url)
        
    @commands.command()
    async def fg(self, *query:str):
        """get a link to a player's Fangraphs page"""
        url = "http://www.fangraphs.com/players.aspx?lastname=%s" % urllib.parse.quote_plus(' '.join(query))
        req = Request(url, headers={'User-Agent' : "ubuntu"})
        res = urlopen(req)
        await self.bot.say("<"+res.url+">")#disable embed because it's shit

    @commands.command()
    async def mlb(self,*team :str):
        """Get MLB info

        Supported commands:
        !mlb               - show info for all games today
        !mlb live          - show info for all games live now
        !mlb <team>        - return game info for today for that team
        !mlb <division>    - return division standings (ale,alc,alw,nle,nlc,nlw,alwc,nlwc)
        !mlb sp <team>     - print scoring plays for today's game
        !mlb line <player> - print the player's line for that day's game
        !mlb ohtani        - get ohtani's stats for the day

        each of the previous commands can end in a number of (+days or -days) to change the date

        !mlb stats <player>   - print the player's season stats

        !mlb leaders <stat>   - list MLB leaders in that stat
           leaders can be followed by a list of options:
              pos=p      - p can be any pos (p,1B,SS,LF, etc)
              lg=l       - l can either be al or nl
              qual=q     - q is minimum PA or IP (increments of 10)
              season=s   - s is year
        """
        delta=None

        if len(team) > 0 and (team[-1].startswith('-') or team[-1].startswith('+')):
            delta = team[-1]
            team = team[:-1]

        if len(team) == 0 or (len(team) == 1 and team[0] == 'live'):
            liveonly=False
            if len(team) == 1:
                liveonly = True
            output = mymlbstats.get_all_game_info(delta=delta, liveonly=liveonly)
            await self.bot.say("```python\n" + output + "```")
            return

        if team[0] == "sp":
            teamname = ' '.join(team[1:]).title()
            if teamname == "Nats":
                teamname = "Nationals"
            scoring_plays = mymlbstats.list_scoring_plays(teamname, delta)
            print(teamname,scoring_plays)
            if len(scoring_plays) > 0:
                output = "```"
                lastinning = ""
                for play in scoring_plays:
                    if play[0] != lastinning:
                        if len(lastinning) != 0:
                            output = output + "```\n```"
                            if len(output) + len(play[0]) > 1800:
                                await self.bot.say(output[:-3])
                                output = "```"
                        output = output + play[0] + "\n"
                        lastinning = play[0]
                    output = output + "\t" + play[1] + "\n"
                output = output + "```"
                await self.bot.say(output)
                return
            else:
                await self.bot.say("No scoring plays")
                return
        elif team[0] == 'line':
            player = '+'.join(team[1:])
            out = mymlbstats.get_player_line(player, delta)
            if len(out) == 0:
                await self.bot.say("couldn't find stats")
            else:
                await self.bot.say("```%s```" % out)
            return
        elif team[0] == 'stats':
            player = '+'.join(team[1:])
            await self.bot.say("```%s```" % mymlbstats.get_player_season_stats(player))
            return
        elif team[0].endswith("leaders") or team[0].endswith("losers"):
            stat = team[1]
            opts = []
            for i in range(2,len(team)):
                opts.append(team[i])
            stattype = 'bat'
            if team[0].startswith('p'):
                t = team[0][1:]
                stattype = 'pit'
            else:
                t = team[0]
            if t == "losers":
                opts.append("reverse=yes")
            fg = FG(stat.lower(),options=opts)
            output = fg.get_stat_leaders_str(stattype=stattype)
            await self.bot.say(output)
            return
        elif team[0] == 'ohtani':
            out = mymlbstats.get_ohtani_line(delta)
            if len(out) > 0:
                await self.bot.say("```%s```" % out)
            else:
                await self.bot.say("No stats found")
            return
        else:
            teamname = ' '.join(team).lower()
        if teamname == "nats":
            teamname = "nationals"

        if teamname in ['nle','nlc','nlw','ale','alc','alw','nlwc','alwc']:
            output = mymlbstats.get_div_standings(teamname)
            await self.bot.say(output)
            return

        output = mymlbstats.get_single_game(teamname,delta=delta)
        if len(output) > 0:
            await self.bot.say("```python\n" + output + "```")
        else:
            await self.bot.say("no games found")

    # @commands.command()
    # async def mlbd(self, year:int, month:int, day:int, *team:str):
    #     """<yyyy mm dd> to show all of that day's games; add a team for just one"""
    #     if len(team) == 0:
    #         gameday = mlbgame.day(year, month, day)
    #         output = "The day's scores:\n```python\n"
    #         for game in gameday:
    #             output = output + mymlbgame.get_game_str(game.game_id) +'\n'
    #         await self.bot.say(output.strip() + "```")
    #         return
    #     else:
    #         team = team[0].title()
    #         gameday = mlbgame.day(year, month, day, home=team, away=team)

        # if len(gameday) > 0 :
        #     game = gameday[0]
        #     id = game.game_id
        #     box = mlbgame.game.GameBoxScore(mlbgame.game.box_score(id))
        #     s = game.nice_score() #+ "\n```" + box.print_scoreboard() + "```"
        #     await self.bot.say(s)
        
def setup(bot):
    bot.add_cog(Baseball(bot))

class FG:
    bdash = ['bb%','k%','iso','babip','avg','obp','slg','woba','wrc+','bsr','off','def','fwar',9]
    bstd = ['g','ab','pa','h','1b','2b','3b','hr','r','rbi','bb','ibb','so','hbp','sf','sh','gdp','sb','cs',3]
    badv = ['ops',10]
    batting = [bdash,bstd,badv]
    pdash = ['w','l','sv','g','gs','ip','k/9','bb/9','hr/9','babip','lob%','gb%','hr/fb','era','fip','xfip','fwar',3]
    pstd = ['w','l','era','g','gs','cg','sho','sv','hld','bs','ip','tbf','h','r','er','hr','bb','ibb','hbp','wp','bk','so',3]
    padv = ['k/9','bb/9','k/bb','hr/9','k%','bb%','k-bb%','avg','whip','babip','lob%','era-','fip-','xfip-','era','fip','e-f','xfip','siera',3]
    pitching = [pdash,pstd,padv]

    asec = ['era','fip','xfip','whip','era-','fip-','xfip-','babip']

    baseurl = "https://www.fangraphs.com/leaders.aspx?"

    def __init__(self, stat, options=[]):
        self.stat = stat
        self.options = options
        self.order = ['d','a']

    def _get_options_str(self):
        # set defaults
        pos = 'all'
        lg = 'all'
        qual = 'y'
        season = '2018'
        team = '0'

        for s in self.options:
            if '=' in s:
                t = s.split('=')
                opt = t[0]
                val = t[1]
                if opt == 'pos':
                    pos = val
                elif opt == 'lg':
                    lg = val
                elif opt == 'qual':
                    qual = val
                elif opt == 'season':
                    season = val
                elif opt == 'team':
                    team = val
                elif opt == 'reverse':
                    self.order = ['a','d']
        return "pos=%s&lg=%s&qual=%s&season=%s&team=%s" % (pos,lg,qual,season,team)

    def get_stat(self, stattype='bat'):
        #parse options
        optstr = self._get_options_str()
        url = self.baseurl + optstr + "&stats="+stattype
        if stattype == 'bat':
            list = self.batting
        elif stattype == 'pit':
            list = self.pitching
        count = -1
        found = False
        for l in list:
            if self.stat in l:
                found = True
                if count == -1:
                    count = 8
                index = l.index(self.stat) + l[-1]
                order = self.order[0]
                if self.stat in self.asec:
                    order = self.order[1]
                url = url + "&type=%d&sort=%d,%s" % (count,index, order)
                break
            count += 1
        if not found:
            return "No matching stat"
        print(url)
        req = Request(url, headers={'User-Agent' : "ubuntu"})
        s = urlopen(req).read().decode('utf-8')
        srchstr = "<table class=\"rgMasterTable\""
        endstr = "</table>"
        s = s[s.find(srchstr)+len(srchstr):]
        s = s[:s.find(endstr)+len(endstr)]
        soup = BeautifulSoup(s,'html.parser')
        list = []
        headers = soup.find_all("th", class_="rgHeader")
        row = []
        for h in headers:
            row.append(h.get_text())
        list.append((row[1],row[2],row[index]))
        rows = soup.find_all("tr", {'class':['rgRow','rgAltRow']})
        for r in rows:
            cells = r.find_all('td')
            row = []
            for c in cells:
                row.append(c.get_text())
            list.append((row[1],row[2],row[index]))
        return list

    def get_stat_leaders_str(self,len=10,stattype='bat'):
        list = self.get_stat(stattype=stattype)
        if list == "No matching stat":
            return "```%s```" % list
        output = "```"
        for i in range(len+1): #+1 to include title row
            l = list[i]
            output = output + l[0].ljust(20) + l[2].rjust(5) + "\n"
        output = output + "```"
        return output

if __name__ == "__main__":
    fg = FG('fwar')
    print(fg.get_stat_leaders_str())
