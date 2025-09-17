#!/usr/bin/env python3
"""
Create historical picks for Woche 1 & 2
"""

from app import app, db, User, Team, Match, Pick, TeamWinnerUsage, TeamLoserUsage
from datetime import datetime

def create_historical_picks():
    with app.app_context():
        # Check if picks already exist
        if Pick.query.first():
            print("✅ Picks already exist")
            return
            
        # Get users
        manuel = User.query.filter_by(username='Manuel').first()
        daniel = User.query.filter_by(username='Daniel').first()
        raff = User.query.filter_by(username='Raff').first()
        haunschi = User.query.filter_by(username='Haunschi').first()
        
        if not all([manuel, daniel, raff, haunschi]):
            print("❌ Users not found, create users first")
            return
            
        # Get teams
        teams = {team.name: team for team in Team.query.all()}
        
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
            winner_team = None
            loser_team = None
            
            for team_name, team in teams.items():
                if winner_name in team_name:
                    winner_team = team
                if loser_name in team_name:
                    loser_team = team
                    
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

if __name__ == '__main__':
    create_historical_picks()

