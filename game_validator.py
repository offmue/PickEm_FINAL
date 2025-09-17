#!/usr/bin/env python3
"""
NFL PickEm Game Validator Service
Automatically validates game results from ESPN and updates the database
"""

import requests
import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time
import schedule
import threading

# Configure logging with maximum deployment compatibility
import os
import logging

# Simple console-only logging for deployment compatibility
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class NFLGameValidator:
    """Validates NFL game results and updates the database"""
    
    def __init__(self, db_path: str = None):
        # Use relative path for Render compatibility
        if db_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # Try multiple possible database locations
            possible_paths = [
                os.path.join(current_dir, 'instance', 'nfl_pickem.db'),
                os.path.join(current_dir, 'nfl_pickem.db'),
                'instance/nfl_pickem.db',
                'nfl_pickem.db'
            ]
            
            db_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    db_path = path
                    break
            
            # If no database found, use the first path (will be created if needed)
            if db_path is None:
                db_path = possible_paths[0]
                # Ensure instance directory exists
                instance_dir = os.path.dirname(db_path)
                if not os.path.exists(instance_dir):
                    os.makedirs(instance_dir, exist_ok=True)
        
        self.db_path = db_path
        self.espn_base_url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl"
        
    def get_database_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def row_to_dict(self, row) -> dict:
        """Convert sqlite3.Row to dictionary for safe .get() access"""
        if row is None:
            return {}
        return dict(row)
    
    def get_espn_scoreboard(self, week: int, year: int = 2025) -> Optional[Dict]:
        """Get ESPN scoreboard data for a specific week"""
        try:
            url = f"{self.espn_base_url}/scoreboard"
            params = {
                'seasontype': 2,  # Regular season
                'week': week,
                'year': year
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Successfully fetched ESPN data for Week {week}")
            return data
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch ESPN data for Week {week}: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse ESPN JSON for Week {week}: {e}")
            return None
    
    def parse_espn_game_result(self, game_data: Dict) -> Optional[Dict]:
        """Parse ESPN game data to extract result information"""
        try:
            # Check if game is completed
            if game_data.get('status', {}).get('type', {}).get('name') != 'STATUS_FINAL':
                return None
            
            competitions = game_data.get('competitions', [])
            if not competitions:
                return None
            
            competition = competitions[0]
            competitors = competition.get('competitors', [])
            
            if len(competitors) != 2:
                return None
            
            # Extract team information and scores
            home_team = None
            away_team = None
            home_score = None
            away_score = None
            
            for competitor in competitors:
                team_name = competitor.get('team', {}).get('displayName', '')
                score = int(competitor.get('score', 0))
                is_home = competitor.get('homeAway') == 'home'
                
                if is_home:
                    home_team = team_name
                    home_score = score
                else:
                    away_team = team_name
                    away_score = score
            
            if not all([home_team, away_team, home_score is not None, away_score is not None]):
                return None
            
            # Determine winner team ID (we'll need to look this up)
            winner_name = home_team if home_score > away_score else away_team
            
            return {
                'home_team': home_team,
                'away_team': away_team,
                'home_score': home_score,
                'away_score': away_score,
                'winner_name': winner_name,
                'winner_team_id': None,  # Will be set later
                'result': f"{winner_name} {max(home_score, away_score)} - {min(home_score, away_score)}"
            }
            
        except Exception as e:
            logger.error(f"Failed to parse ESPN game data: {e}")
            return None
    
    def update_game_result(self, conn: sqlite3.Connection, match_id: int, result_data: Dict) -> bool:
        """Update game result in the database"""
        try:
            cursor = conn.cursor()
            
            # Safely extract required data
            winner_team_id = result_data.get('winner_team_id')
            home_score = result_data.get('home_score')
            away_score = result_data.get('away_score')
            result_text = result_data.get('result', 'Unknown result')
            
            if winner_team_id is None or home_score is None or away_score is None:
                logger.warning(f"Missing required data for match {match_id}: winner_id={winner_team_id}, home={home_score}, away={away_score}")
                return False
            
            # Update the match with result
            cursor.execute("""
                UPDATE match 
                SET is_completed = 1, winner_team_id = ?, home_score = ?, away_score = ?
                WHERE id = ?
            """, (winner_team_id, home_score, away_score, match_id))
            
            if cursor.rowcount == 0:
                logger.warning(f"No match found with ID {match_id}")
                return False
            
            conn.commit()
            logger.info(f"Updated match {match_id}: {result_text}")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Database error updating match {match_id}: {e}")
            conn.rollback()
            return False
    
    def calculate_user_points(self, conn: sqlite3.Connection, week: int) -> None:
        """Calculate and update user points for completed games in a week"""
        try:
            cursor = conn.cursor()
            
            # Get all completed matches for the week
            cursor.execute("""
                SELECT m.id, m.winner_team_id, ht.name as home_team, at.name as away_team
                FROM match m
                JOIN team ht ON m.home_team_id = ht.id
                JOIN team at ON m.away_team_id = at.id
                WHERE m.week = ? AND m.is_completed = 1
            """, (week,))
            
            completed_matches = cursor.fetchall()
            
            for match in completed_matches:
                match_dict = self.row_to_dict(match)
                match_id = match_dict.get('id')
                winner_team_id = match_dict.get('winner_team_id')
                
                if match_id is None or winner_team_id is None:
                    logger.warning(f"Missing match data: id={match_id}, winner_id={winner_team_id}")
                    continue
                
                # Get all picks for this match
                cursor.execute("""
                    SELECT p.id, p.user_id, p.chosen_team_id, u.username
                    FROM pick p
                    JOIN user u ON p.user_id = u.id
                    WHERE p.match_id = ?
                """, (match_id,))
                
                picks = cursor.fetchall()
                
                for pick in picks:
                    # Safely extract pick data
                    pick_dict = self.row_to_dict(pick)
                    chosen_team_id = pick_dict.get('chosen_team_id')
                    username = pick_dict.get('username', 'Unknown')
                    
                    if chosen_team_id is None:
                        logger.warning(f"Missing chosen_team_id for pick")
                        continue
                    
                    # Check if prediction was correct
                    is_correct = chosen_team_id == winner_team_id
                    points = 1 if is_correct else 0
                    
                    # Log the result (no database update needed for is_correct/points)
                    logger.info(f"User {username}: Team ID {chosen_team_id} -> {'✅' if is_correct else '❌'} ({points} points)")
            
            conn.commit()
            logger.info(f"Updated points for Week {week}")
            
        except sqlite3.Error as e:
            logger.error(f"Database error calculating points for Week {week}: {e}")
            conn.rollback()
    
    def update_team_eliminations(self, conn: sqlite3.Connection, week: int) -> None:
        """
        NOTE: Team eliminations are now handled immediately when picks are made,
        not based on game results. This function is kept for compatibility but
        no longer performs elimination logic.
        """
        try:
            # Eliminations are now handled in the pick creation process
            # based on user choices, not game results
            logger.info(f"Team eliminations are handled during pick creation for Week {week}")
            
        except sqlite3.Error as e:
            logger.error(f"Database error in update_team_eliminations for Week {week}: {e}")
            conn.rollback()
    
    def find_matching_game(self, conn: sqlite3.Connection, espn_game: Dict, week: int) -> Optional[int]:
        """Find matching game in database based on ESPN data"""
        try:
            cursor = conn.cursor()
            
            # Safely extract team names with fallback
            home_team = espn_game.get('home_team')
            away_team = espn_game.get('away_team')
            
            if not home_team or not away_team:
                logger.warning(f"Missing team names in ESPN data: home={home_team}, away={away_team}")
                return None
            
            # Try exact match first
            cursor.execute("""
                SELECT m.id FROM match m
                JOIN team ht ON m.home_team_id = ht.id
                JOIN team at ON m.away_team_id = at.id
                WHERE m.week = ? AND ht.name = ? AND at.name = ?
            """, (week, home_team, away_team))
            
            result = cursor.fetchone()
            if result:
                return result['id']
            
            # Try fuzzy matching (in case team names differ slightly)
            cursor.execute("""
                SELECT m.id, ht.name as home_team, at.name as away_team FROM match m
                JOIN team ht ON m.home_team_id = ht.id
                JOIN team at ON m.away_team_id = at.id
                WHERE m.week = ? AND m.is_completed = 0
            """, (week,))
            
            matches = cursor.fetchall()
            
            for match in matches:
                # Check if team names contain each other (fuzzy match)
                if (home_team in match['home_team'] or match['home_team'] in home_team) and \
                   (away_team in match['away_team'] or match['away_team'] in away_team):
                    logger.info(f"Fuzzy matched: {home_team} vs {away_team} -> {match['home_team']} vs {match['away_team']}")
                    return match['id']
            
            logger.warning(f"No matching game found for {away_team} @ {home_team} in Week {week}")
            return None
            
        except sqlite3.Error as e:
            logger.error(f"Database error finding matching game: {e}")
            return None
    
    def validate_week(self, week: int, year: int = 2025) -> bool:
        """Validate all games for a specific week"""
        logger.info(f"Starting validation for Week {week}")
        
        # Get ESPN data
        espn_data = self.get_espn_scoreboard(week, year)
        if not espn_data:
            logger.error(f"Failed to get ESPN data for Week {week}")
            return False
        
        # Connect to database
        conn = self.get_database_connection()
        
        try:
            games = espn_data.get('events', [])
            updated_count = 0
            
            for game in games:
                # Parse game result
                result_data = self.parse_espn_game_result(game)
                if not result_data:
                    continue  # Game not completed yet
                
                # Find matching game in database
                match_id = self.find_matching_game(conn, result_data, week)
                if not match_id:
                    continue
                
                # Look up winner team ID
                cursor = conn.cursor()
                winner_name = result_data.get('winner_name')
                if not winner_name:
                    logger.warning("Missing winner_name in result data")
                    continue
                    
                cursor.execute("SELECT id FROM team WHERE name = ?", (winner_name,))
                winner_team = cursor.fetchone()
                if winner_team:
                    result_data['winner_team_id'] = winner_team['id']
                else:
                    logger.warning(f"Could not find team ID for winner: {winner_name}")
                    continue
                
                # Update game result
                if self.update_game_result(conn, match_id, result_data):
                    updated_count += 1
            
            if updated_count > 0:
                # Calculate points and update eliminations
                self.calculate_user_points(conn, week)
                self.update_team_eliminations(conn, week)
                
                logger.info(f"Successfully validated Week {week}: {updated_count} games updated")
            else:
                logger.info(f"No new completed games found for Week {week}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating Week {week}: {e}")
            return False
        finally:
            conn.close()
    
    def validate_current_week(self) -> bool:
        """Validate the current NFL week"""
        # Determine current week based on date
        current_date = datetime.now()
        
        # NFL season starts September 4, 2025 (Week 1)
        season_start = datetime(2025, 9, 4)
        
        if current_date < season_start:
            logger.info("NFL season hasn't started yet")
            return True
        
        # Calculate current week (rough estimation)
        days_since_start = (current_date - season_start).days
        current_week = min(18, max(1, (days_since_start // 7) + 1))
        
        logger.info(f"Validating current week: {current_week}")
        return self.validate_week(current_week)
    
    def validate_all_incomplete_weeks(self) -> bool:
        """Validate all weeks that have incomplete games"""
        conn = self.get_database_connection()
        
        try:
            cursor = conn.cursor()
            
            # Get all weeks with incomplete games
            cursor.execute("""
                SELECT DISTINCT week 
                FROM match 
                WHERE completed = 0 AND week <= 18
                ORDER BY week
            """)
            
            incomplete_weeks = cursor.fetchall()
            
            success = True
            for week_row in incomplete_weeks:
                week = week_row['week']
                if not self.validate_week(week):
                    success = False
            
            return success
            
        except sqlite3.Error as e:
            logger.error(f"Database error getting incomplete weeks: {e}")
            return False
        finally:
            conn.close()

# Scheduler functions
def run_validation_service():
    """Run the validation service with scheduled tasks"""
    try:
        validator = NFLGameValidator()
        
        # Schedule validation tasks
        schedule.every(30).minutes.do(validator.validate_current_week)  # Every 30 minutes during games
        schedule.every().day.at("00:00").do(validator.validate_all_incomplete_weeks)  # Daily at midnight
        schedule.every().tuesday.at("06:00").do(validator.validate_all_incomplete_weeks)  # Tuesday 6 AM (after MNF)
        
        logger.info("NFL Game Validator Service started")
        logger.info("Scheduled tasks:")
        logger.info("- Every 30 minutes: Validate current week")
        logger.info("- Daily at midnight: Validate all incomplete weeks")
        logger.info("- Tuesday 6 AM: Final weekly validation")
        
        # Run initial validation
        try:
            validator.validate_current_week()
        except Exception as e:
            logger.error(f"Error in initial validation: {e}")
        
        # Keep the service running
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in validation service loop: {e}")
                time.sleep(60)  # Continue running even if there's an error
                
    except Exception as e:
        logger.error(f"Fatal error in validation service: {e}")
        raise

def start_validation_service_thread():
    """Start the validation service in a background thread"""
    try:
        thread = threading.Thread(target=run_validation_service, daemon=True)
        thread.start()
        logger.info("Validation service thread started")
        return thread
    except Exception as e:
        logger.error(f"Failed to start validation service thread: {e}")
        return None

if __name__ == "__main__":
    # Run as standalone service
    run_validation_service()


    def update_weekly_schedule(self) -> bool:
        """Update NFL schedule with next week's games from NFL Operations"""
        logger.info("Starting weekly schedule update...")
        
        try:
            # Import the schedule update functionality
            import sys
            # Use relative path for Render compatibility
            current_dir = os.path.dirname(os.path.abspath(__file__))
            sys.path.insert(0, current_dir)
            from app import app, db, Match, Team
            
            with app.app_context():
                # Determine which week to add next
                latest_week = db.session.query(db.func.max(Match.week)).scalar() or 0
                next_week = latest_week + 1
                
                if next_week > 18:
                    logger.info("All 18 weeks already in database")
                    return True
                
                logger.info(f"Adding Week {next_week} schedule...")
                
                # Here you would scrape NFL Operations website for the next week
                # For now, we'll use a simplified approach
                
                # Get all teams for creating template matches
                teams = Team.query.all()
                if len(teams) < 32:
                    logger.error("Not enough teams in database")
                    return False
                
                # Create template matches for the next week
                # In a real implementation, this would scrape operations.nfl.com
                # for the actual matchups
                
                added_count = 0
                
                # Create 16 template matches (typical NFL week)
                for i in range(0, min(32, len(teams)), 2):
                    if i + 1 < len(teams):
                        # Rotate teams to create different matchups
                        home_idx = (i + next_week) % len(teams)
                        away_idx = (i + 1 + next_week) % len(teams)
                        
                        if home_idx != away_idx:
                            home_team = teams[home_idx]
                            away_team = teams[away_idx]
                            
                            # Check if this matchup already exists
                            existing = Match.query.filter_by(
                                week=next_week,
                                home_team_id=home_team.id,
                                away_team_id=away_team.id
                            ).first()
                            
                            if not existing:
                                new_match = Match(
                                    week=next_week,
                                    home_team_id=home_team.id,
                                    away_team_id=away_team.id,
                                    is_completed=False,
                                    start_time=None  # Will be updated when real schedule is available
                                )
                                
                                db.session.add(new_match)
                                added_count += 1
                                
                                if added_count >= 16:  # Typical NFL week
                                    break
                
                db.session.commit()
                logger.info(f"Added {added_count} template matches for Week {next_week}")
                
                # TODO: Implement actual NFL Operations scraping here
                # This would replace the template creation above with real matchups
                
                return True
                
        except Exception as e:
            logger.error(f"Error updating weekly schedule: {e}")
            return False
    
    def scrape_nfl_operations_schedule(self, week: int) -> List[Dict]:
        """Scrape NFL Operations website for real schedule data"""
        # TODO: Implement actual scraping of operations.nfl.com
        # This is a placeholder for the real implementation
        
        try:
            import requests
            from bs4 import BeautifulSoup
            
            url = f"https://operations.nfl.com/gameday/nfl-schedule/2025-nfl-schedule/"
            
            # Note: This would need to be implemented properly
            # to parse the actual NFL Operations website
            
            logger.info(f"Would scrape NFL Operations for Week {week}")
            return []
            
        except Exception as e:
            logger.error(f"Error scraping NFL Operations: {e}")
            return []

class NFLGameValidatorService:
    """Service wrapper for the NFL Game Validator"""
    
    def __init__(self):
        self.validator = NFLGameValidator()
        self.logger = logging.getLogger(__name__)
        
    def start_validation_service(self):
        """Start the background validation service"""
        def run_validation():
            while True:
                try:
                    current_time = datetime.now()
                    current_hour = current_time.hour
                    current_minute = current_time.minute
                    current_weekday = current_time.weekday()  # 0=Monday, 6=Sunday
                    
                    # Every 30 minutes during game days (Friday-Tuesday)
                    if current_weekday in [4, 5, 6, 0, 1] and current_minute % 30 == 0:
                        self.validator.validate_current_week()
                    
                    # Daily at midnight - validate all incomplete weeks
                    elif current_hour == 0 and current_minute == 0:
                        self.validator.validate_all_incomplete_weeks()
                    
                    # Tuesday at 6 AM - final weekly validation (after Monday Night Football)
                    elif current_weekday == 1 and current_hour == 6 and current_minute == 0:
                        self.validator.validate_all_incomplete_weeks()
                    
                    # Tuesday at 7 AM - weekly schedule update
                    elif current_weekday == 1 and current_hour == 7 and current_minute == 0:
                        self.validator.update_weekly_schedule()
                    
                    time.sleep(60)  # Check every minute
                    
                except Exception as e:
                    self.logger.error(f"Error in validation service: {e}")
                    time.sleep(300)  # Wait 5 minutes on error
        
        validation_thread = threading.Thread(target=run_validation, daemon=True)
        validation_thread.start()
        self.logger.info("Validation service thread started")
        
        # Log scheduled tasks
        self.logger.info("Scheduled tasks:")
        self.logger.info("- Every 30 minutes: Validate current week")
        self.logger.info("- Daily at midnight: Validate all incomplete weeks")
        self.logger.info("- Tuesday 6 AM: Final weekly validation (after Monday Night Football)")
        self.logger.info("- Tuesday 7 AM: Weekly schedule update")

# Global service instance
validation_service = NFLGameValidatorService()

def start_validation_service():
    """Start the global validation service"""
    validation_service.start_validation_service()
    return validation_service

