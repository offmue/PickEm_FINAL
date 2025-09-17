"""
Echte Team Usage Tracking für NFL PickEm 2025
Trackt Team Usage basierend auf echten Spielbeginnen
"""

import logging
from datetime import datetime
import pytz

logger = logging.getLogger(__name__)

class RealTeamUsageTracker:
    """Trackt Team Usage basierend auf echten Spielbeginnen"""
    
    def __init__(self, app, db):
        self.app = app
        self.db = db
        self.vienna_tz = pytz.timezone('Europe/Vienna')
    
    def process_game_start_usage(self, match_id):
        """Verarbeitet Team Usage wenn ein Spiel beginnt"""
        from app import Match, Pick, Team, TeamWinnerUsage, TeamLoserUsage, User
        
        with self.app.app_context():
            try:
                match = Match.query.get(match_id)
                if not match:
                    logger.error(f"❌ Match {match_id} not found")
                    return False
                
                # Prüfe ob Spiel bereits begonnen hat
                now = datetime.now(self.vienna_tz)
                if match.start_time > now:
                    logger.debug(f"⏰ Match {match_id} has not started yet")
                    return False
                
                # Alle Picks für dieses Spiel
                picks = Pick.query.filter_by(match_id=match_id).all()
                
                logger.info(f"🔄 Processing team usage for match {match_id}: {len(picks)} picks")
                
                for pick in picks:
                    self.create_team_usage_for_pick(pick, match)
                
                self.db.session.commit()
                logger.info(f"✅ Team usage processed for match {match_id}")
                return True
                
            except Exception as e:
                logger.error(f"❌ Failed to process team usage for match {match_id}: {e}")
                self.db.session.rollback()
                return False
    
    def create_team_usage_for_pick(self, pick, match):
        """Erstellt Team Usage Einträge für einen Pick"""
        from app import Team, TeamWinnerUsage, TeamLoserUsage
        
        try:
            chosen_team = Team.query.get(pick.chosen_team_id)
            if not chosen_team:
                logger.error(f"❌ Chosen team {pick.chosen_team_id} not found")
                return
            
            # Bestimme Gewinner und Verlierer Team
            if pick.chosen_team_id == match.away_team_id:
                winner_team_id = match.away_team_id
                loser_team_id = match.home_team_id
            else:
                winner_team_id = match.home_team_id
                loser_team_id = match.away_team_id
            
            # Winner Usage erstellen/prüfen
            existing_winner_usage = TeamWinnerUsage.query.filter_by(
                user_id=pick.user_id,
                team_id=winner_team_id
            ).first()
            
            if not existing_winner_usage:
                winner_usage = TeamWinnerUsage(
                    user_id=pick.user_id,
                    team_id=winner_team_id
                )
                self.db.session.add(winner_usage)
                logger.debug(f"✅ Created winner usage: User {pick.user_id}, Team {winner_team_id}")
            
            # Loser Usage erstellen/prüfen
            existing_loser_usage = TeamLoserUsage.query.filter_by(
                user_id=pick.user_id,
                team_id=loser_team_id
            ).first()
            
            if not existing_loser_usage:
                loser_usage = TeamLoserUsage(
                    user_id=pick.user_id,
                    team_id=loser_team_id
                )
                self.db.session.add(loser_usage)
                logger.debug(f"✅ Created loser usage: User {pick.user_id}, Team {loser_team_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to create team usage for pick {pick.id}: {e}")
    
    def check_team_availability(self, user_id, team_id, pick_type='winner'):
        """Prüft ob ein Team für einen User noch verfügbar ist"""
        from app import TeamWinnerUsage, TeamLoserUsage
        
        with self.app.app_context():
            try:
                if pick_type == 'winner':
                    # Prüfe Winner Usage (max 2x)
                    usage_count = TeamWinnerUsage.query.filter_by(
                        user_id=user_id,
                        team_id=team_id
                    ).count()
                    
                    is_available = usage_count < 2
                    logger.debug(f"🔍 Team {team_id} winner availability for user {user_id}: {is_available} (used {usage_count}/2)")
                    return is_available
                    
                elif pick_type == 'loser':
                    # Prüfe Loser Usage (max 1x)
                    usage_count = TeamLoserUsage.query.filter_by(
                        user_id=user_id,
                        team_id=team_id
                    ).count()
                    
                    is_available = usage_count < 1
                    logger.debug(f"🔍 Team {team_id} loser availability for user {user_id}: {is_available} (used {usage_count}/1)")
                    return is_available
                
                return False
                
            except Exception as e:
                logger.error(f"❌ Failed to check team availability: {e}")
                return False
    
    def get_user_team_usage(self, user_id):
        """Holt Team Usage für einen User"""
        from app import TeamWinnerUsage, TeamLoserUsage, Team
        
        with self.app.app_context():
            try:
                # Winner Usage
                winner_usage = self.db.session.query(TeamWinnerUsage, Team).join(
                    Team, TeamWinnerUsage.team_id == Team.id
                ).filter(TeamWinnerUsage.user_id == user_id).all()
                
                # Loser Usage
                loser_usage = self.db.session.query(TeamLoserUsage, Team).join(
                    Team, TeamLoserUsage.team_id == Team.id
                ).filter(TeamLoserUsage.user_id == user_id).all()
                
                winner_teams = []
                for usage, team in winner_usage:
                    winner_teams.append({
                        'name': team.name,
                        'abbreviation': team.abbreviation,
                        'logo_url': team.logo_url
                    })
                
                loser_teams = []
                for usage, team in loser_usage:
                    loser_teams.append({
                        'name': team.name,
                        'abbreviation': team.abbreviation,
                        'logo_url': team.logo_url
                    })
                
                usage_data = {
                    'winner_teams': winner_teams,
                    'loser_teams': loser_teams,
                    'winner_count': len(winner_teams),
                    'loser_count': len(loser_teams)
                }
                
                logger.info(f"📊 Team usage for user {user_id}: {usage_data['winner_count']} winners, {usage_data['loser_count']} losers")
                return usage_data
                
            except Exception as e:
                logger.error(f"❌ Failed to get team usage for user {user_id}: {e}")
                return {'winner_teams': [], 'loser_teams': [], 'winner_count': 0, 'loser_count': 0}
    
    def validate_pick_availability(self, user_id, match_id, chosen_team_id):
        """Validiert ob ein Pick möglich ist basierend auf Team Usage"""
        from app import Match, Team
        
        with self.app.app_context():
            try:
                match = Match.query.get(match_id)
                if not match:
                    return False, "Spiel nicht gefunden"
                
                # Prüfe ob Spiel bereits begonnen hat
                now = datetime.now(self.vienna_tz)
                if match.start_time <= now:
                    return False, "Spiel hat bereits begonnen"
                
                # Bestimme welches Team als Gewinner und welches als Verlierer getippt wird
                if chosen_team_id == match.away_team_id:
                    winner_team_id = match.away_team_id
                    loser_team_id = match.home_team_id
                elif chosen_team_id == match.home_team_id:
                    winner_team_id = match.home_team_id
                    loser_team_id = match.away_team_id
                else:
                    return False, "Gewähltes Team spielt nicht in diesem Spiel"
                
                # Prüfe Winner Team Verfügbarkeit (max 2x)
                if not self.check_team_availability(user_id, winner_team_id, 'winner'):
                    winner_team = Team.query.get(winner_team_id)
                    return False, f"{winner_team.name} bereits 2x als Gewinner verwendet"
                
                # Prüfe Loser Team Verfügbarkeit (max 1x)
                if not self.check_team_availability(user_id, loser_team_id, 'loser'):
                    loser_team = Team.query.get(loser_team_id)
                    return False, f"{loser_team.name} bereits 1x als Verlierer verwendet"
                
                return True, "Pick ist möglich"
                
            except Exception as e:
                logger.error(f"❌ Failed to validate pick availability: {e}")
                return False, "Validierung fehlgeschlagen"
    
    def process_all_started_games(self):
        """Verarbeitet Team Usage für alle bereits begonnenen Spiele"""
        from app import Match
        
        with self.app.app_context():
            try:
                now = datetime.now(self.vienna_tz)
                
                # Alle Spiele die bereits begonnen haben
                started_matches = Match.query.filter(Match.start_time <= now).all()
                
                logger.info(f"🔄 Processing team usage for {len(started_matches)} started games...")
                
                processed_count = 0
                for match in started_matches:
                    if self.process_game_start_usage(match.id):
                        processed_count += 1
                
                logger.info(f"✅ Processed team usage for {processed_count} games")
                return processed_count
                
            except Exception as e:
                logger.error(f"❌ Failed to process all started games: {e}")
                return 0

if __name__ == '__main__':
    print("Real Team Usage Tracker ready!")
    print("Tracks team usage based on real game start times")

