from discord.ext import commands
import covid

class Temp():
    def __init__(self,bot):
        self.bot = bot

    @commands.command()
    async def covid(self,*arg:str):
        """display information about COVID-19"""
        await self.bot.say(covid.get_us())

def setup(bot):
    bot.add_cog(Temp(bot))
