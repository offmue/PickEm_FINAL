"""
Echte Punkte-Berechnung für NFL PickEm 2025
Berechnet Punkte basierend auf echten NFL Ergebnissen
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class RealPointsCalculator:
    """Berechnet Punkte basierend auf echten NFL Ergebnissen"""
    
    def __init__(self, app, db):
        self.app = app
        self.db = db
    
    def calculate_user_points(self, user_id):
        """Berechnet Gesamtpunkte für einen User basierend auf echten Ergebnissen"""
        from app import Pick, Match, Team
        
        with self.app.app_context():
            try:
                # Alle Picks des Users für abgeschlossene Spiele
                user_picks = self.db.session.query(Pick, Match).join(
                    Match, Pick.match_id == Match.id
                ).filter(
                    Pick.user_id == user_id,
                    Match.is_completed == True,
                    Match.winner_team_id.isnot(None)
                ).all()
                
                total_points = 0
                
                for pick, match in user_picks:
                    # Punkte-Logik: +1 Punkt wenn gewähltes Team gewinnt
                    if pick.chosen_team_id == match.winner_team_id:
                        total_points += 1
                        logger.debug(f"✅ User {user_id} gets 1 point for correct pick in match {match.id}")
                    else:
                        logger.debug(f"❌ User {user_id} gets 0 points for incorrect pick in match {match.id}")
                
                logger.info(f"📊 User {user_id} total points: {total_points}")
                return total_points
                
            except Exception as e:
                logger.error(f"❌ Failed to calculate points for user {user_id}: {e}")
                return 0
    
    def calculate_all_user_points(self):
        """Berechnet Punkte für alle User"""
        from app import User
        
        with self.app.app_context():
            try:
                users = User.query.all()
                user_points = {}
                
                for user in users:
                    points = self.calculate_user_points(user.id)
                    user_points[user.username] = points
                
                logger.info(f"📊 All user points calculated: {user_points}")
                return user_points
                
            except Exception as e:
                logger.error(f"❌ Failed to calculate all user points: {e}")
                return {}
    
    def get_leaderboard(self):
        """Erstellt Leaderboard basierend auf echten Punkten"""
        from app import User
        
        with self.app.app_context():
            try:
                users = User.query.all()
                leaderboard = []
                
                for user in users:
                    points = self.calculate_user_points(user.id)
                    leaderboard.append({
                        'username': user.username,
                        'points': points,
                        'user_id': user.id
                    })
                
                # Sortiere nach Punkten (höchste zuerst)
                leaderboard.sort(key=lambda x: x['points'], reverse=True)
                
                # Füge Ränge hinzu
                for i, entry in enumerate(leaderboard):
                    entry['rank'] = i + 1
                
                logger.info(f"🏆 Leaderboard created: {leaderboard}")
                return leaderboard
                
            except Exception as e:
                logger.error(f"❌ Failed to create leaderboard: {e}")
                return []
    
    def validate_completed_matches(self):
        """Validiert alle abgeschlossenen Spiele und berechnet Punkte neu"""
        from app import Match, Pick, User, Team
        
        with self.app.app_context():
            try:
                # Alle abgeschlossenen Spiele
                completed_matches = Match.query.filter(
                    Match.is_completed == True,
                    Match.winner_team_id.isnot(None)
                ).all()
                
                logger.info(f"🔄 Validating {len(completed_matches)} completed matches...")
                
                validation_results = []
                
                for match in completed_matches:
                    # Alle Picks für dieses Spiel
                    picks = Pick.query.filter_by(match_id=match.id).all()
                    
                    match_result = {
                        'match_id': match.id,
                        'week': match.week,
                        'away_team': match.away_team.abbreviation,
                        'home_team': match.home_team.abbreviation,
                        'winner': match.winner_team.abbreviation,
                        'away_score': match.away_score,
                        'home_score': match.home_score,
                        'picks': []
                    }
                    
                    for pick in picks:
                        user = User.query.get(pick.user_id)
                        chosen_team = Team.query.get(pick.chosen_team_id)
                        
                        is_correct = pick.chosen_team_id == match.winner_team_id
                        points = 1 if is_correct else 0
                        
                        pick_result = {
                            'username': user.username,
                            'chosen_team': chosen_team.abbreviation,
                            'is_correct': is_correct,
                            'points': points
                        }
                        
                        match_result['picks'].append(pick_result)
                        
                        logger.debug(f"📊 {user.username} picked {chosen_team.abbreviation}, "
                                   f"winner was {match.winner_team.abbreviation}, "
                                   f"correct: {is_correct}, points: {points}")
                    
                    validation_results.append(match_result)
                
                logger.info("✅ Match validation completed")
                return validation_results
                
            except Exception as e:
                logger.error(f"❌ Failed to validate completed matches: {e}")
                return []
    
    def get_user_pick_history(self, user_id):
        """Holt Pick-Historie für einen User mit Ergebnissen"""
        from app import Pick, Match, Team, User
        
        with self.app.app_context():
            try:
                user = User.query.get(user_id)
                if not user:
                    return []
                
                # Alle Picks des Users mit Match-Details
                picks_query = self.db.session.query(Pick, Match, Team).join(
                    Match, Pick.match_id == Match.id
                ).join(
                    Team, Pick.chosen_team_id == Team.id
                ).filter(Pick.user_id == user_id).order_by(Match.week).all()
                
                pick_history = []
                
                for pick, match, chosen_team in picks_query:
                    away_team = Team.query.get(match.away_team_id)
                    home_team = Team.query.get(match.home_team_id)
                    winner_team = Team.query.get(match.winner_team_id) if match.winner_team_id else None
                    
                    is_correct = None
                    points = 0
                    
                    if match.is_completed and winner_team:
                        is_correct = pick.chosen_team_id == match.winner_team_id
                        points = 1 if is_correct else 0
                    
                    pick_entry = {
                        'week': match.week,
                        'away_team': away_team.abbreviation,
                        'home_team': home_team.abbreviation,
                        'chosen_team': chosen_team.abbreviation,
                        'winner_team': winner_team.abbreviation if winner_team else None,
                        'is_completed': match.is_completed,
                        'is_correct': is_correct,
                        'points': points,
                        'away_score': match.away_score,
                        'home_score': match.home_score
                    }
                    
                    pick_history.append(pick_entry)
                
                logger.info(f"📋 Pick history for {user.username}: {len(pick_history)} picks")
                return pick_history
                
            except Exception as e:
                logger.error(f"❌ Failed to get pick history for user {user_id}: {e}")
                return []

if __name__ == '__main__':
    print("Real Points Calculator ready!")
    print("Calculates points based on real NFL results")

