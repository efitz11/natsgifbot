import discord
from discord.ext import commands
import cfbgame, nflgame, nhlscores, cbbgame, softball

class Sports():
    def __init__(self,bot):
        self.bot = bot

    def _find_delta(self, args):
        delta = None
        if len(args) > 0 and (args[-1].startswith('-') or args[-1].startswith('+')):
            delta = int(args[-1])
            args = args[:-1]
        return delta, args

    @commands.command()
    async def cfb(self,*team:str):
        """display score of team's cfb game"""
        delta, team = self._find_delta(team)
        t = ' '.join(team)
        if delta is None:
            await self.bot.say(cfbgame.get_game(t))
        else:
            await self.bot.say(cfbgame.get_game(t, delta=delta))

    @commands.command()
    async def fcs(self,*team:str):
        """display score of an FCS game

        this command will only display one team at a time"""
        delta, team = self._find_delta(team)
        t = ' '.join(team)
        if delta is None:
            await self.bot.say(cfbgame.get_game(t,fcs=True))
        else:
            await self.bot.say(cfbgame.get_game(t, delta=delta, fcs=True))

    @commands.command()
    async def cbb(self,*team:str):
        """display score of team's cfb game"""
        delta = None
        if len(team) > 0:
            if team[-1].startswith('-') or team[-1].startswith('+'):
                delta = team[-1]
                if len(team) > 1:
                    t = ' '.join(team[:-1])
                else:
                    t = None
            else:
                t = ' '.join(team)
        else:
            t = None
            
        if delta is None:
            await self.bot.say(cbbgame.get_game(t))
        else:
            await self.bot.say(cbbgame.get_game(t,delta=int(delta)))
            
    @commands.command()
    async def nfl(self,*team:str):
        """display score(s) of nfl game"""
        t = ' '.join(team)
        await self.bot.say(nflgame.get_game(t,'nfl'))
        
    @commands.command()
    async def nba(self,*team:str):
        """display score(s) of nba game"""
        t = ' '.join(team)
        await self.bot.say(nflgame.get_game(t,'nba'))

    @commands.command()
    async def nhl(self,*team:str):
        """display score(s) of nhl game"""
        t = ' '.join(team)
        await self.bot.say(nhlscores.get_scores(t))
        
    @commands.command()
    async def fas(self,*args:str):
        """get FAS scores or standings to try and inflate our egos by putting FAS on the same level as major sports"""
        if len(args) > 0:
            if args[0] == "standings":
                await self.bot.say(softball.fas_standings())
            else:
                await self.bot.say(softball.fas_schedule(args[0]))
        else:
            await self.bot.say(softball.fas_schedule())

        
def setup(bot):
    bot.add_cog(Sports(bot))