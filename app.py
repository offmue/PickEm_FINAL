"""
NFL PickEm 2025 - Main Application with ESPN Integration
Complete NFL Pick'em game with real ESPN data
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
import pytz
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'nfl-pickem-2025-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///nfl_pickem.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_score(self):
        """Calculate user's total score"""
        total_points = 0
        picks = Pick.query.filter_by(user_id=self.id).all()
        
        for pick in picks:
            match = pick.match
            if match.is_completed and match.winner_team_id:
                if pick.chosen_team_id == match.winner_team_id:
                    total_points += 1
        
        return total_points

class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    abbreviation = db.Column(db.String(10), unique=True, nullable=False)
    logo_url = db.Column(db.String(200))

class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    week = db.Column(db.Integer, nullable=False)
    home_team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    away_team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    start_time = db.Column(db.DateTime(timezone=True))
    is_completed = db.Column(db.Boolean, default=False)
    winner_team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    home_score = db.Column(db.Integer, default=0)
    away_score = db.Column(db.Integer, default=0)
    
    home_team = db.relationship('Team', foreign_keys=[home_team_id], backref='home_matches')
    away_team = db.relationship('Team', foreign_keys=[away_team_id], backref='away_matches')
    winner_team = db.relationship('Team', foreign_keys=[winner_team_id])

class Pick(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    match_id = db.Column(db.Integer, db.ForeignKey('match.id'), nullable=False)
    chosen_team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    
    user = db.relationship('User', backref='picks')
    match = db.relationship('Match', backref='picks')
    chosen_team = db.relationship('Team')

class TeamWinnerUsage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    
    user = db.relationship('User')
    team = db.relationship('Team')

class TeamLoserUsage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    
    user = db.relationship('User')
    team = db.relationship('Team')

# Import ESPN modules
from espn_data_sync import ESPNDataSync
from espn_points_calculator import ESPNPointsCalculator
from espn_scheduler import ESPNScheduler

# Initialize ESPN components
espn_sync = None
points_calculator = None
espn_scheduler = None

def initialize_espn_components():
    """Initialize ESPN components after app context is available"""
    global espn_sync, points_calculator, espn_scheduler
    
    try:
        logger.info("🔧 Initializing ESPN components...")
        
        espn_sync = ESPNDataSync(app, db)
        points_calculator = ESPNPointsCalculator(app, db)
        espn_scheduler = ESPNScheduler(app, espn_sync, points_calculator)
        
        logger.info("✅ ESPN components initialized")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error initializing ESPN components: {e}")
        return False

def initialize_database():
    """Initialize database with real NFL data from ESPN"""
    try:
        logger.info("🔧 Initializing database with ESPN NFL data...")
        
        # Create all tables
        db.create_all()
        
        # Initialize ESPN components
        if not initialize_espn_components():
            logger.error("❌ Failed to initialize ESPN components")
            return False
        
        # Create test users
        create_test_users()
        
        # Perform full ESPN data sync
        logger.info("🔄 Performing full ESPN data sync...")
        if espn_sync.full_sync():
            logger.info("✅ ESPN data sync completed")
        else:
            logger.warning("⚠️ ESPN data sync failed, using fallback")
        
        # Create historical picks
        create_historical_picks()
        
        # Validate completed games and calculate points
        points_calculator.validate_completed_games()
        
        # Start scheduler
        espn_scheduler.start_scheduler()
        
        logger.info("✅ Database initialization completed with ESPN NFL data")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error initializing database: {e}")
        return False

def create_test_users():
    """Create test users"""
    try:
        test_users = [
            {'username': 'Manuel', 'password': 'Manuel1'},
            {'username': 'Daniel', 'password': 'Daniel1'},
            {'username': 'Raff', 'password': 'Raff1'},
            {'username': 'Haunschi', 'password': 'Haunschi1'}
        ]
        
        for user_data in test_users:
            existing_user = User.query.filter_by(username=user_data['username']).first()
            if not existing_user:
                user = User(username=user_data['username'])
                user.set_password(user_data['password'])
                db.session.add(user)
        
        db.session.commit()
        logger.info("✅ Test users created")
        
    except Exception as e:
        logger.error(f"❌ Error creating test users: {e}")

def create_historical_picks():
    """Create historical picks for test users"""
    try:
        logger.info("🔄 Creating historical picks...")
        
        # Historical picks data
        historical_picks = [
            # Week 1
            {'username': 'Manuel', 'week': 1, 'winner': 'ATL', 'loser': 'TB'},
            {'username': 'Daniel', 'week': 1, 'winner': 'DEN', 'loser': 'TEN'},
            {'username': 'Raff', 'week': 1, 'winner': 'CIN', 'loser': 'CLE'},
            {'username': 'Haunschi', 'week': 1, 'winner': 'WAS', 'loser': 'NYG'},
            # Week 2
            {'username': 'Manuel', 'week': 2, 'winner': 'DAL', 'loser': 'NYG'},
            {'username': 'Daniel', 'week': 2, 'winner': 'PHI', 'loser': 'KC'},
            {'username': 'Raff', 'week': 2, 'winner': 'DAL', 'loser': 'NYG'},
            {'username': 'Haunschi', 'week': 2, 'winner': 'BUF', 'loser': 'NYJ'}
        ]
        
        for pick_data in historical_picks:
            user = User.query.filter_by(username=pick_data['username']).first()
            if not user:
                continue
            
            # Find the match
            winner_team = Team.query.filter_by(abbreviation=pick_data['winner']).first()
            loser_team = Team.query.filter_by(abbreviation=pick_data['loser']).first()
            
            if not winner_team or not loser_team:
                continue
            
            # Find match where these teams played
            match = Match.query.filter_by(week=pick_data['week']).filter(
                ((Match.home_team_id == winner_team.id) & (Match.away_team_id == loser_team.id)) |
                ((Match.home_team_id == loser_team.id) & (Match.away_team_id == winner_team.id))
            ).first()
            
            if match:
                # Check if pick already exists
                existing_pick = Pick.query.filter_by(user_id=user.id, match_id=match.id).first()
                if not existing_pick:
                    pick = Pick(
                        user_id=user.id,
                        match_id=match.id,
                        chosen_team_id=winner_team.id
                    )
                    db.session.add(pick)
        
        db.session.commit()
        logger.info("✅ Historical picks created")
        
    except Exception as e:
        logger.error(f"❌ Error creating historical picks: {e}")

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            return jsonify({'success': True, 'username': user.username})
        else:
            return jsonify({'success': False, 'message': 'Invalid credentials'})
            
    except Exception as e:
        logger.error(f"❌ Login error: {e}")
        return jsonify({'success': False, 'message': 'Login failed'})

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/api/auth/check', methods=['GET'])
def check_session():
    if 'user_id' in session:
        return jsonify({'logged_in': True, 'username': session['username']})
    else:
        return jsonify({'logged_in': False})

@app.route('/api/current-week')
def get_current_week():
    try:
        if espn_sync:
            current_week = espn_sync.get_current_week()
        else:
            current_week = 3  # Fallback
        
        return jsonify({'success': True, 'current_week': current_week})
    except Exception as e:
        logger.error(f"❌ Error getting current week: {e}")
        return jsonify({'success': False, 'current_week': 3})

@app.route('/api/matches/<int:week>')
def get_matches(week):
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Not logged in'})
        
        user_id = session['user_id']
        
        # Get matches for the week
        matches = Match.query.filter_by(week=week).all()
        
        # Get user's pick for this week
        user_pick = None
        if matches:
            for match in matches:
                pick = Pick.query.filter_by(user_id=user_id, match_id=match.id).first()
                if pick:
                    user_pick = {
                        'match_id': match.id,
                        'chosen_team_id': pick.chosen_team_id
                    }
                    break
        
        # Format matches
        matches_data = []
        for match in matches:
            # Check if game has started
            now = datetime.now(timezone.utc)
            has_started = match.start_time and match.start_time <= now
            
            matches_data.append({
                'id': match.id,
                'week': match.week,
                'home_team': {
                    'id': match.home_team.id,
                    'name': match.home_team.name,
                    'abbreviation': match.home_team.abbreviation,
                    'logo_url': match.home_team.logo_url
                },
                'away_team': {
                    'id': match.away_team.id,
                    'name': match.away_team.name,
                    'abbreviation': match.away_team.abbreviation,
                    'logo_url': match.away_team.logo_url
                },
                'start_time': match.start_time.isoformat() if match.start_time else None,
                'is_completed': match.is_completed,
                'has_started': has_started,
                'home_score': match.home_score,
                'away_score': match.away_score,
                'winner_team_id': match.winner_team_id
            })
        
        return jsonify({
            'success': True,
            'matches': matches_data,
            'user_pick': user_pick
        })
        
    except Exception as e:
        logger.error(f"❌ Error getting matches: {e}")
        return jsonify({'success': False, 'matches': [], 'user_pick': None})

@app.route('/api/picks/create', methods=['POST'])
def create_pick():
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Not logged in'})
        
        data = request.get_json()
        user_id = session['user_id']
        match_id = data.get('match_id')
        chosen_team_id = data.get('chosen_team_id')
        
        # Validate match exists
        match = Match.query.get(match_id)
        if not match:
            return jsonify({'success': False, 'message': 'Match not found'})
        
        # Check if game has started
        now = datetime.now(timezone.utc)
        if match.start_time and match.start_time <= now:
            return jsonify({'success': False, 'message': 'Game has already started'})
        
        # Check if user already has a pick for this week
        existing_picks = Pick.query.join(Match).filter(
            Pick.user_id == user_id,
            Match.week == match.week
        ).all()
        
        # Remove existing picks for this week
        for pick in existing_picks:
            db.session.delete(pick)
        
        # Create new pick
        pick = Pick(
            user_id=user_id,
            match_id=match_id,
            chosen_team_id=chosen_team_id
        )
        db.session.add(pick)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Pick saved successfully'})
        
    except Exception as e:
        logger.error(f"❌ Error creating pick: {e}")
        return jsonify({'success': False, 'message': 'Failed to save pick'})

@app.route('/api/leaderboard')
def get_leaderboard():
    try:
        if points_calculator:
            leaderboard = points_calculator.get_leaderboard()
        else:
            # Fallback leaderboard
            users = User.query.all()
            leaderboard = []
            for i, user in enumerate(users):
                leaderboard.append({
                    'rank': i + 1,
                    'username': user.username,
                    'score': user.get_score()
                })
        
        return jsonify({'success': True, 'leaderboard': leaderboard})
        
    except Exception as e:
        logger.error(f"❌ Error getting leaderboard: {e}")
        return jsonify({'success': False, 'leaderboard': []})

@app.route('/api/user/team-usage')
def get_team_usage():
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Not logged in'})
        
        user_id = session['user_id']
        
        # Get team usage
        winner_usage = TeamWinnerUsage.query.filter_by(user_id=user_id).all()
        loser_usage = TeamLoserUsage.query.filter_by(user_id=user_id).all()
        
        winners = [{'team_id': usage.team_id, 'team_name': usage.team.name} for usage in winner_usage]
        losers = [{'team_id': usage.team_id, 'team_name': usage.team.name} for usage in loser_usage]
        
        return jsonify({
            'success': True,
            'winners': winners,
            'losers': losers
        })
        
    except Exception as e:
        logger.error(f"❌ Error getting team usage: {e}")
        return jsonify({'success': False, 'winners': [], 'losers': []})

# Register pick API endpoints
from pick_api_endpoints import register_pick_endpoints
register_pick_endpoints(app)

if __name__ == '__main__':
    with app.app_context():
        initialize_database()
    
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)

