"""
Echte NFL-Daten Sync für NFL PickEm 2025
Lädt echte NFL Schedule und Ergebnisse von SportsData.io
KEINE MOCK-DATEN!
"""

import requests
import logging
from datetime import datetime, timedelta
import pytz
import os

logger = logging.getLogger(__name__)

class RealNFLDataSync:
    """Synchronisiert echte NFL-Daten von SportsData.io"""
    
    def __init__(self):
        self.api_key = os.getenv('SPORTSDATA_API_KEY')
        self.base_url = "https://api.sportsdata.io/v3/nfl"
        self.vienna_tz = pytz.timezone('Europe/Vienna')
        
        if not self.api_key:
            logger.warning("⚠️ No SportsData.io API key found. Cannot load real NFL data!")
            self.api_key = None
    
    def get_real_nfl_schedule(self, season=2025):
        """Lädt echten NFL Schedule für 2025 Season"""
        if not self.api_key:
            logger.error("❌ Cannot load real NFL schedule without API key")
            return []
        
        try:
            # SportsData.io NFL Schedule Endpoint
            url = f"{self.base_url}/scores/json/Schedules/{season}"
            headers = {"Ocp-Apim-Subscription-Key": self.api_key}
            
            logger.info(f"🔄 Loading real NFL schedule for {season}...")
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            games = response.json()
            logger.info(f"✅ Loaded {len(games)} real NFL games for {season}")
            
            return self.convert_to_our_format(games)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to load real NFL schedule: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Error processing NFL schedule: {e}")
            return []
    
    def get_real_nfl_scores(self, season=2025, week=None):
        """Lädt echte NFL Ergebnisse für spezifische Woche"""
        if not self.api_key:
            logger.error("❌ Cannot load real NFL scores without API key")
            return []
        
        try:
            if week:
                # Spezifische Woche
                url = f"{self.base_url}/scores/json/ScoresByWeek/{season}/{week}"
            else:
                # Aktuelle Woche
                url = f"{self.base_url}/scores/json/Scores/{season}"
            
            headers = {"Ocp-Apim-Subscription-Key": self.api_key}
            
            logger.info(f"🔄 Loading real NFL scores for {season} week {week}...")
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            scores = response.json()
            logger.info(f"✅ Loaded {len(scores)} real NFL scores")
            
            return self.convert_scores_to_our_format(scores)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to load real NFL scores: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Error processing NFL scores: {e}")
            return []
    
    def convert_to_our_format(self, sportsdata_games):
        """Konvertiert SportsData.io Format zu unserem Datenbank-Format"""
        converted_games = []
        
        for game in sportsdata_games:
            try:
                # SportsData.io Felder zu unseren Feldern mappen
                game_time = self.parse_game_time(game.get('DateTime'))
                
                converted_game = {
                    'week': game.get('Week'),
                    'season': game.get('Season'),
                    'away_team': self.map_team_abbreviation(game.get('AwayTeam')),
                    'home_team': self.map_team_abbreviation(game.get('HomeTeam')),
                    'start_time': game_time,
                    'is_completed': game.get('IsOver', False),
                    'winner_team': self.determine_winner(game),
                    'away_score': game.get('AwayScore'),
                    'home_score': game.get('HomeScore'),
                    'sportsdata_id': game.get('GameKey')  # Für Referenz
                }
                
                converted_games.append(converted_game)
                
            except Exception as e:
                logger.warning(f"⚠️ Failed to convert game: {e}")
                continue
        
        return converted_games
    
    def convert_scores_to_our_format(self, sportsdata_scores):
        """Konvertiert SportsData.io Scores zu unserem Format"""
        return self.convert_to_our_format(sportsdata_scores)
    
    def parse_game_time(self, datetime_str):
        """Parst SportsData.io DateTime zu Wiener Zeit"""
        if not datetime_str:
            return None
        
        try:
            # SportsData.io verwendet UTC
            utc_time = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            vienna_time = utc_time.astimezone(self.vienna_tz)
            return vienna_time
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to parse game time {datetime_str}: {e}")
            return None
    
    def map_team_abbreviation(self, sportsdata_team):
        """Mappt SportsData.io Team-Namen zu unseren Abkürzungen"""
        team_mapping = {
            'ARI': 'ARI', 'ATL': 'ATL', 'BAL': 'BAL', 'BUF': 'BUF',
            'CAR': 'CAR', 'CHI': 'CHI', 'CIN': 'CIN', 'CLE': 'CLE',
            'DAL': 'DAL', 'DEN': 'DEN', 'DET': 'DET', 'GB': 'GB',
            'HOU': 'HOU', 'IND': 'IND', 'JAX': 'JAX', 'KC': 'KC',
            'LV': 'LV', 'LAC': 'LAC', 'LAR': 'LAR', 'MIA': 'MIA',
            'MIN': 'MIN', 'NE': 'NE', 'NO': 'NO', 'NYG': 'NYG',
            'NYJ': 'NYJ', 'PHI': 'PHI', 'PIT': 'PIT', 'SF': 'SF',
            'SEA': 'SEA', 'TB': 'TB', 'TEN': 'TEN', 'WAS': 'WAS'
        }
        
        return team_mapping.get(sportsdata_team, sportsdata_team)
    
    def determine_winner(self, game):
        """Bestimmt Gewinner basierend auf echten Scores"""
        if not game.get('IsOver', False):
            return None
        
        away_score = game.get('AwayScore', 0)
        home_score = game.get('HomeScore', 0)
        
        if away_score > home_score:
            return self.map_team_abbreviation(game.get('AwayTeam'))
        elif home_score > away_score:
            return self.map_team_abbreviation(game.get('HomeTeam'))
        else:
            # Unentschieden (sehr selten in NFL)
            return None
    
    def get_current_nfl_week(self):
        """Ermittelt aktuelle NFL Woche basierend auf echten Daten"""
        if not self.api_key:
            # Fallback ohne API
            return 3
        
        try:
            url = f"{self.base_url}/scores/json/CurrentWeek"
            headers = {"Ocp-Apim-Subscription-Key": self.api_key}
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            current_week = response.json()
            week_number = current_week.get('Week', 3)
            
            logger.info(f"✅ Current NFL week: {week_number}")
            return week_number
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to get current NFL week: {e}")
            return 3  # Fallback
    
    def sync_real_nfl_data(self, app, db, Team, Match):
        """Synchronisiert echte NFL-Daten in die Datenbank"""
        logger.info("🔄 Starting real NFL data sync...")
        
        with app.app_context():
            try:
                # 1. Lade echten NFL Schedule
                real_games = self.get_real_nfl_schedule(2025)
                
                if not real_games:
                    logger.error("❌ No real NFL games loaded!")
                    return False
                
                # 2. Sync Spiele in Datenbank
                synced_count = 0
                for game_data in real_games:
                    if self.sync_game_to_database(game_data, db, Team, Match):
                        synced_count += 1
                
                # 3. Lade echte Ergebnisse für abgeschlossene Wochen
                for week in [1, 2]:  # Woche 1 und 2 sollten abgeschlossen sein
                    real_scores = self.get_real_nfl_scores(2025, week)
                    for score_data in real_scores:
                        self.update_game_results(score_data, db, Match)
                
                db.session.commit()
                logger.info(f"✅ Real NFL data sync completed: {synced_count} games synced")
                return True
                
            except Exception as e:
                logger.error(f"❌ Real NFL data sync failed: {e}")
                db.session.rollback()
                return False
    
    def sync_game_to_database(self, game_data, db, Team, Match):
        """Synchronisiert ein einzelnes Spiel in die Datenbank"""
        try:
            # Teams finden
            away_team = Team.query.filter_by(abbreviation=game_data['away_team']).first()
            home_team = Team.query.filter_by(abbreviation=game_data['home_team']).first()
            
            if not away_team or not home_team:
                logger.warning(f"⚠️ Teams not found: {game_data['away_team']} vs {game_data['home_team']}")
                return False
            
            # Prüfe ob Spiel bereits existiert
            existing_match = Match.query.filter_by(
                week=game_data['week'],
                away_team_id=away_team.id,
                home_team_id=home_team.id
            ).first()
            
            if existing_match:
                # Update existierendes Spiel
                existing_match.start_time = game_data['start_time']
                existing_match.is_completed = game_data['is_completed']
                if game_data['winner_team']:
                    winner_team = Team.query.filter_by(abbreviation=game_data['winner_team']).first()
                    if winner_team:
                        existing_match.winner_team_id = winner_team.id
                existing_match.away_score = game_data['away_score']
                existing_match.home_score = game_data['home_score']
            else:
                # Erstelle neues Spiel
                winner_team_id = None
                if game_data['winner_team']:
                    winner_team = Team.query.filter_by(abbreviation=game_data['winner_team']).first()
                    if winner_team:
                        winner_team_id = winner_team.id
                
                new_match = Match(
                    week=game_data['week'],
                    away_team_id=away_team.id,
                    home_team_id=home_team.id,
                    start_time=game_data['start_time'],
                    is_completed=game_data['is_completed'],
                    winner_team_id=winner_team_id,
                    away_score=game_data['away_score'],
                    home_score=game_data['home_score']
                )
                db.session.add(new_match)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to sync game: {e}")
            return False
    
    def update_game_results(self, score_data, db, Match):
        """Aktualisiert Spielergebnisse in der Datenbank"""
        try:
            # Finde Match in Datenbank
            match = Match.query.filter_by(week=score_data['week']).join(
                Team, Match.away_team_id == Team.id
            ).filter(Team.abbreviation == score_data['away_team']).first()
            
            if match and score_data['is_completed']:
                match.is_completed = True
                match.away_score = score_data['away_score']
                match.home_score = score_data['home_score']
                
                if score_data['winner_team']:
                    winner_team = Team.query.filter_by(abbreviation=score_data['winner_team']).first()
                    if winner_team:
                        match.winner_team_id = winner_team.id
                
                logger.info(f"✅ Updated game result: {score_data['away_team']} vs {score_data['home_team']}")
            
        except Exception as e:
            logger.error(f"❌ Failed to update game result: {e}")

if __name__ == '__main__':
    # Test der echten NFL-Daten Sync
    sync = RealNFLDataSync()
    print(f"API Key configured: {sync.api_key is not None}")
    print(f"Current NFL Week: {sync.get_current_nfl_week()}")

