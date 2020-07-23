from discord.ext import commands
import covid

class Temp(commands.Cog):
    def __init__(self,bot):
        self.bot = bot

    @commands.command()
    async def covid(self, ctx, *arg:str):
        """display information about COVID-19"""
        # if len(arg) == 0:
        #     await ctx.send(covid.get_us())
        # else:
        #     if not arg[0].startswith('+') and not arg[0].startswith('-'):
        #         await ctx.send(covid.get_state(arg[0]))
        await ctx.send(covid.get_usa())

def setup(bot):
    bot.add_cog(Temp(bot))
