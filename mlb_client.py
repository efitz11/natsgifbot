import aiohttp
import asyncio
import urllib.parse
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class Team:
    id: int
    name: str
    abbreviation: str
    score: int
    hits: int = 0
    errors: int = 0

@dataclass
class Game:
    game_pk: int
    status: str
    abstract_state: str
    away: Team
    home: Team
    inning: int = 0
    is_top_inning: bool = True
    outs: int = 0
    strikes: int = 0
    balls: int = 0
    bases: str = "---"
    pitcher: str = ""
    pitch_count: int = 0
    batter: str = ""
    lineup_pos_batter: str = ""
    on_deck: str = ""
    lineup_pos_on_deck: str = ""
    last_play_desc: str = ""
    last_play_pitcher: str = ""
    last_pitch_type: str = ""
    last_pitch_speed: float = 0.0
    statcast_dist: float = 0.0
    statcast_speed: float = 0.0
    statcast_angle: float = 0.0

    @classmethod
    def from_api_json(cls, data: dict):
        """Parses the raw MLB Stats API JSON into a clean Python object."""
        away_data = data['teams']['away']
        home_data = data['teams']['home']
        ls = data.get('linescore', {})
        
        away_team = Team(
            id=away_data['team']['id'],
            name=away_data['team']['name'],
            abbreviation=away_data['team'].get('abbreviation', away_data['team']['name'][:3].upper()),
            score=away_data.get('score', 0),
            hits=ls.get('teams', {}).get('away', {}).get('hits', 0),
            errors=ls.get('teams', {}).get('away', {}).get('errors', 0)
        )
        
        home_team = Team(
            id=home_data['team']['id'],
            name=home_data['team']['name'],
            abbreviation=home_data['team'].get('abbreviation', home_data['team']['name'][:3].upper()),
            score=home_data.get('score', 0),
            hits=ls.get('teams', {}).get('home', {}).get('hits', 0),
            errors=ls.get('teams', {}).get('home', {}).get('errors', 0)
        )
        
        game = cls(
            game_pk=data['gamePk'],
            status=data['status']['detailedState'],
            abstract_state=data['status']['abstractGameState'],
            away=away_team,
            home=home_team,
            inning=ls.get('currentInning', 0),
            is_top_inning=ls.get('isTopInning', True),
            outs=ls.get('outs', 0),
            strikes=ls.get('strikes', 0),
            balls=ls.get('balls', 0)
        )

        offense = ls.get('offense', {})
        defense = ls.get('defense', {})
        
        bases = "---"
        if 'first' in offense: bases = "1" + bases[1:]
        if 'second' in offense: bases = bases[:1] + "2" + bases[2:]
        if 'third' in offense: bases = bases[:2] + "3"
        game.bases = bases
        
        pitcher_data = defense.get('pitcher', {})
        game.pitcher = pitcher_data.get('lastName', '')
        
        if 'stats' in pitcher_data:
            for st in pitcher_data['stats']:
                if st.get('type', {}).get('displayName') == 'gameLog' and st.get('group', {}).get('displayName') == 'pitching':
                    game.pitch_count = st.get('stats', {}).get('pitchesThrown', 0)
                    break
        
        batter_data = offense.get('batter', {})
        game.batter = batter_data.get('lastName', '')
        on_deck_data = offense.get('onDeck', {})
        game.on_deck = on_deck_data.get('lastName', '')
        
        def find_lineup_pos(player_id, lineups):
            if not lineups: return ""
            for _, players in lineups.items():
                for i, p in enumerate(players):
                    if p.get('id') == player_id:
                        return str(i + 1)
            return ""
            
        lineups = data.get('lineups', {})
        if game.batter:
            game.lineup_pos_batter = find_lineup_pos(batter_data.get('id'), lineups)
        if game.on_deck:
            game.lineup_pos_on_deck = find_lineup_pos(on_deck_data.get('id'), lineups)
            
        last_play = data.get('previousPlay', {})
        if last_play and 'result' in last_play:
            game.last_play_desc = last_play['result'].get('description', '')
            game.last_play_pitcher = last_play.get('matchup', {}).get('pitcher', {}).get('fullName', '')
            
            play_events = last_play.get('playEvents', [])
            for event in play_events:
                if 'pitchData' in event:
                    game.last_pitch_speed = event['pitchData'].get('startSpeed') or 0.0
                    if 'details' in event and 'type' in event['details']:
                        game.last_pitch_type = event['details']['type'].get('description', '')
                if 'hitData' in event:
                    hd = event['hitData']
                    game.statcast_dist = hd.get('totalDistance') or 0.0
                    game.statcast_speed = hd.get('launchSpeed') or 0.0
                    game.statcast_angle = hd.get('launchAngle') or 0.0
        
        return game

    def format_score_line(self) -> str:
        """A simple formatter to output the game score for Discord."""
        away_base = f"{self.away.abbreviation.ljust(3)} {str(self.away.score).rjust(2)} {str(self.away.hits).rjust(2)} {self.away.errors}"
        home_base = f"{self.home.abbreviation.ljust(3)} {str(self.home.score).rjust(2)} {str(self.home.hits).rjust(2)} {self.home.errors}"

        if self.abstract_state == "Live" and self.status != "Delayed":
            outs_str = (int(self.outs) * '●') + ((3 - int(self.outs)) * '○')
            inning_half_str = "▲" if self.is_top_inning else "▼"
            
            pitcher_str = f"P: {self.pitcher}"
            if self.pitch_count > 0:
                pitcher_str += f" ({self.pitch_count} P)"
                
            away_line = f"{away_base} | {inning_half_str} {self.inning} | {self.bases.center(5)} | {pitcher_str}"
            
            count_str = f"({self.balls}-{self.strikes})"
            batter_str = f"{self.lineup_pos_batter}: {self.batter}" if self.lineup_pos_batter else f"B: {self.batter}"
            on_deck_str = f"{self.lineup_pos_on_deck}: {self.on_deck}" if self.lineup_pos_on_deck else f"OD: {self.on_deck}"
            home_line = f"{home_base} | {outs_str} | {count_str.center(5)} | {batter_str} {on_deck_str}"
            
            output = f"{away_line}\n{home_line}"
            
            if self.last_play_desc:
                output += f"\n\nLast Play: With {self.last_play_pitcher} pitching, {self.last_play_desc}\n"
                pitch_info = []
                if self.last_pitch_type:
                    pitch_info.append(f"Pitch: {self.last_pitch_type}, {self.last_pitch_speed:.2f} mph")
                if self.statcast_dist > 0 or self.statcast_speed > 0:
                    pitch_info.append(f"Statcast: {self.statcast_dist:.2f} ft, {self.statcast_speed:.2f} mph, {self.statcast_angle:.2f} degrees")
                if pitch_info:
                    output += "\n" + "\n".join(pitch_info)
            return output
        elif self.abstract_state == "Final":
            final_str = f"F/{self.inning}" if self.inning != 9 and self.inning > 0 else "F"
            return f"{away_base} | {final_str}\n{home_base} |"
        else:
            return f"{self.away.abbreviation.ljust(3)} {str(self.away.score).rjust(2)} | {self.status}\n{self.home.abbreviation.ljust(3)} {str(self.home.score).rjust(2)} |"

    def format_modern_score_line(self) -> str:
        """A modern Discord markdown formatter for the game score."""
        away_line = f"**{self.away.abbreviation} {self.away.score}** ({self.away.hits}H, {self.away.errors}E)"
        home_line = f"**{self.home.abbreviation} {self.home.score}** ({self.home.hits}H, {self.home.errors}E)"
        
        if self.abstract_state == "Live" and self.status != "Delayed":
            outs_str = (int(self.outs) * '●') + ((3 - int(self.outs)) * '○')
            inning_half_str = "▲" if self.is_top_inning else "▼"
            
            bases_emojis = ""
            bases_emojis += "⚾" if self.bases[0] == "1" else "♢"
            bases_emojis += "⚾" if self.bases[1] == "2" else "♢"
            bases_emojis += "⚾" if self.bases[2] == "3" else "♢"
            
            pitcher_str = f"**P:** {self.pitcher}" + (f" ({self.pitch_count}P)" if self.pitch_count > 0 else "")
            batter_str = f"**B:** {self.batter}"
            
            output = f"{away_line} @ {home_line}\n"
            output += f"**{inning_half_str} {self.inning}** | **Outs:** {outs_str} | **Count:** {self.balls}-{self.strikes} | **Bases:** {bases_emojis}\n"
            output += f"{pitcher_str} | {batter_str}\n"
            
            if self.last_play_desc:
                output += f"*{self.last_play_desc}*\n"
                
                pitch_info = []
                if self.last_pitch_type:
                    pitch_info.append(f"{self.last_pitch_type} ({self.last_pitch_speed:.1f} mph)")
                if self.statcast_dist > 0 or self.statcast_speed > 0:
                    pitch_info.append(f"{self.statcast_dist:.1f}ft / {self.statcast_speed:.1f}mph / {self.statcast_angle:.1f}°")
                
                if pitch_info:
                    output += f"> {' | '.join(pitch_info)}"
            return output
        elif self.abstract_state == "Final":
            final_str = f"Final/{self.inning}" if self.inning != 9 and self.inning > 0 else "Final"
            return f"{away_line} @ {home_line} | **{final_str}**"
        else:
            return f"{away_line} @ {home_line} | **{self.status}**"

@dataclass
class PlayerGameStats:
    player_name: str
    team_abbrev: str
    opp_abbrev: str
    is_home: bool
    date: str
    batting_stats: Optional[dict] = None
    pitching_stats: Optional[dict] = None
    pitching_dec: str = ""
    info_message: str = ""
    headshot_url: str = ""

    def format_discord_code_block(self) -> str:
        if self.info_message:
            return self.info_message

        output = ""

        if self.pitching_stats:
            s = self.pitching_stats
            output += " IP  H  R ER HR BB SO  P-S\n"
            output += f"{str(s.get('inningsPitched', '0.0')):>3} {s.get('hits', 0):>2} {s.get('runs', 0):>2} {s.get('earnedRuns', 0):>2} {s.get('homeRuns', 0):>2} {s.get('baseOnBalls', 0):>2} {s.get('strikeOuts', 0):>2} {s.get('pitchesThrown', 0):>2}-{s.get('strikes', 0)} {self.pitching_dec}\n\n"

        if self.batting_stats:
            s = self.batting_stats
            output += "AB H 2B 3B HR R RBI BB SO SB CS\n"
            output += f"{s.get('atBats', 0):>2} {s.get('hits', 0)} {s.get('doubles', 0):>2} {s.get('triples', 0):>2} {s.get('homeRuns', 0):>2} {s.get('runs', 0)} {s.get('rbi', 0):>3} {s.get('baseOnBalls', 0):>2} {s.get('strikeOuts', 0):>2} {s.get('stolenBases', 0):>2} {s.get('caughtStealing', 0):>2}\n\n"

        return output.strip()

@dataclass
class PlayerSeasonStats:
    player_name: str
    team_abbrev: str
    stat_type: str
    years: str
    is_career: bool
    info_line: str
    stats: List[dict]
    info_message: str = ""
    headshot_url: str = ""

    def format_discord_code_block(self) -> str:
        if self.info_message:
            return self.info_message

        if self.stat_type == "hitting":
            labels_list = [
                ['season', 'team', 'atBats', 'runs', 'hits', 'doubles', 'triples', 'homeRuns', 'rbi', 'baseOnBalls', 'strikeOuts', 'stolenBases', 'caughtStealing'],
                ['season', 'team', 'avg', 'obp', 'slg', 'ops']
            ]
            repl = {'season':'YEAR', 'team':'TM', 'atBats':'AB', 'hits':'H', 'doubles':'2B', 'triples':'3B', 'homeRuns':'HR', 'runs':'R', 'rbi':'RBI', 'baseOnBalls':'BB', 'strikeOuts':'SO', 'stolenBases':'SB', 'caughtStealing':'CS', 'avg':'AVG', 'obp':'OBP', 'slg':'SLG', 'ops':'OPS'}
        else:
            labels_list = [
                ['season', 'team', 'wins', 'losses', 'gamesPlayed', 'gamesStarted', 'saves',],
                ['season', 'team', 'inningsPitched', 'hits', 'runs', 'earnedRuns', 'baseOnBalls', 'strikeOuts', 'homeRuns', 'era', 'whip']
            ]
            repl = {'season':'YEAR', 'team':'TM', 'wins':'W', 'losses':'L', 'gamesPlayed':'G', 'gamesStarted':'GS', 'saves':'SV', 'inningsPitched':'IP', 'strikeOuts':'SO', 'baseOnBalls':'BB', 'homeRuns':'HR', 'era':'ERA', 'whip':'WHIP', 'hits':'H', 'runs':'R', 'earnedRuns':'ER'}

        if len(self.stats) == 1:
            for labels in labels_list:
                if 'season' in labels: labels.remove('season')
                if 'team' in labels: labels.remove('team')
        elif len(self.stats) > 1:
            for labels in labels_list:
                if 'season' in labels: labels.remove('season')

        blocks = []
        for labels in labels_list:
            lines = [''] * (len(self.stats) + 1)
            for label in labels:
                display_label = repl.get(label, label.upper())
                width = len(display_label)
                for row in self.stats:
                    width = max(width, len(str(row.get(label, ""))))
                
                lines[0] += display_label.rjust(width) + " "
                for i, row in enumerate(self.stats):
                    lines[i+1] += str(row.get(label, "")).rjust(width) + " "
            # Use .strip('\n') to prevent Python from deleting the leading spaces on your headers!
            blocks.append("\n".join([line.rstrip() for line in lines]).strip('\n'))

        return "\n\n".join(blocks)

class MLBClient:
    BASE_URL = "https://statsapi.mlb.com/api/v1"

    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None

    async def get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self):
        """Closes the aiohttp session properly."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def search_players(self, query: str) -> List[dict]:
        """Queries the Baseball Savant search API for autocomplete."""
        session = await self.get_session()
        url = f"https://baseballsavant.mlb.com/player/search-all?search={urllib.parse.quote(query)}"
        try:
            async with session.get(url) as resp:
                return await resp.json()
        except Exception:
            return []

    async def get_player_game_stats(self, player_id_or_name: str, date: str = None) -> List[PlayerGameStats]:
        session = await self.get_session()
        player_id = None
        player_name = player_id_or_name

        # If autocomplete was used, this will be the player's ID digits. 
        # If the user typed it manually and hit enter, we look them up first!
        if player_id_or_name.isdigit():
            player_id = player_id_or_name
        else:
            players = await self.search_players(player_id_or_name)
            if not players:
                return []
            player_id = str(players[0]['id'])
            player_name = players[0]['name']
        
        headshot_url = f"https://securea.mlb.com/mlb/images/players/head_shot/{player_id}@3x.jpg"

        # Fetch player info to find out what team they are currently on
        person_url = f"{self.BASE_URL}/people/{player_id}?hydrate=currentTeam,team"
        async with session.get(person_url) as resp:
            person_data = await resp.json()

        if not person_data.get('people'):
            return []

        person = person_data['people'][0]
        player_name = person.get('fullName', player_name)
        if 'currentTeam' not in person:
            return [PlayerGameStats(player_name, "FA", "N/A", False, date or "Today", info_message="Player is not currently on a team.", headshot_url=headshot_url)]

        team_id = person['currentTeam']['id']
        team_abbrev = person['currentTeam'].get('abbreviation', 'TEAM')

        # Fetch the team's schedule for the target date to get the gamePk(s)
        schedule_url = f"{self.BASE_URL}/schedule?sportId=1&teamId={team_id}"
        if date: schedule_url += f"&date={date}"

        async with session.get(schedule_url) as resp:
            sched_data = await resp.json()

        if not sched_data.get('dates') or not sched_data['dates'][0].get('games'):
            return [PlayerGameStats(player_name, team_abbrev, "N/A", False, date or "Today", info_message="No games scheduled for this date.", headshot_url=headshot_url)]

        results = []
        games = sched_data['dates'][0]['games']
        game_date = sched_data['dates'][0]['date']
        game_date_formatted = f"{int(game_date[5:7])}/{int(game_date[8:10])}"

        # Loop through all games that day (handles doubleheaders cleanly)
        for game in games:
            is_home = (game['teams']['home']['team']['id'] == team_id)
            side = 'home' if is_home else 'away'
            
            # Fetch the Boxscore for that game
            box_url = f"{self.BASE_URL}/game/{game['gamePk']}/boxscore"
            async with session.get(box_url) as resp:
                box_data = await resp.json()
                
            box_away = box_data['teams']['away']['team']
            box_home = box_data['teams']['home']['team']
            team_abbrev = box_home.get('abbreviation', team_abbrev) if is_home else box_away.get('abbreviation', team_abbrev)
            opp_abbrev = box_away.get('abbreviation', "OPP") if is_home else box_home.get('abbreviation', "OPP")
                
            players_dict = box_data['teams'][side]['players']
            player_key = f"ID{player_id}"
            
            if player_key not in players_dict:
                results.append(PlayerGameStats(player_name, team_abbrev, opp_abbrev, is_home, game_date_formatted, info_message="Player did not play in this game.", headshot_url=headshot_url))
                continue
                
            player_stats = players_dict[player_key]['stats']
            batting = player_stats.get('batting')
            pitching = player_stats.get('pitching')
            
            # Pitchers usually have empty hitting dicts even in the DH era, so we filter them out
            if batting and batting.get('atBats', 0) == 0 and batting.get('plateAppearances', 0) == 0:
                batting = None
            if pitching and pitching.get('inningsPitched', '0.0') == '0.0':
                pitching = None
                
            if not batting and not pitching:
                results.append(PlayerGameStats(player_name, team_abbrev, opp_abbrev, is_home, game_date_formatted, info_message="Player played but recorded no stats (e.g., pinch runner or defensive sub).", headshot_url=headshot_url))
                continue
                
            results.append(PlayerGameStats(
                player_name=player_name, team_abbrev=team_abbrev, opp_abbrev=opp_abbrev, is_home=is_home,
                date=game_date_formatted, batting_stats=batting, pitching_stats=pitching, pitching_dec=pitching.get('note', '') if pitching else "",
                headshot_url=headshot_url
            ))
            
        return results

    async def get_player_season_stats(self, player_id_or_name: str, stat_type: str = None, year: str = None, career: bool = False) -> List[PlayerSeasonStats]:
        session = await self.get_session()
        player_id = None
        player_name = player_id_or_name

        if player_id_or_name.isdigit():
            player_id = player_id_or_name
        else:
            players = await self.search_players(player_id_or_name)
            if not players:
                return []
            player_id = str(players[0]['id'])
            player_name = players[0]['name']

        headshot_url = f"https://securea.mlb.com/mlb/images/players/head_shot/{player_id}@3x.jpg"

        person_url = f"{self.BASE_URL}/people/{player_id}?hydrate=currentTeam,team,stats(type=[yearByYear,careerRegularSeason,career](team(league)),leagueListId=mlb_hist,group=[hitting,pitching])"
        async with session.get(person_url) as resp:
            person_data = await resp.json()

        if not person_data.get('people'):
            return []

        person = person_data['people'][0]
        player_name = person.get('fullName', player_name)
        pos = person.get('primaryPosition', {}).get('abbreviation', '')
        
        birthdate = person.get('birthDate', '1900-01-01')[:10]
        try:
            b_dt = datetime.strptime(birthdate, "%Y-%m-%d")
            now = datetime.now()
            age = now.year - b_dt.year - ((now.month, now.day) < (b_dt.month, b_dt.day))
            age_str = f"Age: {age}"
        except:
            age_str = ""

        info_line = f"{pos}  |  B/T: {person.get('batSide', {}).get('code', '')}/{person.get('pitchHand', {}).get('code', '')}  |  {person.get('height', '')}  |  {person.get('weight', '')} lbs  |  {age_str}"

        if not stat_type:
            if pos == "TWP":
                stat_types_to_fetch = ["hitting", "pitching"]
            else:
                stat_types_to_fetch = ["pitching"] if pos == "P" else ["hitting"]
        else:
            stat_types_to_fetch = [stat_type]

        api_stat_types = ["careerRegularSeason", "career"] if career else ["yearByYear"]
        target_year = str(year) if year else None
        
        all_stats = person.get('stats', [])
        results = []
        team_abbrev = person.get('currentTeam', {}).get('abbreviation', 'FA')

        for st in stat_types_to_fetch:
            found_stats = []
            current_target_year = target_year

            for stat_group in all_stats:
                if stat_group['group']['displayName'] == st and stat_group['type']['displayName'] in api_stat_types:
                    splits = stat_group.get('splits', [])
                    if not splits:
                        continue
                        
                    if career:
                        career_split = splits[-1]
                        for sp in splits:
                            if 'team' not in sp:
                                career_split = sp
                                break
                                
                        s = career_split.get('stat', {})
                        s['season'] = "Career"
                        s['team'] = "MLB"
                        found_stats.append(s)
                        current_target_year = "Career"
                        break
                    else:
                        if not current_target_year:
                            current_target_year = splits[-1].get('season', str(datetime.now().year))
                            
                        for split in splits:
                            season = split.get('season', '')
                            if season == current_target_year:
                                s = split.get('stat', {})
                                s['season'] = season
                                s['team'] = split.get('team', {}).get('abbreviation', 'MLB')
                                found_stats.append(s)

            if found_stats:
                results.append(PlayerSeasonStats(
                    player_name=player_name,
                    team_abbrev=team_abbrev,
                    stat_type=st,
                    years=current_target_year or str(year),
                    is_career=career,
                    info_line=info_line,
                    stats=found_stats,
                    headshot_url=headshot_url
                ))
            elif stat_type or len(stat_types_to_fetch) == 1:
                results.append(PlayerSeasonStats(
                    player_name=player_name,
                    team_abbrev=team_abbrev,
                    stat_type=st,
                    years=current_target_year or str(year),
                    is_career=career,
                    info_line=info_line,
                    stats=[],
                    info_message=f"No {st} stats found for this player.",
                    headshot_url=headshot_url
                ))

        return results

    async def get_todays_games(self, team_query: str = None, date: str = None) -> List[Game]:
        session = await self.get_session()
        # Request all the expanded data your old bot was using
        url = f"{self.BASE_URL}/schedule?sportId=1&hydrate=team,linescore(matchup,runners),previousPlay,person,stats,lineups"
        if date:
            url += f"&date={date}"
        print(url)  # Debug: Print the URL being requested
        
        async with session.get(url) as resp:
            resp.raise_for_status()
            data = await resp.json()
            
        if not data.get('dates'):
            return []
            
        games = []
        for game_data in data['dates'][0]['games']:
            game = Game.from_api_json(game_data)
            
            # Filter by team if a search query was provided
            if team_query:
                query = team_query.lower()
                
                # Common aliases mapping to catch nicknames your old bot used
                aliases = {"nats": "nationals", "yanks": "yankees", "cards": "cardinals", "dbacks": "diamondbacks", "barves": "braves"}
                if query in aliases:
                    query = aliases[query]
                    
                away_name = game.away.name.lower()
                home_name = game.home.name.lower()
                away_abbr = game.away.abbreviation.lower()
                home_abbr = game.home.abbreviation.lower()
                
                if (query != away_abbr and query != home_abbr and 
                    query not in away_name and query not in home_name):
                    continue
            
            games.append(game)
            
        # The schedule endpoint strips hitData from previousPlay. We must fetch the 
        # playByPlay endpoint concurrently for any live games to get the Statcast metrics.
        async def fetch_pbp(g: Game):
            if g.abstract_state == "Live" and g.status != "Delayed":
                pbp_url = f"{self.BASE_URL}/game/{g.game_pk}/playByPlay"
                try:
                    async with session.get(pbp_url) as pbp_resp:
                        if pbp_resp.status == 200:
                            pbp_data = await pbp_resp.json()
                            all_plays = pbp_data.get('allPlays', [])
                            if all_plays:
                                last_play = all_plays[-1]
                                # Fallback to previous play if current play has no description yet
                                if 'result' in last_play and 'description' not in last_play['result'] and len(all_plays) > 1:
                                    last_play = all_plays[-2]
                                
                                g.last_play_desc = last_play.get('result', {}).get('description', g.last_play_desc)
                                g.last_play_pitcher = last_play.get('matchup', {}).get('pitcher', {}).get('fullName', g.last_play_pitcher)
                                
                                for event in last_play.get('playEvents', []):
                                    if 'pitchData' in event:
                                        g.last_pitch_speed = event['pitchData'].get('startSpeed') or 0.0
                                        if 'details' in event and 'type' in event['details']:
                                            g.last_pitch_type = event['details']['type'].get('description', '')
                                    if 'hitData' in event:
                                        hd = event['hitData']
                                        g.statcast_dist = hd.get('totalDistance') or 0.0
                                        g.statcast_speed = hd.get('launchSpeed') or 0.0
                                        g.statcast_angle = hd.get('launchAngle') or 0.0
                except Exception as e:
                    print(f"Error fetching PBP for game {g.game_pk}: {e}")

        if games:
            await asyncio.gather(*(fetch_pbp(g) for g in games))

        return games