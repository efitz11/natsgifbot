import discord
from discord.ext import commands
import cfbgame, nflgame, nhlscores, cbbgame

class Sports():
    def __init__(self,bot):
        self.bot = bot
        
    @commands.command()
    async def cfb(self,*team:str):
        """display score of team's cfb game"""
        t = ' '.join(team)
        await self.bot.say(cfbgame.get_game(t))
        
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

        
def setup(bot):
    bot.add_cog(Sports(bot))