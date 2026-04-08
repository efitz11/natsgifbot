import discord
from discord import app_commands
from discord.ext import commands

class MLBSlash(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Create a slash command group: /mlb
    mlb = app_commands.Group(name="mlb", description="MLB stats and scores commands")

    @mlb.command(name="score", description="Get today's MLB games or a specific team's game")
    @app_commands.describe(team="The team abbreviation to search for (e.g. wsh, lad). Leave blank for all.")
    async def score(self, interaction: discord.Interaction, team: str = None):
        # Defer the response immediately. The MLB API might take longer than 3 seconds to respond.
        await interaction.response.defer()

        # Fetch the games using our new async API client
        games = await self.bot.mlb_client.get_todays_games(team_abbrev=team)

        if games:
            output = "\n\n".join([game.format_score_line() for game in games])
            
            # Truncate if the output exceeds Discord's 2000 character limit (optional safeguard)
            if len(output) > 1900:
                output = output[:1900] + "\n... (truncated for Discord)"
            
            await interaction.followup.send(f"```python\n{output}\n```")
        else:
            await interaction.followup.send("No games found.")

async def setup(bot):
    await bot.add_cog(MLBSlash(bot))