import aiohttp
import asyncio
from dataclasses import dataclass
from typing import List, Optional

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
            return f"{away_base} | F\n{home_base} |"
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
            return f"{away_line} @ {home_line} | **Final**"
        else:
            return f"{away_line} @ {home_line} | **{self.status}**"

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

    async def get_todays_games(self, team_abbrev: str = None) -> List[Game]:
        session = await self.get_session()
        # Request all the expanded data your old bot was using
        url = f"{self.BASE_URL}/schedule?sportId=1&hydrate=team,linescore(matchup,runners),previousPlay,person,stats,lineups"
        print(url)  # Debug: Print the URL being requested
        
        async with session.get(url) as resp:
            resp.raise_for_status()
            data = await resp.json()
            
        if not data.get('dates'):
            return []
            
        games = []
        for game_data in data['dates'][0]['games']:
            game = Game.from_api_json(game_data)
            
            # Filter by team if a search parameter was provided
            if team_abbrev:
                team_lower = team_abbrev.lower()
                if (game.away.abbreviation.lower() != team_lower and 
                    game.home.abbreviation.lower() != team_lower):
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