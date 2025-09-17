"""
ESPN Data Sync for NFL PickEm 2025
Handles automatic syncing of real NFL data from ESPN API
"""

import logging
from datetime import datetime, timezone
from espn_api_client import ESPNAPIClient

logger = logging.getLogger(__name__)

class ESPNDataSync:
    """Handles syncing of ESPN NFL data to database"""
    
    def __init__(self, app, db):
        self.app = app
        self.db = db
        self.espn_client = ESPNAPIClient()
        
        # Import models within app context
        with app.app_context():
            from app import Team, Match
            self.Team = Team
            self.Match = Match
    
    def sync_teams(self):
        """Sync NFL teams from ESPN"""
        try:
            logger.info("🔄 Syncing NFL teams from ESPN...")
            
            espn_teams = self.espn_client.get_teams()
            
            with self.app.app_context():
                teams_created = 0
                teams_updated = 0
                
                for espn_team in espn_teams:
                    # Check if team exists
                    team = self.Team.query.filter_by(abbreviation=espn_team['abbreviation']).first()
                    
                    if team:
                        # Update existing team
                        team.name = espn_team['name']
                        team.logo_url = espn_team['logo_url']
                        teams_updated += 1
                    else:
                        # Create new team
                        team = self.Team(
                            name=espn_team['name'],
                            abbreviation=espn_team['abbreviation'],
                            logo_url=espn_team['logo_url']
                        )
                        self.db.session.add(team)
                        teams_created += 1
                
                self.db.session.commit()
                logger.info(f"✅ Teams sync completed: {teams_created} created, {teams_updated} updated")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error syncing teams: {e}")
            return False
    
    def sync_schedule(self, week=None):
        """Sync NFL schedule from ESPN"""
        try:
            if week:
                logger.info(f"🔄 Syncing NFL schedule for week {week} from ESPN...")
                espn_games = self.espn_client.get_schedule(week=week)
            else:
                logger.info("🔄 Syncing complete NFL schedule from ESPN...")
                espn_games = self.espn_client.get_schedule()
            
            with self.app.app_context():
                games_created = 0
                games_updated = 0
                
                for espn_game in espn_games:
                    # Find teams by abbreviation
                    home_team = self.Team.query.filter_by(abbreviation=self._map_espn_team_id(espn_game['home_team_id'])).first()
                    away_team = self.Team.query.filter_by(abbreviation=self._map_espn_team_id(espn_game['away_team_id'])).first()
                    
                    if not home_team or not away_team:
                        logger.warning(f"⚠️ Teams not found for game: {espn_game['away_team_name']} @ {espn_game['home_team_name']}")
                        continue
                    
                    # Check if match exists
                    match = self.Match.query.filter_by(
                        week=espn_game['week'],
                        home_team_id=home_team.id,
                        away_team_id=away_team.id
                    ).first()
                    
                    if match:
                        # Update existing match
                        match.start_time = espn_game['start_time']
                        if espn_game['is_completed']:
                            match.is_completed = True
                            match.home_score = espn_game['home_score']
                            match.away_score = espn_game['away_score']
                            # Set winner
                            if espn_game['winner_team_id']:
                                winner_team = self.Team.query.filter_by(abbreviation=self._map_espn_team_id(espn_game['winner_team_id'])).first()
                                if winner_team:
                                    match.winner_team_id = winner_team.id
                        games_updated += 1
                    else:
                        # Create new match
                        match = self.Match(
                            week=espn_game['week'],
                            home_team_id=home_team.id,
                            away_team_id=away_team.id,
                            start_time=espn_game['start_time'],
                            is_completed=espn_game['is_completed'],
                            home_score=espn_game['home_score'],
                            away_score=espn_game['away_score']
                        )
                        
                        # Set winner if completed
                        if espn_game['is_completed'] and espn_game['winner_team_id']:
                            winner_team = self.Team.query.filter_by(abbreviation=self._map_espn_team_id(espn_game['winner_team_id'])).first()
                            if winner_team:
                                match.winner_team_id = winner_team.id
                        
                        self.db.session.add(match)
                        games_created += 1
                
                self.db.session.commit()
                logger.info(f"✅ Schedule sync completed: {games_created} created, {games_updated} updated")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error syncing schedule: {e}")
            return False
    
    def sync_results(self, week):
        """Sync game results for a specific week"""
        try:
            logger.info(f"🔄 Syncing game results for week {week} from ESPN...")
            
            espn_results = self.espn_client.get_game_results(week=week)
            
            with self.app.app_context():
                results_updated = 0
                
                for espn_result in espn_results:
                    # Find the match by ESPN ID or teams
                    match = self.Match.query.filter_by(week=week).all()
                    
                    for m in match:
                        home_team_abbr = self._map_espn_team_id(espn_result.get('home_team_id', ''))
                        away_team_abbr = self._map_espn_team_id(espn_result.get('away_team_id', ''))
                        
                        if (m.home_team.abbreviation == home_team_abbr and 
                            m.away_team.abbreviation == away_team_abbr):
                            
                            # Update match with results
                            m.is_completed = True
                            m.home_score = espn_result['home_score']
                            m.away_score = espn_result['away_score']
                            
                            # Set winner
                            if espn_result['winner_team_id']:
                                winner_team = self.Team.query.filter_by(
                                    abbreviation=self._map_espn_team_id(espn_result['winner_team_id'])
                                ).first()
                                if winner_team:
                                    m.winner_team_id = winner_team.id
                            
                            results_updated += 1
                            break
                
                self.db.session.commit()
                logger.info(f"✅ Results sync completed: {results_updated} games updated")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error syncing results: {e}")
            return False
    
    def get_current_week(self):
        """Get current NFL week from ESPN"""
        try:
            current_week = self.espn_client.get_current_week()
            logger.info(f"✅ Current NFL week: {current_week}")
            return current_week
        except Exception as e:
            logger.error(f"❌ Error getting current week: {e}")
            return 3  # Default fallback
    
    def _map_espn_team_id(self, espn_id):
        """Map ESPN team ID to our abbreviation format"""
        # ESPN uses different IDs, map them to standard abbreviations
        espn_to_abbr = {
            '22': 'ARI',  # Arizona Cardinals
            '1': 'ATL',   # Atlanta Falcons
            '33': 'BAL',  # Baltimore Ravens
            '2': 'BUF',   # Buffalo Bills
            '29': 'CAR',  # Carolina Panthers
            '3': 'CHI',   # Chicago Bears
            '4': 'CIN',   # Cincinnati Bengals
            '5': 'CLE',   # Cleveland Browns
            '6': 'DAL',   # Dallas Cowboys
            '7': 'DEN',   # Denver Broncos
            '8': 'DET',   # Detroit Lions
            '9': 'GB',    # Green Bay Packers
            '34': 'HOU',  # Houston Texans
            '11': 'IND',  # Indianapolis Colts
            '30': 'JAX',  # Jacksonville Jaguars
            '12': 'KC',   # Kansas City Chiefs
            '13': 'LV',   # Las Vegas Raiders
            '24': 'LAC',  # Los Angeles Chargers
            '14': 'LAR',  # Los Angeles Rams
            '15': 'MIA',  # Miami Dolphins
            '16': 'MIN',  # Minnesota Vikings
            '17': 'NE',   # New England Patriots
            '18': 'NO',   # New Orleans Saints
            '19': 'NYG',  # New York Giants
            '20': 'NYJ',  # New York Jets
            '21': 'PHI',  # Philadelphia Eagles
            '23': 'PIT',  # Pittsburgh Steelers
            '25': 'SF',   # San Francisco 49ers
            '26': 'SEA',  # Seattle Seahawks
            '27': 'TB',   # Tampa Bay Buccaneers
            '10': 'TEN',  # Tennessee Titans
            '28': 'WAS'   # Washington Commanders
        }
        
        return espn_to_abbr.get(str(espn_id), str(espn_id))
    
    def full_sync(self):
        """Perform complete data sync"""
        try:
            logger.info("🚀 Starting full ESPN data sync...")
            
            # Sync teams first
            if not self.sync_teams():
                return False
            
            # Sync complete schedule
            if not self.sync_schedule():
                return False
            
            # Sync results for completed weeks
            current_week = self.get_current_week()
            for week in range(1, current_week):
                self.sync_results(week)
            
            logger.info("✅ Full ESPN data sync completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error in full sync: {e}")
            return False

# Test function
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # This would normally be called with Flask app and db
    print("ESPN Data Sync module loaded successfully")

