import discord
from discord.ext import commands

from urllib.request import urlopen, Request
import urllib.parse
from datetime import datetime, timedelta, time

import mlbgame, mymlbgame
import mymlbstats

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
        elif team[0] == 'leaders':
            stat = team[1]
            output = '```'
            leaders = mymlbstats.get_stat_leader(stat)
            if len(leaders) == 0:
                await self.bot.say('not found')
                return
            for p in leaders:
                name = p[0].ljust(20)
                team = p[1].ljust(3)
                val  = p[2].rjust(5)
                output = output + "%s %s %s\n" % (val, team, name)
            output = output + "```"
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