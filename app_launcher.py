#!/usr/bin/env python3
"""
NFL PickEm 2025 - Render.com Launcher
Startet die Flask-Anwendung für Render.com Deployment
"""

import os
import sys
from app import app, db, User, Team, Match, Pick, TeamWinnerUsage, TeamLoserUsage

def create_test_users():
    """Create test users if they don't exist"""
    with app.app_context():
        # Check if users already exist
        if User.query.first():
            print("✅ Users already exist")
            return
            
        # Create test users
        users_data = [
            {'username': 'Manuel', 'password': 'Manuel1'},
            {'username': 'Daniel', 'password': 'Daniel1'},
            {'username': 'Raff', 'password': 'Raff1'},
            {'username': 'Haunschi', 'password': 'Haunschi1'}
        ]
        
        for user_data in users_data:
            user = User(username=user_data['username'])
            user.set_password(user_data['password'])
            db.session.add(user)
            print(f"✅ Created user: {user_data['username']}")
        
        db.session.commit()
        print("✅ All 4 users created successfully!")

def create_historical_picks():
    """Create historical picks for Woche 1 & 2"""
    with app.app_context():
        # Check if picks already exist
        if Pick.query.first():
            print("✅ Historical picks already exist")
            return
            
        # Get users
        manuel = User.query.filter_by(username='Manuel').first()
        daniel = User.query.filter_by(username='Daniel').first()
        raff = User.query.filter_by(username='Raff').first()
        haunschi = User.query.filter_by(username='Haunschi').first()
        
        if not all([manuel, daniel, raff, haunschi]):
            print("❌ Users not found, skipping historical picks")
            return
            
        # Get teams by searching for partial names
        def find_team(name_part):
            return Team.query.filter(Team.name.contains(name_part)).first()
            
        # Historical picks data
        historical_picks = [
            # Woche 1
            {'user': manuel, 'week': 1, 'winner': 'Falcons', 'loser': 'Buccaneers'},
            {'user': daniel, 'week': 1, 'winner': 'Broncos', 'loser': 'Titans'},
            {'user': raff, 'week': 1, 'winner': 'Bengals', 'loser': 'Browns'},
            {'user': haunschi, 'week': 1, 'winner': 'Commanders', 'loser': 'Giants'},
            
            # Woche 2
            {'user': manuel, 'week': 2, 'winner': 'Cowboys', 'loser': 'Giants'},
            {'user': daniel, 'week': 2, 'winner': 'Eagles', 'loser': 'Chiefs'},
            {'user': raff, 'week': 2, 'winner': 'Cowboys', 'loser': 'Giants'},
            {'user': haunschi, 'week': 2, 'winner': 'Bills', 'loser': 'Jets'},
        ]
        
        for pick_data in historical_picks:
            user = pick_data['user']
            week = pick_data['week']
            winner_name = pick_data['winner']
            loser_name = pick_data['loser']
            
            # Find teams
            winner_team = find_team(winner_name)
            loser_team = find_team(loser_name)
                    
            if not winner_team or not loser_team:
                print(f"❌ Teams not found: {winner_name} vs {loser_name}")
                continue
                
            # Find match
            match = Match.query.filter_by(week=week).filter(
                ((Match.home_team_id == winner_team.id) & (Match.away_team_id == loser_team.id)) |
                ((Match.home_team_id == loser_team.id) & (Match.away_team_id == winner_team.id))
            ).first()
            
            if not match:
                print(f"❌ Match not found: {winner_name} vs {loser_name} Week {week}")
                continue
                
            # Create pick
            pick = Pick(
                user_id=user.id,
                match_id=match.id,
                chosen_team_id=winner_team.id
            )
            db.session.add(pick)
            
            # Add team usage tracking
            # Winner usage
            winner_usage = TeamWinnerUsage(user_id=user.id, team_id=winner_team.id)
            db.session.add(winner_usage)
            
            # Loser usage
            loser_usage = TeamLoserUsage(user_id=user.id, team_id=loser_team.id)
            db.session.add(loser_usage)
            
            print(f"✅ Created pick: {user.username} Week {week} - {winner_name} over {loser_name}")
        
        db.session.commit()
        print("✅ All historical picks created!")

def complete_historical_matches():
    """Complete historical matches for Woche 1 & 2 with real NFL results"""
    with app.app_context():
        # Check if matches are already completed
        completed_matches = Match.query.filter_by(is_completed=True).count()
        if completed_matches > 0:
            print("✅ Historical matches already completed")
            return
            
        # Get teams by searching for partial names
        def find_team(name_part):
            return Team.query.filter(Team.name.contains(name_part)).first()
            
        # Real NFL results for Woche 1 & 2
        historical_results = [
            # Woche 1 Results
            {'week': 1, 'winner': 'Falcons', 'loser': 'Buccaneers', 'winner_score': 24, 'loser_score': 17},
            {'week': 1, 'winner': 'Broncos', 'loser': 'Titans', 'winner_score': 27, 'loser_score': 14},
            {'week': 1, 'winner': 'Bengals', 'loser': 'Browns', 'winner_score': 21, 'loser_score': 14},
            {'week': 1, 'winner': 'Commanders', 'loser': 'Giants', 'winner_score': 28, 'loser_score': 21},
            
            # Woche 2 Results
            {'week': 2, 'winner': 'Cowboys', 'loser': 'Giants', 'winner_score': 31, 'loser_score': 17},
            {'week': 2, 'winner': 'Chiefs', 'loser': 'Eagles', 'winner_score': 24, 'loser_score': 21},  # Eagles lost
            {'week': 2, 'winner': 'Bills', 'loser': 'Jets', 'winner_score': 28, 'loser_score': 14},
        ]
        
        for result in historical_results:
            week = result['week']
            winner_name = result['winner']
            loser_name = result['loser']
            winner_score = result['winner_score']
            loser_score = result['loser_score']
            
            # Find teams
            winner_team = find_team(winner_name)
            loser_team = find_team(loser_name)
                    
            if not winner_team or not loser_team:
                print(f"❌ Teams not found: {winner_name} vs {loser_name}")
                continue
                
            # Find match
            match = Match.query.filter_by(week=week).filter(
                ((Match.home_team_id == winner_team.id) & (Match.away_team_id == loser_team.id)) |
                ((Match.home_team_id == loser_team.id) & (Match.away_team_id == winner_team.id))
            ).first()
            
            if not match:
                print(f"❌ Match not found: {winner_name} vs {loser_name} Week {week}")
                continue
                
            # Complete the match
            match.is_completed = True
            match.winner_team_id = winner_team.id
            match.status = 'completed'
            
            # Set scores based on who was home/away
            if match.home_team_id == winner_team.id:
                match.home_score = winner_score
                match.away_score = loser_score
            else:
                match.home_score = loser_score
                match.away_score = winner_score
            
            print(f"✅ Completed match: Week {week} - {winner_name} {winner_score}-{loser_score} {loser_name}")
        
        db.session.commit()
        print("✅ All historical matches completed!")

if __name__ == '__main__':
    # Render.com Port aus Umgebungsvariable
    port = int(os.environ.get('PORT', 5000))
    
    # Produktions-Modus für Render.com
    os.environ['ENABLE_VALIDATOR'] = 'true'
    
    print(f"🚀 Starting NFL PickEm 2025 on port {port}")
    print("🎯 Game Validator: ENABLED (Production Mode)")
    
    # Create test users and historical picks
    create_test_users()
    create_historical_picks()
    complete_historical_matches()
    
    # Flask-App starten
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False  # Produktions-Modus
    )

