"""
ESPN API Client for NFL PickEm 2025
Provides real NFL data without cost or registration
"""

import requests
import json
from datetime import datetime, timezone
import pytz
import logging

logger = logging.getLogger(__name__)

class ESPNAPIClient:
    """ESPN API Client for real NFL data"""
    
    BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/football/nfl"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'NFL-PickEm-2025/1.0'
        })
    
    def get_current_week(self):
        """Get current NFL week"""
        try:
            url = f"{self.BASE_URL}/scoreboard"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Get current week from ESPN data
            if 'week' in data and 'number' in data['week']:
                current_week = data['week']['number']
                logger.info(f"✅ Current NFL week from ESPN: {current_week}")
                return current_week
            
            # Fallback: calculate based on season start
            season_start = datetime(2024, 9, 5, tzinfo=timezone.utc)  # NFL 2024 season start
            now = datetime.now(timezone.utc)
            weeks_since_start = (now - season_start).days // 7
            current_week = min(max(weeks_since_start + 1, 1), 18)
            
            logger.info(f"✅ Calculated current NFL week: {current_week}")
            return current_week
            
        except Exception as e:
            logger.error(f"❌ Error getting current week: {e}")
            return 3  # Default to week 3
    
    def get_teams(self):
        """Get all NFL teams"""
        try:
            url = f"{self.BASE_URL}/teams"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            teams = []
            
            for team_data in data.get('sports', [{}])[0].get('leagues', [{}])[0].get('teams', []):
                team = team_data.get('team', {})
                teams.append({
                    'id': team.get('id'),
                    'name': team.get('displayName', ''),
                    'abbreviation': team.get('abbreviation', ''),
                    'logo_url': team.get('logos', [{}])[0].get('href', '') if team.get('logos') else ''
                })
            
            logger.info(f"✅ Loaded {len(teams)} NFL teams from ESPN")
            return teams
            
        except Exception as e:
            logger.error(f"❌ Error getting teams: {e}")
            return self._get_fallback_teams()
    
    def get_schedule(self, week=None, season=2024):
        """Get NFL schedule for specific week or entire season"""
        try:
            if week:
                url = f"{self.BASE_URL}/scoreboard?week={week}&seasontype=2&year={season}"
            else:
                url = f"{self.BASE_URL}/scoreboard?seasontype=2&year={season}"
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            games = []
            
            for event in data.get('events', []):
                game = self._parse_game_data(event)
                if game:
                    games.append(game)
            
            logger.info(f"✅ Loaded {len(games)} games from ESPN for week {week or 'all'}")
            return games
            
        except Exception as e:
            logger.error(f"❌ Error getting schedule: {e}")
            return []
    
    def get_game_results(self, week, season=2024):
        """Get completed game results for a specific week"""
        try:
            url = f"{self.BASE_URL}/scoreboard?week={week}&seasontype=2&year={season}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            for event in data.get('events', []):
                if event.get('status', {}).get('type', {}).get('completed', False):
                    result = self._parse_game_result(event)
                    if result:
                        results.append(result)
            
            logger.info(f"✅ Loaded {len(results)} completed games from ESPN for week {week}")
            return results
            
        except Exception as e:
            logger.error(f"❌ Error getting game results: {e}")
            return []
    
    def _parse_game_data(self, event):
        """Parse ESPN game data into our format"""
        try:
            # Get teams
            competitions = event.get('competitions', [])
            if not competitions:
                return None
            
            competition = competitions[0]
            competitors = competition.get('competitors', [])
            
            if len(competitors) != 2:
                return None
            
            # Determine home/away teams
            home_team = None
            away_team = None
            
            for competitor in competitors:
                if competitor.get('homeAway') == 'home':
                    home_team = competitor.get('team', {})
                elif competitor.get('homeAway') == 'away':
                    away_team = competitor.get('team', {})
            
            if not home_team or not away_team:
                return None
            
            # Get game time
            date_str = event.get('date', '')
            game_time = None
            if date_str:
                try:
                    # Parse ESPN date format
                    utc_time = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    # Convert to Vienna time
                    vienna_tz = pytz.timezone('Europe/Vienna')
                    game_time = utc_time.astimezone(vienna_tz)
                except:
                    pass
            
            # Get week number
            week = event.get('week', {}).get('number', 1)
            
            # Get game status
            status = event.get('status', {})
            is_completed = status.get('type', {}).get('completed', False)
            
            # Get winner if completed
            winner_team_id = None
            home_score = 0
            away_score = 0
            
            if is_completed:
                for competitor in competitors:
                    score = int(competitor.get('score', 0))
                    if competitor.get('homeAway') == 'home':
                        home_score = score
                        if competitor.get('winner', False):
                            winner_team_id = home_team.get('id')
                    else:
                        away_score = score
                        if competitor.get('winner', False):
                            winner_team_id = away_team.get('id')
            
            return {
                'espn_id': event.get('id'),
                'week': week,
                'home_team_id': home_team.get('id'),
                'away_team_id': away_team.get('id'),
                'home_team_name': home_team.get('displayName', ''),
                'away_team_name': away_team.get('displayName', ''),
                'start_time': game_time,
                'is_completed': is_completed,
                'winner_team_id': winner_team_id,
                'home_score': home_score,
                'away_score': away_score
            }
            
        except Exception as e:
            logger.error(f"❌ Error parsing game data: {e}")
            return None
    
    def _parse_game_result(self, event):
        """Parse ESPN game result data"""
        game_data = self._parse_game_data(event)
        if game_data and game_data['is_completed']:
            return {
                'espn_id': game_data['espn_id'],
                'winner_team_id': game_data['winner_team_id'],
                'home_score': game_data['home_score'],
                'away_score': game_data['away_score']
            }
        return None
    
    def _get_fallback_teams(self):
        """Fallback NFL teams if ESPN API fails"""
        return [
            {'id': 'ARI', 'name': 'Arizona Cardinals', 'abbreviation': 'ARI', 'logo_url': ''},
            {'id': 'ATL', 'name': 'Atlanta Falcons', 'abbreviation': 'ATL', 'logo_url': ''},
            {'id': 'BAL', 'name': 'Baltimore Ravens', 'abbreviation': 'BAL', 'logo_url': ''},
            {'id': 'BUF', 'name': 'Buffalo Bills', 'abbreviation': 'BUF', 'logo_url': ''},
            {'id': 'CAR', 'name': 'Carolina Panthers', 'abbreviation': 'CAR', 'logo_url': ''},
            {'id': 'CHI', 'name': 'Chicago Bears', 'abbreviation': 'CHI', 'logo_url': ''},
            {'id': 'CIN', 'name': 'Cincinnati Bengals', 'abbreviation': 'CIN', 'logo_url': ''},
            {'id': 'CLE', 'name': 'Cleveland Browns', 'abbreviation': 'CLE', 'logo_url': ''},
            {'id': 'DAL', 'name': 'Dallas Cowboys', 'abbreviation': 'DAL', 'logo_url': ''},
            {'id': 'DEN', 'name': 'Denver Broncos', 'abbreviation': 'DEN', 'logo_url': ''},
            {'id': 'DET', 'name': 'Detroit Lions', 'abbreviation': 'DET', 'logo_url': ''},
            {'id': 'GB', 'name': 'Green Bay Packers', 'abbreviation': 'GB', 'logo_url': ''},
            {'id': 'HOU', 'name': 'Houston Texans', 'abbreviation': 'HOU', 'logo_url': ''},
            {'id': 'IND', 'name': 'Indianapolis Colts', 'abbreviation': 'IND', 'logo_url': ''},
            {'id': 'JAX', 'name': 'Jacksonville Jaguars', 'abbreviation': 'JAX', 'logo_url': ''},
            {'id': 'KC', 'name': 'Kansas City Chiefs', 'abbreviation': 'KC', 'logo_url': ''},
            {'id': 'LV', 'name': 'Las Vegas Raiders', 'abbreviation': 'LV', 'logo_url': ''},
            {'id': 'LAC', 'name': 'Los Angeles Chargers', 'abbreviation': 'LAC', 'logo_url': ''},
            {'id': 'LAR', 'name': 'Los Angeles Rams', 'abbreviation': 'LAR', 'logo_url': ''},
            {'id': 'MIA', 'name': 'Miami Dolphins', 'abbreviation': 'MIA', 'logo_url': ''},
            {'id': 'MIN', 'name': 'Minnesota Vikings', 'abbreviation': 'MIN', 'logo_url': ''},
            {'id': 'NE', 'name': 'New England Patriots', 'abbreviation': 'NE', 'logo_url': ''},
            {'id': 'NO', 'name': 'New Orleans Saints', 'abbreviation': 'NO', 'logo_url': ''},
            {'id': 'NYG', 'name': 'New York Giants', 'abbreviation': 'NYG', 'logo_url': ''},
            {'id': 'NYJ', 'name': 'New York Jets', 'abbreviation': 'NYJ', 'logo_url': ''},
            {'id': 'PHI', 'name': 'Philadelphia Eagles', 'abbreviation': 'PHI', 'logo_url': ''},
            {'id': 'PIT', 'name': 'Pittsburgh Steelers', 'abbreviation': 'PIT', 'logo_url': ''},
            {'id': 'SF', 'name': 'San Francisco 49ers', 'abbreviation': 'SF', 'logo_url': ''},
            {'id': 'SEA', 'name': 'Seattle Seahawks', 'abbreviation': 'SEA', 'logo_url': ''},
            {'id': 'TB', 'name': 'Tampa Bay Buccaneers', 'abbreviation': 'TB', 'logo_url': ''},
            {'id': 'TEN', 'name': 'Tennessee Titans', 'abbreviation': 'TEN', 'logo_url': ''},
            {'id': 'WAS', 'name': 'Washington Commanders', 'abbreviation': 'WAS', 'logo_url': ''}
        ]

# Test function
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    client = ESPNAPIClient()
    
    print("Testing ESPN API Client...")
    
    # Test current week
    current_week = client.get_current_week()
    print(f"Current week: {current_week}")
    
    # Test teams
    teams = client.get_teams()
    print(f"Teams loaded: {len(teams)}")
    
    # Test schedule for current week
    games = client.get_schedule(week=current_week)
    print(f"Games for week {current_week}: {len(games)}")
    
    # Test completed games for week 1
    results = client.get_game_results(week=1)
    print(f"Completed games for week 1: {len(results)}")

