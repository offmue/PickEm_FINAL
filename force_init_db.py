#!/usr/bin/env python3
"""
Force database initialization with correct timezone data
"""

import os
import sys
import logging
from datetime import datetime, timezone
import pytz

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import from the main app
from app_login_protected import app, db, Team, User, Match, create_nfl_teams, create_test_users, create_week3_games

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def force_initialize_database():
    """Force initialize database with fresh data"""
    logger.info("🔧 Force initializing database...")
    
    with app.app_context():
        # Drop all tables
        db.drop_all()
        logger.info("🗑️ Dropped all tables")
        
        # Create all tables
        db.create_all()
        logger.info("📋 Created all tables")
        
        # Create NFL teams
        teams_created = create_nfl_teams()
        logger.info(f"🏈 Created {teams_created} NFL teams")
        
        # Create test users
        users_created = create_test_users()
        logger.info(f"👥 Created {users_created} test users")
        
        # Create Week 3 games
        games_created = create_week3_games()
        logger.info(f"🎮 Created {games_created} Week 3 games")
        
        logger.info("✅ Force database initialization completed")

if __name__ == '__main__':
    force_initialize_database()

