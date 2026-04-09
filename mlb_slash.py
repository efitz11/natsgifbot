import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta

def parse_date(date_str: str) -> str:
    """Parses a user input date string into YYYY-MM-DD format."""
    # Use Eastern Time as the baseline for MLB dates
    now = datetime.utcnow() - timedelta(hours=5)
    if not date_str:
        return None
        
    date_str = date_str.lower().strip()
    if date_str == 'yesterday':
        return (now - timedelta(days=1)).strftime("%Y-%m-%d")
    elif date_str == 'tomorrow':
        return (now + timedelta(days=1)).strftime("%Y-%m-%d")
    elif date_str.startswith('+') or date_str.startswith('-'):
        try:
            days = int(date_str)
            return (now + timedelta(days=days)).strftime("%Y-%m-%d")
        except ValueError:
            pass
    elif '/' in date_str or '-' in date_str:
        parts = date_str.replace('-', '/').split('/')
        try:
            month, day = int(parts[0]), int(parts[1])
            year = int(parts[2]) if len(parts) == 3 else now.year
            if year < 100: year += 2000
            return f"{year:04d}-{month:02d}-{day:02d}"
        except (ValueError, IndexError):
            pass
            
    return None

class MLBSlash(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Create a slash command group: /mlb
    mlb = app_commands.Group(name="mlb", description="MLB stats and scores commands")

    @mlb.command(name="score", description="Get today's MLB games or a specific team's game")
    @app_commands.describe(team="The team abbreviation or name to search for (e.g. wsh, nationals, lad). Leave blank for all.")
    @app_commands.describe(date="A specific date (e.g. 4/7/26, yesterday, +2, -5)")
    async def score(self, interaction: discord.Interaction, team: str = None, date: str = None):
        # Defer the response immediately. The MLB API might take longer than 3 seconds to respond.
        await interaction.response.defer()

        # Parse the date if provided
        parsed_date = parse_date(date)

        # Fetch the games using our new async API client
        games = await self.bot.mlb_client.get_todays_games(team_query=team, date=parsed_date)

        if games:
            embeds = []
            title = f"MLB Scores ({parsed_date})" if parsed_date else "MLB Scores"
            current_embed = discord.Embed(title=title, color=discord.Color.blue())
            
            for game in games:
                # Use emojis in the field title to indicate game status
                if game.abstract_state == "Live":
                    name = f"🔴 {game.away.abbreviation} @ {game.home.abbreviation} - Live"
                elif game.abstract_state == "Final":
                    final_str = f"Final/{game.inning}" if game.inning != 9 and game.inning > 0 else "Final"
                    name = f"🏁 {game.away.abbreviation} @ {game.home.abbreviation} - {final_str}"
                else:
                    name = f"🗓️ {game.away.abbreviation} @ {game.home.abbreviation} - {game.status}"

                value = f"```python\n{game.format_score_line()}\n```"
                
                # Discord limits embeds to 25 fields and 6000 total characters
                if len(current_embed.fields) >= 25 or len(current_embed) + len(name) + len(value) > 5900:
                    embeds.append(current_embed)
                    current_embed = discord.Embed(title=f"{title} (Cont.)", color=discord.Color.blue())
                    
                current_embed.add_field(name=name, value=value, inline=False)
                
            embeds.append(current_embed)
            await interaction.followup.send(embeds=embeds)
        else:
            await interaction.followup.send("No games found.")

async def setup(bot):
    await bot.add_cog(MLBSlash(bot))