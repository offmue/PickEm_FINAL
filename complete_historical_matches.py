#!/usr/bin/env python3
"""
Complete historical matches for Woche 1 & 2 with real NFL results
"""

from app import app, db, Team, Match
from datetime import datetime

def complete_historical_matches():
    with app.app_context():
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
            match.updated_at = datetime.utcnow()
            
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
    complete_historical_matches()

