#!/usr/bin/env python3
"""
Create historical data for NFL PickEm - Weeks 1 and 2 with real picks and results
"""

import os
import sys
import logging
from datetime import datetime, timezone

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import from the main app
from app_login_protected import app, db, Team, User, Match, Pick

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_historical_games():
    """Create historical games for weeks 1 and 2"""
    
    # Week 1 games (completed)
    week1_games = [
        # Manuel's pick: Falcons W vs Buccaneers L
        {'away': 'TB', 'home': 'ATL', 'time': '2025-09-03T17:00:00', 'home_score': 24, 'away_score': 17, 'winner': 'ATL'},
        # Daniel's pick: Broncos W vs Titans L  
        {'away': 'TEN', 'home': 'DEN', 'time': '2025-09-03T20:00:00', 'home_score': 28, 'away_score': 14, 'winner': 'DEN'},
        # Raff's pick: Bengals W vs Browns L
        {'away': 'CLE', 'home': 'CIN', 'time': '2025-09-03T17:00:00', 'home_score': 21, 'away_score': 10, 'winner': 'CIN'},
        # Haunschi's pick: Commanders W vs Giants L
        {'away': 'NYG', 'home': 'WAS', 'time': '2025-09-03T17:00:00', 'home_score': 31, 'away_score': 14, 'winner': 'WAS'},
    ]
    
    # Week 2 games (completed)
    week2_games = [
        # Manuel & Raff's pick: Cowboys W vs Giants L
        {'away': 'NYG', 'home': 'DAL', 'time': '2025-09-10T20:00:00', 'home_score': 35, 'away_score': 17, 'winner': 'DAL'},
        # Daniel's pick: Eagles W vs Chiefs L
        {'away': 'KC', 'home': 'PHI', 'time': '2025-09-10T00:00:00', 'home_score': 28, 'away_score': 21, 'winner': 'PHI'},
        # Haunschi's pick: Bills W vs Jets L
        {'away': 'NYJ', 'home': 'BUF', 'time': '2025-09-10T17:00:00', 'home_score': 24, 'away_score': 10, 'winner': 'BUF'},
    ]
    
    games_created = 0
    
    # Create Week 1 games
    for week, games in [(1, week1_games), (2, week2_games)]:
        for game in games:
            # Get teams
            away_team = Team.query.filter_by(abbreviation=game['away']).first()
            home_team = Team.query.filter_by(abbreviation=game['home']).first()
            winner_team = Team.query.filter_by(abbreviation=game['winner']).first()
            
            if away_team and home_team and winner_team:
                # Check if game already exists
                existing_game = Match.query.filter_by(
                    week=week,
                    home_team_id=home_team.id,
                    away_team_id=away_team.id
                ).first()
                
                if not existing_game:
                    # Create new game
                    new_game = Match(
                        week=week,
                        home_team_id=home_team.id,
                        away_team_id=away_team.id,
                        start_time=datetime.fromisoformat(game['time']).replace(tzinfo=timezone.utc),
                        home_score=game['home_score'],
                        away_score=game['away_score'],
                        winner_team_id=winner_team.id,
                        is_completed=True
                    )
                    
                    db.session.add(new_game)
                    games_created += 1
                    logger.info(f"✅ Created Week {week} game: {away_team.name} @ {home_team.name} ({game['home_score']}-{game['away_score']})")
    
    db.session.commit()
    return games_created

def create_historical_picks():
    """Create historical picks for all users"""
    
    # Historical picks data
    historical_picks = [
        # Week 1
        {'username': 'Manuel', 'week': 1, 'away': 'TB', 'home': 'ATL', 'chosen': 'ATL'},  # Falcons W
        {'username': 'Daniel', 'week': 1, 'away': 'TEN', 'home': 'DEN', 'chosen': 'DEN'},  # Broncos W
        {'username': 'Raff', 'week': 1, 'away': 'CLE', 'home': 'CIN', 'chosen': 'CIN'},    # Bengals W
        {'username': 'Haunschi', 'week': 1, 'away': 'NYG', 'home': 'WAS', 'chosen': 'WAS'}, # Commanders W
        
        # Week 2
        {'username': 'Manuel', 'week': 2, 'away': 'NYG', 'home': 'DAL', 'chosen': 'DAL'},  # Cowboys W
        {'username': 'Daniel', 'week': 2, 'away': 'KC', 'home': 'PHI', 'chosen': 'PHI'},   # Eagles W
        {'username': 'Raff', 'week': 2, 'away': 'NYG', 'home': 'DAL', 'chosen': 'DAL'},    # Cowboys W
        {'username': 'Haunschi', 'week': 2, 'away': 'NYJ', 'home': 'BUF', 'chosen': 'BUF'}, # Bills W
    ]
    
    picks_created = 0
    
    for pick_data in historical_picks:
        # Get user
        user = User.query.filter_by(username=pick_data['username']).first()
        if not user:
            logger.warning(f"❌ User {pick_data['username']} not found")
            continue
            
        # Get teams
        away_team = Team.query.filter_by(abbreviation=pick_data['away']).first()
        home_team = Team.query.filter_by(abbreviation=pick_data['home']).first()
        chosen_team = Team.query.filter_by(abbreviation=pick_data['chosen']).first()
        
        if not (away_team and home_team and chosen_team):
            logger.warning(f"❌ Teams not found for pick: {pick_data}")
            continue
            
        # Get match
        match = Match.query.filter_by(
            week=pick_data['week'],
            home_team_id=home_team.id,
            away_team_id=away_team.id
        ).first()
        
        if not match:
            logger.warning(f"❌ Match not found for pick: {pick_data}")
            continue
            
        # Check if pick already exists
        existing_pick = Pick.query.filter_by(
            user_id=user.id,
            match_id=match.id
        ).first()
        
        if not existing_pick:
            # Create new pick
            new_pick = Pick(
                user_id=user.id,
                match_id=match.id,
                chosen_team_id=chosen_team.id,
                created_at=datetime.utcnow()
            )
            
            db.session.add(new_pick)
            picks_created += 1
            
            # Check if pick was correct
            is_correct = (chosen_team.id == match.winner_team_id)
            result = "✅ CORRECT" if is_correct else "❌ WRONG"
            logger.info(f"Created pick: {user.username} W{pick_data['week']} chose {chosen_team.name} {result}")
    
    db.session.commit()
    return picks_created

def main():
    """Main function to create all historical data"""
    logger.info("🏈 Creating historical NFL PickEm data...")
    
    with app.app_context():
        # Create historical games
        games_created = create_historical_games()
        logger.info(f"✅ Created {games_created} historical games")
        
        # Create historical picks
        picks_created = create_historical_picks()
        logger.info(f"✅ Created {picks_created} historical picks")
        
        logger.info("🎉 Historical data creation completed!")

if __name__ == '__main__':
    main()

