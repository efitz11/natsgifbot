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
    milb = app_commands.Group(name="milb", description="MiLB stats and scores commands")

    @mlb.command(name="line", description="Get a player's stat line for today or a specific date")
    @app_commands.describe(player="The player to search for")
    @app_commands.describe(date="A specific date (e.g. 4/7/26, yesterday, +2, -5)")
    async def line(self, interaction: discord.Interaction, player: str, date: str = None):
        await interaction.response.defer()
        parsed_date = parse_date(date)

        # Because we linked autocomplete below, "player" will typically contain the exact Player ID
        stats_list = await self.bot.mlb_client.get_player_game_stats(player, date=parsed_date)

        if not stats_list:
            await interaction.followup.send("Could not find stats for that player.")
            return

        embed = discord.Embed(color=discord.Color.blue())
        
        if len(stats_list) == 1:
            stats = stats_list[0]
            embed.title = f"{stats.player_name} ({stats.team_abbrev}) {stats.date} {'vs' if stats.is_home else '@'} {stats.opp_abbrev}"
            embed.description = f"```python\n{stats.format_discord_code_block()}\n```"
        else:
            stats = stats_list[0]
            embed.title = f"{stats.player_name} ({stats.team_abbrev}) - {stats.date}"
            for i, s in enumerate(stats_list, 1):
                name = f"Game {i}: {'vs' if s.is_home else '@'} {s.opp_abbrev}"
                embed.add_field(name=name, value=f"```python\n{s.format_discord_code_block()}\n```", inline=False)
                
        if stats_list[0].headshot_url:
            embed.set_thumbnail(url=stats_list[0].headshot_url)
                
        await interaction.followup.send(embed=embed)

    @line.autocomplete('player')
    async def player_autocomplete(self, interaction: discord.Interaction, current: str):
        if len(current) < 3:
            return []
        players = await self.bot.mlb_client.search_players(current)
        
        nats_choices = []
        other_choices = []
        
        for p in players:
            team = p.get('name_display_club')
            # The Savant API returns mlb=1 for active Major Leaguers
            if team and p.get('mlb') == 1:
                name = p.get('name', 'Unknown')
                choice = app_commands.Choice(name=f"{name} ({team})"[:100], value=str(p.get('id', '')))
                
                if "nationals" in team.lower():
                    nats_choices.append(choice)
                else:
                    other_choices.append(choice)
                    
        # Combine and return up to 25 matches for Discord's popup menu
        return (nats_choices + other_choices)[:25]

    @mlb.command(name="abs", description="Get a player's at-bats and video highlights for today or a specific date")
    @app_commands.describe(player="The player to search for")
    @app_commands.describe(date="A specific date (e.g. 4/7/26, yesterday, +2, -5)")
    async def abs_command(self, interaction: discord.Interaction, player: str, date: str = None):
        await self._send_player_abs(interaction, player, date, milb=False)

    @abs_command.autocomplete('player')
    async def abs_player_autocomplete(self, interaction: discord.Interaction, current: str):
        return await self.player_autocomplete(interaction, current)

    @mlb.command(name="sp", description="Get all scoring plays for a team in a given game.")
    @app_commands.describe(team="The team to get scoring plays for (e.g. wsh, nationals)")
    @app_commands.describe(date="A specific date (e.g. 4/7/26, yesterday, +2, -5)")
    async def scoring_plays(self, interaction: discord.Interaction, team: str, date: str = None):
        await interaction.response.defer()
        parsed_date = parse_date(date)

        games = await self.bot.mlb_client.get_games_with_scoring_plays(team, date=parsed_date)

        if not games:
            await interaction.followup.send("Could not find a game for that team on the specified date.")
            return
        
        embeds = []
        for i, game in enumerate(games, 1):
            embed = discord.Embed(color=discord.Color.blue())

            final_str = f"{game.status}/{game.inning}" if game.inning != 9 and game.inning > 0 else game.status
            title = f"🏁 {game.away.abbreviation} @ {game.home.abbreviation} - {final_str}" if game.abstract_state == "Final" else \
                    f"🔴 {game.away.abbreviation} @ {game.home.abbreviation} - {game.status}" if game.abstract_state == "Live" else \
                    f"🗓️ {game.away.abbreviation} @ {game.home.abbreviation} - {game.status}"
            if len(games) > 1: title += f" (Game {i})"
            embed.title = title
            
            desc = f"```python\n{game.format_score_line()}\n```\n"
            if game.scoring_plays:
                desc += "### Scoring Plays\n"
                for sp in game.scoring_plays:
                    desc += f"**{sp.inning.title()}:** {sp.description}\n"
                    if sp.video_url: desc += f"> [🎥 **{sp.video_blurb}**]({sp.video_url})\n"
                    desc += "\n"
            else:
                desc += "\nNo scoring plays found for this team in this game."

            embed.description = desc[:4096].strip()
            embeds.append(embed)

        await interaction.followup.send(embeds=embeds)

    @mlb.command(name="stats", description="Get a player's season or career stats")
    @app_commands.describe(player="The player to search for")
    @app_commands.describe(year="A specific year (e.g. 2023). Leave blank for most recent.")
    @app_commands.describe(stat_type="Hitting or Pitching. Leave blank for default.")
    @app_commands.describe(career="Get career totals instead of a single season")
    @app_commands.choices(stat_type=[
        app_commands.Choice(name="Hitting", value="hitting"),
        app_commands.Choice(name="Pitching", value="pitching")
    ])
    async def stats(self, interaction: discord.Interaction, player: str, year: str = None, stat_type: app_commands.Choice[str] = None, career: bool = False):
        await interaction.response.defer()

        s_type = stat_type.value if stat_type else None

        season_stats_list = await self.bot.mlb_client.get_player_season_stats(player, stat_type=s_type, year=year, career=career)

        if not season_stats_list:
            await interaction.followup.send("Could not find stats for that player.")
            return

        embed = discord.Embed(color=discord.Color.blue())
        
        first_stats = season_stats_list[0]
        display_team = first_stats.team_abbrev
        if not first_stats.is_career and first_stats.stats:
            teams = []
            for s in first_stats.stats:
                t = s.get('team')
                if t and t not in ['MLB', 'MiLB'] and t not in teams:
                    teams.append(t)
            if teams:
                display_team = "/".join(teams)

        if first_stats.is_career:
            years_str = f" ({first_stats.years})" if first_stats.years and first_stats.years != "Career" else ""
            if len(season_stats_list) > 1:
                embed.title = f"Career Stats for {first_stats.player_name}{years_str}"
            else:
                embed.title = f"Career {first_stats.stat_type.capitalize()} Stats for {first_stats.player_name}{years_str}"
        else:
            if len(season_stats_list) > 1:
                embed.title = f"{first_stats.years} Stats for {first_stats.player_name} ({display_team})"
            else:
                embed.title = f"{first_stats.years} {first_stats.stat_type.capitalize()} Stats for {first_stats.player_name} ({display_team})"
            
        description = f"{first_stats.info_line}\n\n"
        for st in season_stats_list:
            if len(season_stats_list) > 1:
                prefix = "Career " if st.is_career else f"{st.years} "
                description += f"*{prefix}{st.stat_type.capitalize()}*\n"
            description += f"```python\n{st.format_discord_code_block()}\n```\n"
            
        embed.description = description.strip()
        if first_stats.headshot_url:
            embed.set_thumbnail(url=first_stats.headshot_url)
        
        await interaction.followup.send(embed=embed)

    @stats.autocomplete('player')
    async def stats_player_autocomplete(self, interaction: discord.Interaction, current: str):
        return await self.player_autocomplete(interaction, current)

    @milb.command(name="stats", description="Get a minor league player's season or career stats")
    @app_commands.describe(player="The minor league player to search for")
    @app_commands.describe(year="A specific year (e.g. 2023). Leave blank for most recent.")
    @app_commands.describe(stat_type="Hitting or Pitching. Leave blank for default.")
    @app_commands.describe(career="Get career totals instead of a single season")
    @app_commands.choices(stat_type=[
        app_commands.Choice(name="Hitting", value="hitting"),
        app_commands.Choice(name="Pitching", value="pitching")
    ])
    async def milb_stats(self, interaction: discord.Interaction, player: str, year: str = None, stat_type: app_commands.Choice[str] = None, career: bool = False):
        await interaction.response.defer()
        s_type = stat_type.value if stat_type else None
        season_stats_list = await self.bot.mlb_client.get_player_season_stats(player, stat_type=s_type, year=year, career=career, milb=True)

        if not season_stats_list:
            await interaction.followup.send("Could not find stats for that minor league player.")
            return

        embed = discord.Embed(color=discord.Color.blue())
        first_stats = season_stats_list[0]
        display_team = first_stats.team_abbrev
        if not first_stats.is_career and first_stats.stats:
            teams = [s.get('team') for s in first_stats.stats if s.get('team') and s.get('team') not in ['MLB', 'MiLB']]
            if teams:
                display_team = "/".join(dict.fromkeys(teams)) # Removes duplicates while preserving order
                
        if first_stats.parent_org_abbrev:
            display_team = f"{display_team}-{first_stats.parent_org_abbrev}"

        years_str = f" ({first_stats.years})" if first_stats.years and first_stats.years != "Career" else ""
        embed.title = f"{'Career' if first_stats.is_career else first_stats.years} Stats for {first_stats.player_name}{years_str if first_stats.is_career else ' (' + display_team + ')'}"
            
        description = f"{first_stats.info_line}\n\n"
        for st in season_stats_list:
            if len(season_stats_list) > 1:
                description += f"*{'Career ' if st.is_career else st.years + ' '}{st.stat_type.capitalize()}*\n"
            description += f"```python\n{st.format_discord_code_block()}\n```\n"
            
        embed.description = description.strip()
        if first_stats.headshot_url:
            embed.set_thumbnail(url=first_stats.headshot_url)
        await interaction.followup.send(embed=embed)

    @milb_stats.autocomplete('player')
    async def milb_stats_player_autocomplete(self, interaction: discord.Interaction, current: str):
        if len(current) < 3: return []
        players = await self.bot.mlb_client.search_players(current, milb=True)
        nats_choices, other_choices = [], []
        for p in players:
            team, name = p.get('name_display_club', 'Unknown'), p.get('name', 'Unknown')
            choice = app_commands.Choice(name=f"{name} ({team})"[:100], value=str(p.get('id', '')))
            nats_choices.append(choice) if any(aff in team.lower() for aff in ['nationals', 'senators', 'red wings', 'blue rocks', 'frednats', 'rochester', 'harrisburg', 'wilmington', 'fredericksburg']) else other_choices.append(choice)
        return (nats_choices + other_choices)[:25]

    @milb.command(name="line", description="Get a minor league player's stat line for today or a specific date")
    @app_commands.describe(player="The minor league player to search for")
    @app_commands.describe(date="A specific date (e.g. 4/7/26, yesterday, +2, -5)")
    async def milb_line(self, interaction: discord.Interaction, player: str, date: str = None):
        await interaction.response.defer()
        parsed_date = parse_date(date)

        stats_list = await self.bot.mlb_client.get_player_game_stats(player, date=parsed_date, milb=True)

        if not stats_list:
            await interaction.followup.send("Could not find stats for that minor league player.")
            return

        embed = discord.Embed(color=discord.Color.blue())
        
        if len(stats_list) == 1:
            stats = stats_list[0]
            embed.title = f"{stats.player_name} ({stats.team_abbrev}) {stats.date} {'vs' if stats.is_home else '@'} {stats.opp_abbrev}"
            embed.description = f"```python\n{stats.format_discord_code_block()}\n```"
        else:
            stats = stats_list[0]
            embed.title = f"{stats.player_name} ({stats.team_abbrev}) - {stats.date}"
            for i, s in enumerate(stats_list, 1):
                name = f"Game {i}: {'vs' if s.is_home else '@'} {s.opp_abbrev}"
                embed.add_field(name=name, value=f"```python\n{s.format_discord_code_block()}\n```", inline=False)
                
        if stats_list[0].headshot_url:
            embed.set_thumbnail(url=stats_list[0].headshot_url)
                
        await interaction.followup.send(embed=embed)

    @milb_line.autocomplete('player')
    async def milb_line_player_autocomplete(self, interaction: discord.Interaction, current: str):
        return await self.milb_stats_player_autocomplete(interaction, current)

    @milb.command(name="abs", description="Get a minor league player's at-bats and video highlights")
    @app_commands.describe(player="The minor league player to search for")
    @app_commands.describe(date="A specific date (e.g. 4/7/26, yesterday, +2, -5)")
    async def milb_abs(self, interaction: discord.Interaction, player: str, date: str = None):
        await self._send_player_abs(interaction, player, date, milb=True)

    @milb_abs.autocomplete('player')
    async def milb_abs_player_autocomplete(self, interaction: discord.Interaction, current: str):
        return await self.milb_stats_player_autocomplete(interaction, current)

    async def _send_player_abs(self, interaction: discord.Interaction, player: str, date: str, milb: bool):
        await interaction.response.defer()
        parsed_date = parse_date(date)

        stats_list = await self.bot.mlb_client.get_player_game_stats(player, date=parsed_date, milb=milb, include_abs=True)

        if not stats_list:
            await interaction.followup.send("Could not find stats for that player.")
            return

        embeds = []
        for i, stats in enumerate(stats_list, 1):
            embed = discord.Embed(color=discord.Color.blue())
            
            if len(stats_list) == 1:
                embed.title = f"{stats.player_name} ({stats.team_abbrev}) {stats.date} {'vs' if stats.is_home else '@'} {stats.opp_abbrev}"
            else:
                embed.title = f"{stats.player_name} ({stats.team_abbrev}) - {stats.date} (Game {i}: {'vs' if stats.is_home else '@'} {stats.opp_abbrev})"
                
            if stats.headshot_url:
                embed.set_thumbnail(url=stats.headshot_url)
                
            desc = f"```python\n{stats.format_discord_code_block()}\n```\n"
            
            if stats.at_bats:
                desc += "### Play-by-Play\n"
                for ab in stats.at_bats:
                    if not ab.is_complete:
                        desc += f"**{ab.inning.title()}:** Currently at bat.\n\n"
                        continue
                        
                    scoring = "__" if ab.is_scoring else ""
                    ab_text = f"**{ab.inning.title()}:** {scoring}With **{ab.pitcher_name}** pitching, {ab.description}{scoring}"
                    
                    if ab.pitch_data or ab.statcast_data:
                        extras = " | ".join(filter(None, [ab.pitch_data, ab.statcast_data]))
                        ab_text += f" *({extras})*"
                        
                    desc += ab_text + "\n"
                    
                    if ab.video_url:
                        desc += f"> [🎥 **{ab.video_blurb}**]({ab.video_url})\n"
                        
                    desc += "\n"
                    
            if len(desc) > 4096:
                desc = desc[:4093] + "..."
                
            embed.description = desc.strip()
            embeds.append(embed)
            
        await interaction.followup.send(embeds=embeds)

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
                    name = f"🔴 {game.away.abbreviation} @ {game.home.abbreviation} - {game.status}"
                elif game.abstract_state == "Final":
                    final_str = f"{game.status}/{game.inning}" if game.inning != 9 and game.inning > 0 else game.status
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

    @mlb.command(name="next", description="Get the upcoming games for a team")
    @app_commands.describe(team="The team abbreviation or name (e.g. wsh, dodgers)")
    @app_commands.describe(games="Number of games to show (default 3, max 10)")
    async def next_games(self, interaction: discord.Interaction, team: str, games: int = 3):
        await self._send_schedule(interaction, team, games, past=False)

    @mlb.command(name="past", description="Get the recently completed games for a team")
    @app_commands.describe(team="The team abbreviation or name (e.g. wsh, dodgers)")
    @app_commands.describe(games="Number of games to show (default 3, max 10)")
    async def past_games(self, interaction: discord.Interaction, team: str, games: int = 3):
        await self._send_schedule(interaction, team, games, past=True)

    async def _send_schedule(self, interaction: discord.Interaction, team: str, num_games: int, past: bool):
        await interaction.response.defer()
        num_games = max(1, min(10, num_games))

        games = await self.bot.mlb_client.get_team_schedule(team, num_games=num_games, past=past)

        if not games:
            await interaction.followup.send(f"Could not find any {'past' if past else 'upcoming'} games for that team.")
            return

        direction = "Past" if past else "Next"
        
        target_abbr = team.upper()
        query = team.lower()
        aliases = {"nats": "nationals", "yanks": "yankees", "cards": "cardinals", "dbacks": "diamondbacks", "barves": "braves"}
        query = aliases.get(query, query)
        for g in games:
            if query == g.away.abbreviation.lower() or query in g.away.name.lower():
                target_abbr = g.away.abbreviation
                break
            elif query == g.home.abbreviation.lower() or query in g.home.name.lower():
                target_abbr = g.home.abbreviation
                break

        embeds = []
        title = f"{direction} {len(games)} Games for {target_abbr}"
        current_embed = discord.Embed(title=title, color=discord.Color.blue())
        
        for game in games:
            date_str = game.game_date_str or "Unknown Date"
            if game.abstract_state == "Live":
                name = f"🔴 {game.away.abbreviation} @ {game.home.abbreviation} - {game.status} ({date_str})"
            elif game.abstract_state == "Final":
                final_str = f"{game.status}/{game.inning}" if game.inning != 9 and game.inning > 0 else game.status
                name = f"🏁 {game.away.abbreviation} @ {game.home.abbreviation} - {final_str} ({date_str})"
            else:
                name = f"🗓️ {game.away.abbreviation} @ {game.home.abbreviation} - {game.status} ({date_str})"

            value = f"```python\n{game.format_score_line()}\n```"
            
            if len(current_embed.fields) >= 25 or len(current_embed) + len(name) + len(value) > 5900:
                embeds.append(current_embed)
                current_embed = discord.Embed(title=f"{title} (Cont.)", color=discord.Color.blue())
                
            current_embed.add_field(name=name, value=value, inline=False)
            
        embeds.append(current_embed)
        await interaction.followup.send(embeds=embeds)

async def setup(bot):
    await bot.add_cog(MLBSlash(bot))