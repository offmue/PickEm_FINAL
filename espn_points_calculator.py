"""
ESPN Points Calculator for NFL PickEm 2025
Calculates user points based on real NFL game results
"""

import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class ESPNPointsCalculator:
    """Calculates user points based on ESPN NFL results"""
    
    def __init__(self, app, db):
        self.app = app
        self.db = db
        
        # Import models within app context
        with app.app_context():
            from app import User, Pick, Match, Team, TeamWinnerUsage, TeamLoserUsage
            self.User = User
            self.Pick = Pick
            self.Match = Match
            self.Team = Team
            self.TeamWinnerUsage = TeamWinnerUsage
            self.TeamLoserUsage = TeamLoserUsage
    
    def calculate_points_for_week(self, week):
        """Calculate points for all users for a specific week"""
        try:
            logger.info(f"🔄 Calculating points for week {week}...")
            
            with self.app.app_context():
                # Get all completed matches for this week
                completed_matches = self.Match.query.filter_by(
                    week=week, 
                    is_completed=True
                ).all()
                
                if not completed_matches:
                    logger.info(f"⚠️ No completed matches found for week {week}")
                    return True
                
                points_awarded = 0
                
                for match in completed_matches:
                    if not match.winner_team_id:
                        logger.warning(f"⚠️ Match {match.id} completed but no winner set")
                        continue
                    
                    # Get all picks for this match
                    picks = self.Pick.query.filter_by(match_id=match.id).all()
                    
                    for pick in picks:
                        # Award point if user picked the winning team
                        if pick.chosen_team_id == match.winner_team_id:
                            # User gets 1 point for correct pick
                            logger.info(f"✅ User {pick.user.username} gets 1 point for correct pick in week {week}")
                            points_awarded += 1
                        else:
                            logger.info(f"❌ User {pick.user.username} gets 0 points for incorrect pick in week {week}")
                
                logger.info(f"✅ Points calculation completed for week {week}: {points_awarded} points awarded")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error calculating points for week {week}: {e}")
            return False
    
    def calculate_all_points(self):
        """Recalculate points for all completed weeks"""
        try:
            logger.info("🔄 Recalculating all user points...")
            
            with self.app.app_context():
                # Get all completed weeks
                completed_weeks = self.db.session.query(self.Match.week).filter_by(is_completed=True).distinct().all()
                
                total_points_awarded = 0
                
                for (week,) in completed_weeks:
                    if self.calculate_points_for_week(week):
                        # Count points for this week
                        week_matches = self.Match.query.filter_by(week=week, is_completed=True).all()
                        for match in week_matches:
                            if match.winner_team_id:
                                correct_picks = self.Pick.query.filter_by(
                                    match_id=match.id,
                                    chosen_team_id=match.winner_team_id
                                ).count()
                                total_points_awarded += correct_picks
                
                logger.info(f"✅ All points recalculated: {total_points_awarded} total points awarded")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error recalculating all points: {e}")
            return False
    
    def get_user_score(self, user_id):
        """Get total score for a specific user"""
        try:
            with self.app.app_context():
                user = self.User.query.get(user_id)
                if not user:
                    return 0
                
                total_points = 0
                
                # Get all user picks
                picks = self.Pick.query.filter_by(user_id=user_id).all()
                
                for pick in picks:
                    match = pick.match
                    if match.is_completed and match.winner_team_id:
                        if pick.chosen_team_id == match.winner_team_id:
                            total_points += 1
                
                return total_points
                
        except Exception as e:
            logger.error(f"❌ Error getting user score: {e}")
            return 0
    
    def get_leaderboard(self):
        """Get leaderboard with all user scores"""
        try:
            with self.app.app_context():
                users = self.User.query.all()
                leaderboard = []
                
                for user in users:
                    score = self.get_user_score(user.id)
                    leaderboard.append({
                        'user_id': user.id,
                        'username': user.username,
                        'score': score
                    })
                
                # Sort by score (highest first)
                leaderboard.sort(key=lambda x: x['score'], reverse=True)
                
                # Add rank
                for i, entry in enumerate(leaderboard):
                    entry['rank'] = i + 1
                
                logger.info(f"✅ Leaderboard generated with {len(leaderboard)} users")
                return leaderboard
                
        except Exception as e:
            logger.error(f"❌ Error generating leaderboard: {e}")
            return []
    
    def process_team_usage_for_started_games(self):
        """Process team usage for games that have started"""
        try:
            logger.info("🔄 Processing team usage for started games...")
            
            with self.app.app_context():
                now = datetime.now(timezone.utc)
                
                # Get all matches that have started but haven't been processed for team usage
                started_matches = self.Match.query.filter(
                    self.Match.start_time <= now,
                    self.Match.is_completed == False  # Only process once
                ).all()
                
                usage_processed = 0
                
                for match in started_matches:
                    # Get all picks for this match
                    picks = self.Pick.query.filter_by(match_id=match.id).all()
                    
                    for pick in picks:
                        # Process winner usage
                        existing_winner = self.TeamWinnerUsage.query.filter_by(
                            user_id=pick.user_id,
                            team_id=pick.chosen_team_id
                        ).first()
                        
                        if not existing_winner:
                            winner_usage = self.TeamWinnerUsage(
                                user_id=pick.user_id,
                                team_id=pick.chosen_team_id
                            )
                            self.db.session.add(winner_usage)
                        
                        # Process loser usage (the other team)
                        loser_team_id = match.away_team_id if pick.chosen_team_id == match.home_team_id else match.home_team_id
                        
                        existing_loser = self.TeamLoserUsage.query.filter_by(
                            user_id=pick.user_id,
                            team_id=loser_team_id
                        ).first()
                        
                        if not existing_loser:
                            loser_usage = self.TeamLoserUsage(
                                user_id=pick.user_id,
                                team_id=loser_team_id
                            )
                            self.db.session.add(loser_usage)
                        
                        usage_processed += 1
                
                self.db.session.commit()
                logger.info(f"✅ Team usage processed for {usage_processed} picks")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error processing team usage: {e}")
            return False
    
    def validate_completed_games(self):
        """Validate and process all completed games"""
        try:
            logger.info("🔄 Validating completed games...")
            
            # Process team usage for started games
            self.process_team_usage_for_started_games()
            
            # Recalculate all points
            self.calculate_all_points()
            
            logger.info("✅ Game validation completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error validating games: {e}")
            return False

# Test function
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # This would normally be called with Flask app and db
    print("ESPN Points Calculator module loaded successfully")

