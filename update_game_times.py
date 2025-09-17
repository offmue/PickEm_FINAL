#!/usr/bin/env python3
"""
Update game times to future dates for testing pick functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app_final_working import app, db, Match
from datetime import datetime, timezone, timedelta

def update_game_times():
    """Update all Week 3 games to future times for testing"""
    with app.app_context():
        print("🔧 Updating game times to future dates...")
        
        # Get all Week 3 matches
        week3_matches = Match.query.filter_by(week=3).all()
        print(f"Found {len(week3_matches)} Week 3 matches")
        
        # Set new start times (tomorrow at various hours)
        tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
        base_time = tomorrow.replace(hour=19, minute=0, second=0, microsecond=0)  # 7 PM tomorrow
        
        for i, match in enumerate(week3_matches):
            # Spread games across different times
            new_time = base_time + timedelta(hours=i * 3)  # Every 3 hours
            
            print(f"Updating Match {match.id}: {match.away_team.name} @ {match.home_team.name}")
            print(f"  Old time: {match.start_time}")
            print(f"  New time: {new_time}")
            
            match.start_time = new_time
        
        # Commit changes
        db.session.commit()
        print("✅ All game times updated successfully!")
        
        # Verify updates
        print("\n📅 Updated game schedule:")
        for match in week3_matches:
            vienna_time = match.start_time.astimezone(timezone.utc).replace(tzinfo=None) + timedelta(hours=2)  # Vienna is UTC+2
            print(f"  Match {match.id}: {match.away_team.name} @ {match.home_team.name} - {vienna_time.strftime('%d.%m., %H:%M')} Vienna")

if __name__ == '__main__':
    update_game_times()

