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
        """<team> to show today's game, or blank to show all games"""
        now = datetime.now() - timedelta(hours=3)
        if len(team) == 0:
            output = mymlbstats.get_all_game_info()
            await self.bot.say("```python\n" + output + "```")
            return

            day = mlbgame.day(now.year, now.month, now.day)
            if len(day) == 0:
                await self.bot.say("No games today.")
                return
            output = "Today's scores:\n```python\n"
            day_sorted = []
            for game in day:
                day_sorted.append((game.game_start_time,game))
            day_sorted.sort(key=lambda tup: tup[0])
            for game in day_sorted:
                try:
                    output = output + mymlbgame.get_game_str(game[1].game_id) +'\n'
                except Exception as e:
                    print(e)
                    continue
            await self.bot.say(output.strip() + "```")
            return
        
        teamname = team[0].title()
        if teamname == "Nats":
            teamname = "Nationals"

        output = mymlbstats.get_single_game(teamname)
        #day = mlbgame.day(now.year, now.month, now.day, home=teamname, away=teamname)
        #
        #if len(day) > 0 :
        #    game = day[0]
        #    id = game.game_id
        #    output = mymlbgame.get_game_str(id,lastplay=True)
        await self.bot.say("```python\n" + output + "```")

    @commands.command()
    async def mlbd(self, year:int, month:int, day:int, *team:str):
        """<yyyy mm dd> to show all of that day's games; add a team for just one"""
        if len(team) == 0:
            gameday = mlbgame.day(year, month, day)
            output = "The day's scores:\n```python\n"
            for game in gameday:
                output = output + mymlbgame.get_game_str(game.game_id) +'\n'
            await self.bot.say(output.strip() + "```")
            return
        else:
            team = team[0].title()
            gameday = mlbgame.day(year, month, day, home=team, away=team)

        if len(gameday) > 0 :
            game = gameday[0]
            id = game.game_id
            box = mlbgame.game.GameBoxScore(mlbgame.game.box_score(id))
            s = game.nice_score() #+ "\n```" + box.print_scoreboard() + "```"
            await self.bot.say(s)
        
def setup(bot):
    bot.add_cog(Baseball(bot))