import aiohttp
import asyncio
import urllib.parse
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime, timedelta

def _bold_play_description(desc: str, play: dict) -> str:
    if not desc or not play:
        return desc
        
    names = set()
    matchup = play.get('matchup', {})
    if matchup.get('batter'): names.add(matchup['batter'].get('fullName'))
    if matchup.get('pitcher'): names.add(matchup['pitcher'].get('fullName'))
    
    for runner in play.get('runners', []):
        if runner.get('details', {}).get('runner'):
            names.add(runner['details']['runner'].get('fullName'))
            
    names = {n for n in names if n}
    for name in sorted(names, key=len, reverse=True):
        # Idempotent replacement to prevent double-bolding if we run this twice
        desc = desc.replace(f"**{name}**", name)
        desc = desc.replace(name, f"**{name}**")
        
    return desc

@dataclass
class Team:
    id: int
    name: str
    abbreviation: str
    score: int
    hits: int = 0
    errors: int = 0
    record: str = ""

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
    away_probable: str = ""
    home_probable: str = ""
    away_probable_stats: str = ""
    home_probable_stats: str = ""
    win_pitcher: str = ""
    loss_pitcher: str = ""
    save_pitcher: str = ""
    win_pitcher_note: str = ""
    loss_pitcher_note: str = ""
    save_pitcher_note: str = ""
    game_time_str: str = ""
    game_date_str: str = ""
    scoring_plays: List["ScoringPlay"] = None

    @classmethod
    def from_api_json(cls, data: dict):
        """Parses the raw MLB Stats API JSON into a clean Python object."""
        away_data = data['teams']['away']
        home_data = data['teams']['home']
        ls = data.get('linescore', {})
        
        away_record = f"({away_data.get('leagueRecord', {}).get('wins', 0)}-{away_data.get('leagueRecord', {}).get('losses', 0)})"
        home_record = f"({home_data.get('leagueRecord', {}).get('wins', 0)}-{home_data.get('leagueRecord', {}).get('losses', 0)})"
        
        away_team = Team(
            id=away_data['team']['id'],
            name=away_data['team']['name'],
            abbreviation=away_data['team'].get('abbreviation', away_data['team']['name'][:3].upper()),
            score=away_data.get('score', 0),
            hits=ls.get('teams', {}).get('away', {}).get('hits', 0),
            errors=ls.get('teams', {}).get('away', {}).get('errors', 0),
            record=away_record
        )
        
        home_team = Team(
            id=home_data['team']['id'],
            name=home_data['team']['name'],
            abbreviation=home_data['team'].get('abbreviation', home_data['team']['name'][:3].upper()),
            score=home_data.get('score', 0),
            hits=ls.get('teams', {}).get('home', {}).get('hits', 0),
            errors=ls.get('teams', {}).get('home', {}).get('errors', 0),
            record=home_record
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
            desc = last_play['result'].get('description', '')
            game.last_play_desc = _bold_play_description(desc, last_play)
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
        
        game.away_probable = away_data.get('probablePitcher', {}).get('lastName', '')
        game.home_probable = home_data.get('probablePitcher', {}).get('lastName', '')
        
        if 'stats' in away_data.get('probablePitcher', {}):
            for st in away_data['probablePitcher']['stats']:
                if st.get('type', {}).get('displayName') == 'statsSingleSeason' and st.get('group', {}).get('displayName') == 'pitching':
                    s = st.get('stats', {})
                    game.away_probable_stats = f"({s.get('wins', 0)}-{s.get('losses', 0)}) {s.get('era', '-.--')}"
                    break
                    
        if 'stats' in home_data.get('probablePitcher', {}):
            for st in home_data['probablePitcher']['stats']:
                if st.get('type', {}).get('displayName') == 'statsSingleSeason' and st.get('group', {}).get('displayName') == 'pitching':
                    s = st.get('stats', {})
                    game.home_probable_stats = f"({s.get('wins', 0)}-{s.get('losses', 0)}) {s.get('era', '-.--')}"
                    break
        
        decisions = data.get('decisions', {})
        
        winner = decisions.get('winner', {})
        game.win_pitcher = winner.get('lastName', '')
        for st in winner.get('stats', []):
            if st.get('type', {}).get('displayName') == 'gameLog' and 'note' in st.get('stats', {}):
                game.win_pitcher_note = st['stats']['note']
            elif st.get('type', {}).get('displayName') == 'statsSingleSeason' and not game.win_pitcher_note:
                game.win_pitcher_note = f"(W, {st.get('stats', {}).get('wins', 0)}-{st.get('stats', {}).get('losses', 0)})"
                
        loser = decisions.get('loser', {})
        game.loss_pitcher = loser.get('lastName', '')
        for st in loser.get('stats', []):
            if st.get('type', {}).get('displayName') == 'gameLog' and 'note' in st.get('stats', {}):
                game.loss_pitcher_note = st['stats']['note']
            elif st.get('type', {}).get('displayName') == 'statsSingleSeason' and not game.loss_pitcher_note:
                game.loss_pitcher_note = f"(L, {st.get('stats', {}).get('wins', 0)}-{st.get('stats', {}).get('losses', 0)})"
                
        save = decisions.get('save', {})
        game.save_pitcher = save.get('lastName', '')
        for st in save.get('stats', []):
            if st.get('type', {}).get('displayName') == 'gameLog' and 'note' in st.get('stats', {}):
                game.save_pitcher_note = st['stats']['note']
            elif st.get('type', {}).get('displayName') == 'statsSingleSeason' and not game.save_pitcher_note:
                game.save_pitcher_note = f"(SV, {st.get('stats', {}).get('saves', 0)})"
        
        if 'gameDate' in data:
            try:
                dt = datetime.strptime(data['gameDate'], "%Y-%m-%dT%H:%M:%SZ")
                dt = dt - timedelta(hours=4)  # ET offset for baseball season
                game.game_time_str = dt.strftime("%I:%M %p").lstrip('0') + " ET"
                game.game_date_str = dt.strftime("%A, %b %d").replace(" 0", " ")
            except ValueError:
                pass

        return game

    def format_score_line(self) -> str:
        """A simple formatter to output the game score for Discord."""
        away_base = f"{self.away.abbreviation.ljust(3)} {str(self.away.score).rjust(2)} {str(self.away.hits).rjust(2)} {self.away.errors}"
        home_base = f"{self.home.abbreviation.ljust(3)} {str(self.home.score).rjust(2)} {str(self.home.hits).rjust(2)} {self.home.errors}"

        if self.abstract_state == "Live" and self.status not in ["Delayed", "Warmup"]:
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
                output += f"\n\nLast Play: With **{self.last_play_pitcher}** pitching, {self.last_play_desc}\n"
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
            
            away_p, home_p, sv_p = "", "", ""
            if self.win_pitcher:
                w_str = f"{self.win_pitcher} {self.win_pitcher_note}".strip()
                l_str = f"{self.loss_pitcher} {self.loss_pitcher_note}".strip()
                if self.save_pitcher:
                    sv_p = f"{self.save_pitcher} {self.save_pitcher_note}".strip()
                
                if self.away.score > self.home.score:
                    away_p = w_str
                    home_p = l_str
                elif self.home.score > self.away.score:
                    away_p = l_str
                    home_p = w_str
                    
            away_p_str = f" | {away_p}" if away_p else ""
            home_p_str = f" | {home_p}" if home_p else ""
            
            result = f"{away_base}  {self.away.record.center(7)} | {final_str.ljust(4)}{away_p_str}\n{home_base}  {self.home.record.center(7)} | {' ' * 4}{home_p_str}"
            if sv_p:
                spacer = " " * len(f"{home_base}  {self.home.record.center(7)}")
                result += f"\n{spacer} | {' ' * 4} | {sv_p}"
                
            return result
        else:
            time_str = self.game_time_str if self.status in ["Scheduled", "Pre-Game", "Warmup"] and self.game_time_str else self.status
            
            away_prob = f"{self.away_probable.ljust(10)} {self.away_probable_stats}".strip() if self.away_probable else ""
            home_prob = f"{self.home_probable.ljust(10)} {self.home_probable_stats}".strip() if self.home_probable else ""
            
            away_prob_str = f" | {away_prob}" if away_prob else ""
            home_prob_str = f" | {home_prob}" if home_prob else ""
            
            return f"{self.away.abbreviation.ljust(3)} {self.away.record.center(7)} | {time_str.ljust(11)}{away_prob_str}\n{self.home.abbreviation.ljust(3)} {self.home.record.center(7)} | {' ' * 11}{home_prob_str}"

    def format_modern_score_line(self) -> str:
        """A modern Discord markdown formatter for the game score."""
        away_line = f"**{self.away.abbreviation} {self.away.score}** ({self.away.hits}H, {self.away.errors}E)"
        home_line = f"**{self.home.abbreviation} {self.home.score}** ({self.home.hits}H, {self.home.errors}E)"
        
        if self.abstract_state == "Live" and self.status not in ["Delayed", "Warmup"]:
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
class AtBat:
    inning: str
    pitcher_name: str
    description: str
    pitch_data: str
    statcast_data: str
    video_url: str
    video_blurb: str
    is_scoring: bool
    is_complete: bool

@dataclass
class ScoringPlay:
    inning: str
    description: str
    video_url: str
    video_blurb: str

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
    at_bats: List[AtBat] = None

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
    parent_org_abbrev: str = ""

    def format_discord_code_block(self) -> str:
        if self.info_message:
            return self.info_message

        if self.stat_type == "hitting":
            labels_list = [
                ['season', 'team', 'gamesPlayed', 'plateAppearances', 'atBats', 'runs', 'hits', 'doubles', 'triples', 'homeRuns', 'rbi', 'baseOnBalls', 'strikeOuts'],
                ['season', 'team', 'stolenBases', 'caughtStealing', 'intentionalWalks', 'hitByPitch', 'avg', 'obp', 'slg', 'ops']
            ]
            repl = {'season':'YEAR', 'team':'TM', 'gamesPlayed':'G', 'plateAppearances':'PA', 'atBats':'AB', 'hits':'H', 'doubles':'2B', 'triples':'3B', 'homeRuns':'HR', 'runs':'R', 'rbi':'RBI', 'baseOnBalls':'BB', 'strikeOuts':'SO', 'stolenBases':'SB', 'caughtStealing':'CS', 'totalBases':'TB', 'intentionalWalks':'IBB', 'hitByPitch':'HBP', 'avg':'AVG', 'obp':'OBP', 'slg':'SLG', 'ops':'OPS'}
        else:
            labels_list = [
                ['season', 'team', 'wins', 'losses', 'gamesPlayed', 'gamesStarted', 'completeGames', 'shutouts', 'saveOpportunities', 'saves', 'holds'],
                ['season', 'team', 'inningsPitched', 'hits', 'runs', 'earnedRuns', 'homeRuns', 'baseOnBalls', 'strikeOuts', 'era', 'whip'],
                ['season', 'team', 'strikeoutsPer9Inn', 'walksPer9Inn', 'strikeoutWalkRatio', 'avg']
            ]
            repl = {'season':'YEAR', 'team':'TM', 'wins':'W', 'losses':'L', 'gamesPlayed':'G', 'gamesStarted':'GS', 'completeGames':'CG', 'shutouts':'SHO', 'saves':'SV', 'saveOpportunities':'SVO', 'holds':'HLD',
                    'gamesFinished':'GF', 'inningsPitched':'IP', 'strikeOuts':'SO', 'baseOnBalls':'BB', 'homeRuns':'HR', 'era':'ERA', 'whip':'WHIP', 'hits':'H', 'runs':'R', 'earnedRuns':'ER', 
                    'strikeoutsPer9Inn':'K/9', 'walksPer9Inn':'BB/9', 'strikeoutWalkRatio':'K/BB', 'avg':'AVG'}

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

    async def search_players(self, query: str, milb: bool = False) -> List[dict]:
        """Queries the MLB APIs for autocomplete."""
        session = await self.get_session()
        if milb:
            url = f"{self.BASE_URL}/people/search?names={urllib.parse.quote(query)}&sportIds=11,12,13,14,15,5442,16&active=true&hydrate=currentTeam,team"
            try:
                async with session.get(url) as resp:
                    data = await resp.json()
                    results = []
                    for p in data.get('people', []):
                        team_name = p.get('currentTeam', {}).get('name', 'FA')
                        results.append({'id': p['id'], 'name': p['fullName'], 'name_display_club': team_name, 'mlb': 1})
                    return results
            except Exception:
                return []
        else:
            url = f"https://baseballsavant.mlb.com/player/search-all?search={urllib.parse.quote(query)}"
            try:
                async with session.get(url) as resp:
                    return await resp.json()
            except Exception:
                return []

    async def get_team_id(self, team_query: str) -> Optional[int]:
        if not team_query: return None
        query = team_query.lower()
        aliases = {"nats": "nationals", "yanks": "yankees", "cards": "cardinals", "dbacks": "diamondbacks", "barves": "braves"}
        query = aliases.get(query, query)
        
        session = await self.get_session()
        async with session.get(f"{self.BASE_URL}/teams?sportId=1") as resp:
            data = await resp.json()
            for team in data.get('teams', []):
                if (query == team.get('abbreviation', '').lower() or 
                    query in team.get('name', '').lower() or 
                    query in team.get('teamName', '').lower()):
                    return team['id']
        return None

    async def get_team_schedule(self, team_query: str, num_games: int = 3, past: bool = False) -> List[Game]:
        team_id = await self.get_team_id(team_query)
        if not team_id:
            return []

        now = datetime.utcnow() - timedelta(hours=5)
        # Use a wide 45-day window to guarantee we find enough games even with rainouts or the All-Star break
        if past:
            start_date = (now - timedelta(days=45)).strftime("%Y-%m-%d")
            end_date = now.strftime("%Y-%m-%d")
        else:
            start_date = now.strftime("%Y-%m-%d")
            end_date = (now + timedelta(days=45)).strftime("%Y-%m-%d")

        session = await self.get_session()
        url = f"{self.BASE_URL}/schedule?sportId=1&teamId={team_id}&startDate={start_date}&endDate={end_date}&hydrate=team,linescore(matchup,runners),previousPlay,person,stats,lineups,probablePitcher,decisions"
        
        async with session.get(url) as resp:
            data = await resp.json()

        if not data.get('dates'): return []

        games = []
        for date_obj in data['dates']:
            for game_data in date_obj['games']:
                game = Game.from_api_json(game_data)
                if past:
                    # Only include games that have completely finished
                    if game.abstract_state == 'Final' or game.status in ['Suspended', 'Completed Early']:
                        games.append(game)
                else:
                    # Include anything that isn't finished or cancelled (Scheduled, Warmup, Live, Delayed)
                    if game.abstract_state != 'Final' and game.status not in ['Postponed', 'Cancelled']:
                        games.append(game)

        # Take the most recent 'N' games from the end of the list (past), or the first 'N' games (next)
        games = games[-num_games:] if past else games[:num_games]
            
        # Fetch PBP if any of these scheduled games happen to be Live right now
        async def fetch_pbp(g: Game):
            if g.abstract_state == "Live" and g.status not in ["Delayed", "Warmup"]:
                try:
                    async with session.get(f"{self.BASE_URL}/game/{g.game_pk}/playByPlay") as pbp_resp:
                        if pbp_resp.status == 200:
                            # Our existing static parse handles everything else, so just poke the endpoint to wake the API up
                            pass
                except Exception: pass
                
        if games: await asyncio.gather(*(fetch_pbp(g) for g in games))
        return games

    async def get_games_with_scoring_plays(self, team_query: str, date: str = None) -> List[Game]:
        # 1. Find the game(s) for the team
        games = await self.get_todays_games(team_query=team_query, date=date)
        if not games:
            return []
        
        team_id = await self.get_team_id(team_query)
        if not team_id:
            return games

        session = await self.get_session()

        async def process_game(game: Game):
            # 2. Fetch PBP and Content
            pbp_url = f"{self.BASE_URL}/game/{game.game_pk}/playByPlay"
            content_url = f"{self.BASE_URL}/game/{game.game_pk}/content"
            
            try:
                async with session.get(pbp_url) as resp:
                    pbp_data = await resp.json() if resp.status == 200 else {}
                async with session.get(content_url) as resp:
                    content_data = await resp.json() if resp.status == 200 else {}
            except Exception as e:
                print(f"Error fetching scoring play data for game {game.game_pk}: {e}")
                return

            # 3. Process scoring plays
            game.scoring_plays = []
            
            team_side = 'away' if game.away.id == team_id else 'home'
            team_half = 'top' if team_side == 'away' else 'bottom'

            content_dict = {}
            highlights = content_data.get('highlights', {}).get('highlights', {}).get('items', [])
            for item in highlights:
                if 'guid' in item:
                    for pb in item.get('playbacks', []):
                        if pb.get('name') == 'mp4Avc':
                            content_dict[item['guid']] = {'url': pb['url'], 'blurb': item.get('headline', item.get('blurb', ''))}
                            break

            scoring_play_indices = pbp_data.get('scoringPlays', [])
            if not scoring_play_indices: return
            all_plays = pbp_data.get('allPlays', [])

            for play_index in scoring_play_indices:
                play = all_plays[play_index]
                if play.get('about', {}).get('halfInning') != team_half: continue

                half = play.get('about', {}).get('halfInning', '')
                inning = f"{'bot' if half == 'bottom' else half} {play.get('about', {}).get('inning', '')}"
                desc = play.get('result', {}).get('description', 'Scoring play.')
                desc = _bold_play_description(desc, play)
                if 'awayScore' in play.get('result', {}): desc += f" ({play['result']['awayScore']}-{play['result']['homeScore']})"
                vid_url, vid_blurb = "", ""
                if play.get('playEvents') and (play_id := play['playEvents'][-1].get('playId')) and play_id in content_dict:
                    vid_url, vid_blurb = content_dict[play_id]['url'], content_dict[play_id]['blurb']
                game.scoring_plays.append(ScoringPlay(inning, desc, vid_url, vid_blurb))

        await asyncio.gather(*(process_game(g) for g in games))
        return games

    async def get_player_game_stats(self, player_id_or_name: str, date: str = None, milb: bool = False, include_abs: bool = False) -> List[PlayerGameStats]:
        session = await self.get_session()
        player_id = None
        player_name = player_id_or_name

        # If autocomplete was used, this will be the player's ID digits. 
        # If the user typed it manually and hit enter, we look them up first!
        if player_id_or_name.isdigit():
            player_id = player_id_or_name
        else:
            players = await self.search_players(player_id_or_name, milb=milb)
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
        sport_ids = "11,12,13,14,15,5442,16" if milb else "1"
        schedule_url = f"{self.BASE_URL}/schedule?sportId={sport_ids}&teamId={team_id}"
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
                
            at_bats = []
            if include_abs:
                pbp_url = f"{self.BASE_URL}/game/{game['gamePk']}/playByPlay"
                content_url = f"{self.BASE_URL}/game/{game['gamePk']}/content"
                
                try:
                    async with session.get(pbp_url) as resp:
                        pbp_data = await resp.json() if resp.status == 200 else {}
                    async with session.get(content_url) as resp:
                        content_data = await resp.json() if resp.status == 200 else {}
                except Exception as e:
                    print(f"Error fetching AB data: {e}")
                    pbp_data, content_data = {}, {}
                    
                content_dict = {}
                highlights = content_data.get('highlights', {}).get('highlights', {}).get('items', [])
                for item in highlights:
                    if 'guid' in item:
                        for pb in item.get('playbacks', []):
                            if pb.get('name') == 'mp4Avc':
                                content_dict[item['guid']] = {'url': pb['url'], 'blurb': item.get('headline', item.get('blurb', ''))}
                                break
                                
                for play in pbp_data.get('allPlays', []):
                    if play.get('matchup', {}).get('batter', {}).get('id') == int(player_id):
                        half = play.get('about', {}).get('halfInning', '')
                        if half == 'bottom': half = 'bot'
                        inning = f"{half} {play.get('about', {}).get('inning', '')}"
                        is_complete = play.get('about', {}).get('isComplete', False)
                        desc = play.get('result', {}).get('description', 'Currently at bat.')
                        desc = _bold_play_description(desc, play)
                        pitcher = play.get('matchup', {}).get('pitcher', {}).get('fullName', '')
                        is_scoring = play.get('about', {}).get('isScoringPlay', False)

                        pitch_str, statcast_str, vid_url, vid_blurb = "", "", "", ""

                        if play.get('playEvents'):
                            last_event = play['playEvents'][-1]
                            if 'pitchData' in last_event:
                                pspeed = last_event['pitchData'].get('startSpeed')
                                ptype = last_event.get('details', {}).get('type', {}).get('description')
                                if pspeed and ptype:
                                    pitch_str = f"{pspeed:.1f} mph {ptype}"

                            if 'hitData' in last_event:
                                hd = last_event['hitData']
                                dist, ev, la = hd.get('totalDistance'), hd.get('launchSpeed'), hd.get('launchAngle')
                                parts = []
                                if dist: parts.append(f"{dist} ft")
                                if ev: parts.append(f"{ev} mph")
                                if la is not None: parts.append(f"{la} degrees")
                                statcast_str = ", ".join(parts)

                            play_id = last_event.get('playId')
                            if play_id and play_id in content_dict:
                                vid_url = content_dict[play_id]['url']
                                vid_blurb = content_dict[play_id]['blurb']

                        at_bats.append(AtBat(inning, pitcher, desc, pitch_str, statcast_str, vid_url, vid_blurb, is_scoring, is_complete))

            results.append(PlayerGameStats(
                player_name=player_name, team_abbrev=team_abbrev, opp_abbrev=opp_abbrev, is_home=is_home,
                date=game_date_formatted, batting_stats=batting, pitching_stats=pitching, pitching_dec=pitching.get('note', '') if pitching else "",
                headshot_url=headshot_url, at_bats=at_bats
            ))
            
        return results

    async def get_player_season_stats(self, player_id_or_name: str, stat_type: str = None, year: str = None, career: bool = False, milb: bool = False) -> List[PlayerSeasonStats]:
        session = await self.get_session()
        player_id = None
        player_name = player_id_or_name

        if player_id_or_name.isdigit():
            player_id = player_id_or_name
        else:
            players = await self.search_players(player_id_or_name, milb=milb)
            if not players:
                return []
            player_id = str(players[0]['id'])
            player_name = players[0]['name']

        headshot_url = f"https://securea.mlb.com/mlb/images/players/head_shot/{player_id}@3x.jpg"

        league_list_id = "mlb_milb" if milb else "mlb_hist"
        person_url = f"{self.BASE_URL}/people/{player_id}?hydrate=currentTeam,team,draft,stats(type=[yearByYear,careerRegularSeason,career](team(league,sport)),leagueListId={league_list_id},group=[hitting,pitching])"
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
        
        if person.get('nickName'):
            info_line += f"  |  \"{person['nickName']}\""
            
        if milb and 'drafts' in person and person['drafts']:
            draft = person['drafts'][-1]
            d_year = draft.get('year', 'N/A')
            d_round = draft.get('pickRound', 'N/A')
            d_pick = draft.get('roundPickNumber', 'N/A')
            d_school_obj = draft.get('school') or {}
            d_school = d_school_obj.get('name', 'N/A')
            info_line += f"\n  Draft: {d_year} | Round: {d_round} | Pick: {d_pick} | School: {d_school}"
            
        parent_org_abbrev = ""
        if milb:
            parent_org_id = person.get('currentTeam', {}).get('parentOrgId')
            if parent_org_id:
                async with session.get(f"{self.BASE_URL}/teams/{parent_org_id}") as resp:
                    if resp.status == 200:
                        team_data = await resp.json()
                        if team_data.get('teams'):
                            parent_org_abbrev = team_data['teams'][0].get('abbreviation', '')

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

        career_years_str = ""
        if career:
            career_years = []
            career_teams = []
            for stat_group in all_stats:
                if stat_group['type']['displayName'] == 'yearByYear':
                    for split in stat_group.get('splits', []):
                        season = split.get('season')
                        if season and season not in career_years:
                            career_years.append(season)
                        if milb:
                            t_abbrev = split.get('sport', {}).get('abbreviation')
                        else:
                            t_abbrev = split.get('team', {}).get('abbreviation')
                        if t_abbrev and t_abbrev not in ['MLB', 'MiLB']:
                            if t_abbrev not in career_teams:
                                career_teams.append(t_abbrev)
            
            if career_years:
                career_years_str = f"{min(career_years)}-{max(career_years)}" if len(career_years) > 1 else min(career_years)
            if career_teams:
                info_line += f"\n\n{'-'.join(career_teams)}"

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
                        current_target_year = career_years_str or "Career"
                        break
                    else:
                        if not current_target_year:
                            current_target_year = splits[-1].get('season', str(datetime.now().year))
                            
                        for split in splits:
                            season = split.get('season', '')
                            if season == current_target_year:
                                s = split.get('stat', {})
                                s['season'] = season
                                if milb:
                                    s['team'] = split.get('sport', {}).get('abbreviation', 'MiLB')
                                else:
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
                    headshot_url=headshot_url,
                    parent_org_abbrev=parent_org_abbrev
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
                    headshot_url=headshot_url,
                    parent_org_abbrev=parent_org_abbrev
                ))

        return results

    async def get_todays_games(self, team_query: str = None, date: str = None) -> List[Game]:
        session = await self.get_session()
        # Request all the expanded data your old bot was using
        url = f"{self.BASE_URL}/schedule?sportId=1&hydrate=team,linescore(matchup,runners),previousPlay,person,stats,lineups,probablePitcher,decisions"
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
                                
                                desc = last_play.get('result', {}).get('description', g.last_play_desc)
                                g.last_play_desc = _bold_play_description(desc, last_play)
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