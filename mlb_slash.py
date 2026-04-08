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
            embeds = []
            current_embed = discord.Embed(title="MLB Scores", color=discord.Color.blue())
            
            for game in games:
                # Use emojis in the field title to indicate game status
                if game.abstract_state == "Live":
                    name = f"🔴 {game.away.abbreviation} @ {game.home.abbreviation} - Live"
                elif game.abstract_state == "Final":
                    name = f"🏁 {game.away.abbreviation} @ {game.home.abbreviation} - Final"
                else:
                    name = f"🗓️ {game.away.abbreviation} @ {game.home.abbreviation} - {game.status}"

                value = f"```python\n{game.format_score_line()}\n```"
                
                # Discord limits embeds to 25 fields and 6000 total characters
                if len(current_embed.fields) >= 25 or len(current_embed) + len(name) + len(value) > 5900:
                    embeds.append(current_embed)
                    current_embed = discord.Embed(title="MLB Scores (Cont.)", color=discord.Color.blue())
                    
                current_embed.add_field(name=name, value=value, inline=False)
                
            embeds.append(current_embed)
            await interaction.followup.send(embeds=embeds)
        else:
            await interaction.followup.send("No games found.")

async def setup(bot):
    await bot.add_cog(MLBSlash(bot))