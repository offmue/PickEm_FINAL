from flask import Flask, request, jsonify, session, send_from_directory, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = 'nfl-pickem-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///nfl_pickem.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Enable CORS
CORS(app, supports_credentials=True)

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_admin': self.is_admin,
            'score': self.get_score()
        }
    
    def get_score(self):
        """Calculate user's total score based on correct picks"""
        score = 0
        picks = Pick.query.filter_by(user_id=self.id).all()
        for pick in picks:
            match = db.session.get(Match, pick.match_id)
            if match and match.is_completed and match.winner_team_id == pick.chosen_team_id:
                score += 1
        return score

class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    abbreviation = db.Column(db.String(10), nullable=False)
    logo_url = db.Column(db.String(255), nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'abbreviation': self.abbreviation,
            'logo_url': self.logo_url
        }

class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    week = db.Column(db.Integer, nullable=False)
    home_team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    away_team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    is_completed = db.Column(db.Boolean, default=False)
    winner_team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=True)
    
    # New fields for ESPN integration
    home_score = db.Column(db.Integer, nullable=True)
    away_score = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(20), default='scheduled')  # scheduled, in_progress, completed
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    home_team = db.relationship('Team', foreign_keys=[home_team_id])
    away_team = db.relationship('Team', foreign_keys=[away_team_id])
    winner_team = db.relationship('Team', foreign_keys=[winner_team_id])
    
    # Helper properties for ESPN integration
    @property
    def home_team_name(self):
        return self.home_team.name if self.home_team else None
    
    @property
    def away_team_name(self):
        return self.away_team.name if self.away_team else None
    
    @property
    def winner(self):
        return self.winner_team.name if self.winner_team else None
    
    @property
    def is_game_started(self):
        """Check if the game has started (corrected timezone handling)"""
        import pytz
        from datetime import datetime
        
        # Get current time in Vienna
        vienna_tz = pytz.timezone('Europe/Vienna')
        now_vienna = datetime.now(vienna_tz)
        
        # Interpret stored time as US Eastern Time (not UTC!)
        eastern_tz = pytz.timezone('US/Eastern')
        
        if self.start_time.tzinfo is None:
            # Stored time is US Eastern Time without timezone info
            start_time_eastern = eastern_tz.localize(self.start_time)
        else:
            # If timezone info exists, convert to Eastern first
            start_time_eastern = self.start_time.astimezone(eastern_tz)
            
        # Convert to Vienna time for comparison
        start_time_vienna = start_time_eastern.astimezone(vienna_tz)
        
        return now_vienna >= start_time_vienna
    
    @property
    def start_time_vienna(self):
        """Get start time in Vienna timezone (corrected)"""
        import pytz
        
        vienna_tz = pytz.timezone('Europe/Vienna')
        eastern_tz = pytz.timezone('US/Eastern')
        
        if self.start_time.tzinfo is None:
            # Stored time is US Eastern Time
            start_time_eastern = eastern_tz.localize(self.start_time)
        else:
            start_time_eastern = self.start_time.astimezone(eastern_tz)
            
        return start_time_eastern.astimezone(vienna_tz)
    
    @winner.setter
    def winner(self, team_name):
        if team_name:
            team = Team.query.filter_by(name=team_name).first()
            if team:
                self.winner_team_id = team.id
                self.is_completed = True
                self.status = 'completed'
    
    def to_dict(self):
        return {
            'id': self.id,
            'week': self.week,
            'home_team': self.home_team.to_dict(),
            'away_team': self.away_team.to_dict(),
            'start_time': self.start_time.isoformat(),
            'start_time_vienna': self.start_time_vienna.isoformat(),
            'is_completed': self.is_completed,
            'is_game_started': self.is_game_started,
            'home_score': self.home_score,
            'away_score': self.away_score,
            'status': self.status,
            'winner': self.winner,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'winner_team': self.winner_team.to_dict() if self.winner_team_id else None
        }

class Pick(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    match_id = db.Column(db.Integer, db.ForeignKey('match.id'), nullable=False)
    chosen_team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    
    user = db.relationship('User')
    match = db.relationship('Match')
    chosen_team = db.relationship('Team')
    
    @property
    def is_correct(self):
        if not self.match.is_completed:
            return False
        return self.chosen_team_id == self.match.winner_team_id
    
    def to_dict(self):
        return {
            'id': self.id,
            'user': self.user.to_dict(),
            'match': self.match.to_dict(),
            'chosen_team': self.chosen_team.to_dict(),
            'is_correct': self.is_correct
        }

class EliminatedTeam(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    elimination_type = db.Column(db.String(20), nullable=False)  # 'winner' or 'loser'
    
    user = db.relationship('User')
    team = db.relationship('Team')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user': self.user.to_dict(),
            'team': self.team.to_dict(),
            'elimination_type': self.elimination_type
        }

class TeamWinnerUsage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    usage_count = db.Column(db.Integer, default=0)
    
    user = db.relationship('User')
    team = db.relationship('Team')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user': self.user.to_dict(),
            'team': self.team.to_dict(),
            'usage_count': self.usage_count
        }

class TeamLoserUsage(db.Model):
    """Tracks teams that have been picked as losers (automatically when picking a winner)"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    week = db.Column(db.Integer, nullable=False)  # Track which week this happened
    match_id = db.Column(db.Integer, db.ForeignKey('match.id'), nullable=False)  # Track the specific match
    
    user = db.relationship('User')
    team = db.relationship('Team')
    match = db.relationship('Match')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user': self.user.to_dict(),
            'team': self.team.to_dict(),
            'week': self.week,
            'match': self.match.to_dict()
        }

# API Routes
@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON data'}), 400
            
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            return jsonify({
                'message': 'Login successful',
                'user': user.to_dict()
            }), 200
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
    except Exception as e:
        print(f"Error in login: {e}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

@app.route('/api/auth/logout', methods=['POST', 'GET'])
def logout():
    try:
        session.pop('user_id', None)
        return jsonify({'message': 'Logout successful'}), 200
    except Exception as e:
        print(f"Error in logout: {e}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

@app.route('/api/auth/me', methods=['GET'])
def get_current_user():
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        user = db.session.get(User, user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'user': user.to_dict()
        }), 200
    except Exception as e:
        print(f"Error in get_current_user: {e}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

@app.route('/api/auth/check-session', methods=['GET'])
def check_session():
    """Check if user has active session"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'user': None}), 200
        
        user = db.session.get(User, user_id)
        if not user:
            session.pop('user_id', None)  # Clear invalid session
            return jsonify({'user': None}), 200
        
        return jsonify({
            'user': user.to_dict()
        }), 200
    except Exception as e:
        print(f"Error in check_session: {e}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

@app.route('/api/user/stats', methods=['GET'])
def get_user_stats():
    """Get user statistics (points, rank)"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        user = db.session.get(User, user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Calculate user score
        user_score = user.get_score()
        
        # Calculate user rank
        users = User.query.all()
        leaderboard = []
        for u in users:
            score = u.get_score()
            leaderboard.append({
                'id': u.id,
                'username': u.username,
                'score': score
            })
            
        leaderboard.sort(key=lambda x: x['score'], reverse=True)
        
        # Find user rank
        user_rank = None
        current_rank = 1
        for i, u in enumerate(leaderboard):
            if i > 0 and leaderboard[i]['score'] < leaderboard[i-1]['score']:
                current_rank = i + 1
            
            if u['id'] == user_id:
                user_rank = current_rank
                break
        
        return jsonify({
            'points': user_score,
            'rank': user_rank or '-'
        }), 200
    except Exception as e:
        print(f"Error in get_user_stats: {e}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

@app.route('/api/teams', methods=['GET'])
def get_teams():
    try:
        teams = Team.query.all()
        return jsonify({
            'teams': [team.to_dict() for team in teams]
        }), 200
    except Exception as e:
        print(f"Error in get_teams: {e}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

@app.route('/api/matches', methods=['GET'])
def get_matches():
    try:
        week = request.args.get('week', type=int)
        
        if week:
            matches = Match.query.filter_by(week=week).all()
        else:
            matches = Match.query.all()
            
        return jsonify({
            'matches': [match.to_dict() for match in matches]
        }), 200
    except Exception as e:
        print(f"Error in get_matches: {e}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

@app.route('/api/current-week', methods=['GET'])
def get_current_week():
    try:
        # For simplicity, we'll return week 2 as the current week
        return jsonify({
            'current_week': 2
        }), 200
    except Exception as e:
        print(f"Error in get_current_week: {e}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

@app.route('/api/picks', methods=['GET', 'POST'])
def handle_picks():
    try:
        if request.method == 'GET':
            # GET-Logik bleibt unverändert
            user_id = request.args.get('user_id', type=int)
            week = request.args.get('week', type=int)
            
            if not user_id:
                return jsonify({'error': 'User ID required'}), 400
                
            query = Pick.query.filter_by(user_id=user_id)
            
            if week:
                picks = query.join(Match).filter(Match.week == week).all()
            else:
                picks = query.all()
                
            return jsonify({
                'picks': [pick.to_dict() for pick in picks]
            }), 200
        
        elif request.method == 'POST':
            user_id = session.get('user_id')
            if not user_id:
                return jsonify({'error': 'Not authenticated'}), 401
                
            data = request.get_json()
            match_id = data.get('match_id')
            chosen_team_id = data.get('chosen_team_id')
            
            if not match_id or not chosen_team_id:
                return jsonify({'error': 'Match ID and chosen team ID required'}), 400
            
            # === BASIC VALIDATIONS ===
            match = db.session.get(Match, match_id)
            if not match:
                return jsonify({'error': 'Match not found'}), 404
            
            team = db.session.get(Team, chosen_team_id)
            if not team:
                return jsonify({'error': 'Team not found'}), 404
            
            # Check if team is part of the match
            if team.id not in [match.home_team_id, match.away_team_id]:
                return jsonify({'error': 'Team is not part of this match'}), 400
            
            # Check if game has started
            if match.is_game_started:
                return jsonify({'error': 'Game has already started. Picks are no longer allowed.'}), 400
            
            # Check if match is completed
            if match.is_completed:
                return jsonify({'error': 'Cannot pick for completed match'}), 400
            
            # === DETERMINE OPPOSING TEAM ===
            opposing_team_id = match.away_team_id if team.id == match.home_team_id else match.home_team_id
            
            # === ELIMINATION CHECKS ===
            # Check if chosen team is winner-eliminated (used 2x as winner)
            winner_eliminated = EliminatedTeam.query.filter_by(
                user_id=user_id, 
                team_id=team.id, 
                elimination_type='winner'
            ).first()
            if winner_eliminated:
                return jsonify({'error': f'{team.name} cannot be picked as winner (already used 2x as winner)'}), 400
            
            # Check if opposing team is loser-eliminated (already used 1x as loser)
            loser_eliminated = EliminatedTeam.query.filter_by(
                user_id=user_id, 
                team_id=opposing_team_id, 
                elimination_type='loser'
            ).first()
            if loser_eliminated:
                opposing_team = db.session.get(Team, opposing_team_id)
                return jsonify({'error': f'{opposing_team.name} cannot be picked as loser (already used 1x as loser)'}), 400
            
            # === USAGE LIMIT CHECKS ===
            # Check winner usage limit (max 2x)
            winner_usage = TeamWinnerUsage.query.filter_by(user_id=user_id, team_id=team.id).first()
            if winner_usage and winner_usage.usage_count >= 2:
                return jsonify({'error': f'{team.name} has already been picked as winner 2 times this season'}), 400
            
            # Check loser usage limit (max 1x)
            loser_usage = TeamLoserUsage.query.filter_by(user_id=user_id, team_id=opposing_team_id).first()
            if loser_usage:
                opposing_team = db.session.get(Team, opposing_team_id)
                return jsonify({'error': f'{opposing_team.name} has already been picked as loser this season'}), 400
            
            # === HANDLE PICK (CREATE OR UPDATE) ===
            existing_week_pick = Pick.query.join(Match).filter(
                Pick.user_id == user_id,
                Match.week == match.week
            ).first()
            
            if existing_week_pick:
                # UPDATE EXISTING PICK (Pick-Wechsel)
                result = update_existing_pick(user_id, existing_week_pick, match, team.id, opposing_team_id)
                if result.get('error'):
                    return jsonify(result), 400
                    
                return jsonify({
                    'message': 'Pick updated successfully',
                    'pick': existing_week_pick.to_dict()
                }), 200
            else:
                # CREATE NEW PICK
                result = create_new_pick(user_id, match, team.id, opposing_team_id)
                if result.get('error'):
                    return jsonify(result), 400
                    
                return jsonify({
                    'message': 'Pick created successfully',
                    'pick': result['pick'].to_dict()
                }), 201
                
    except Exception as e:
        print(f"Error in handle_picks: {e}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500


def update_existing_pick(user_id, existing_pick, new_match, new_team_id, new_opposing_team_id):
    """
    Update existing pick - nur bei laufenden Spielen, nicht bei abgeschlossenen
    """
    try:
        old_match = existing_pick.match
        old_team_id = existing_pick.chosen_team_id
        old_opposing_team_id = old_match.away_team_id if old_team_id == old_match.home_team_id else old_match.home_team_id
        
        # Wenn sich nichts ändert, nichts tun
        if existing_pick.match_id == new_match.id and old_team_id == new_team_id:
            return {'success': True}
        
        # WICHTIG: Nur bei nicht-abgeschlossenen Spielen Usage zurücksetzen
        if not old_match.is_completed:
            # Entferne alte Usage-Einträge (nur bei laufenden Spielen)
            remove_temporary_usage(user_id, old_team_id, old_opposing_team_id, old_match.id)
        
        # Update Pick
        existing_pick.match_id = new_match.id
        existing_pick.chosen_team_id = new_team_id
        
        # Füge neue Usage-Einträge hinzu (nur bei laufenden Spielen)
        if not new_match.is_completed:
            add_temporary_usage(user_id, new_team_id, new_opposing_team_id, new_match)
        
        db.session.commit()
        return {'success': True}
        
    except Exception as e:
        db.session.rollback()
        return {'error': f'Failed to update pick: {str(e)}'}


def create_new_pick(user_id, match, team_id, opposing_team_id):
    """
    Create new pick and apply elimination rules immediately
    REPARIERT: Mit Duplikat-Checks für EliminatedTeam und TeamWinnerUsage
    """
    try:
        # Create pick
        new_pick = Pick(
            user_id=user_id,
            match_id=match.id,
            chosen_team_id=team_id
        )
        db.session.add(new_pick)
        
        # IMMEDIATE ELIMINATION LOGIC (based on choice, not game result)
        
        # 1. Eliminate opposing team as loser (can never be chosen as loser again)
        # CHECK FOR DUPLICATES FIRST!
        existing_loser_elimination = EliminatedTeam.query.filter_by(
            user_id=user_id,
            team_id=opposing_team_id,
            elimination_type='loser'
        ).first()
        
        if not existing_loser_elimination:
            loser_elimination = EliminatedTeam(
                user_id=user_id,
                team_id=opposing_team_id,
                elimination_type='loser'
            )
            db.session.add(loser_elimination)
        
        # 2. Update winner usage count
        # CHECK FOR EXISTING USAGE FIRST!
        winner_usage = TeamWinnerUsage.query.filter_by(user_id=user_id, team_id=team_id).first()
        if winner_usage:
            # DON'T INCREMENT IF ALREADY AT CORRECT COUNT!
            # Count actual picks instead of incrementing blindly
            actual_picks = Pick.query.filter_by(user_id=user_id, chosen_team_id=team_id).count()
            winner_usage.usage_count = actual_picks
        else:
            winner_usage = TeamWinnerUsage(user_id=user_id, team_id=team_id, usage_count=1)
            db.session.add(winner_usage)
        
        # 3. Check if chosen team should be eliminated as winner (2x limit)
        # CHECK FOR EXISTING WINNER ELIMINATION FIRST!
        if winner_usage.usage_count >= 2:
            existing_winner_elimination = EliminatedTeam.query.filter_by(
                user_id=user_id,
                team_id=team_id,
                elimination_type='winner'
            ).first()
            
            if not existing_winner_elimination:
                winner_elimination = EliminatedTeam(
                    user_id=user_id,
                    team_id=team_id,
                    elimination_type='winner'
                )
                db.session.add(winner_elimination)
        
        db.session.commit()
        return {'success': True, 'pick': new_pick}
        
    except Exception as e:
        db.session.rollback()
        return {'error': f'Failed to create pick: {str(e)}'}


def add_temporary_usage(user_id, team_id, opposing_team_id, match):
    """
    Füge temporäre Usage-Einträge hinzu (werden bei Spielende finalisiert)
    REPARIERT: Mit Duplikat-Checks
    """
    # Winner usage - CHECK FOR DUPLICATES!
    winner_usage = TeamWinnerUsage.query.filter_by(user_id=user_id, team_id=team_id).first()
    if winner_usage:
        # Count actual picks instead of incrementing
        actual_picks = Pick.query.filter_by(user_id=user_id, chosen_team_id=team_id).count()
        winner_usage.usage_count = actual_picks
    else:
        winner_usage = TeamWinnerUsage(user_id=user_id, team_id=team_id, usage_count=1)
        db.session.add(winner_usage)
    
    # Loser usage - CHECK FOR DUPLICATES!
    existing_loser_usage = TeamLoserUsage.query.filter_by(
        user_id=user_id,
        team_id=opposing_team_id,
        match_id=match.id
    ).first()
    
    if not existing_loser_usage:
        loser_usage = TeamLoserUsage(
            user_id=user_id,
            team_id=opposing_team_id,
            week=match.week,
            match_id=match.id
        )
        db.session.add(loser_usage)


def remove_temporary_usage(user_id, team_id, opposing_team_id, match_id):
    """
    Entferne temporäre Usage-Einträge (bei Pick-Wechsel)
    REPARIERT: Mit korrekter Zählung
    """
    # Remove winner usage - COUNT ACTUAL PICKS!
    winner_usage = TeamWinnerUsage.query.filter_by(user_id=user_id, team_id=team_id).first()
    if winner_usage:
        # Count actual remaining picks
        actual_picks = Pick.query.filter_by(user_id=user_id, chosen_team_id=team_id).count()
        if actual_picks > 0:
            winner_usage.usage_count = actual_picks
        else:
            db.session.delete(winner_usage)
    
    # Remove loser usage
    loser_usage = TeamLoserUsage.query.filter_by(
        user_id=user_id, 
        team_id=opposing_team_id, 
        match_id=match_id
    ).first()
    if loser_usage:
        db.session.delete(loser_usage)


@app.route('/api/picks/score', methods=['GET'])
def get_user_scores():
    try:
        user_id = request.args.get('user_id', type=int)
        
        if not user_id:
            return jsonify({'error': 'User ID required'}), 400
            
        # Get the user
        user = db.session.get(User, user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        # Get all other users
        other_users = User.query.filter(User.id != user_id).all()
        
        return jsonify({
            'user': {
                'id': user.id,
                'username': user.username,
                'score': user.get_score()
            },
            'opponents': [
                {
                    'id': other_user.id,
                    'username': other_user.username,
                    'score': other_user.get_score()
                }
                for other_user in other_users
            ]
        }), 200
    except Exception as e:
        print(f"Error in get_user_scores: {e}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

@app.route('/api/picks/recent', methods=['GET'])
def get_recent_picks():
    try:
        user_id = request.args.get('user_id', type=int)
        
        if not user_id:
            return jsonify({'error': 'User ID required'}), 400
            
        # Get the user
        user = db.session.get(User, user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        # Get recent picks (last 2 weeks)
        recent_picks = []
        
        # Get current week
        current_week = 2  # Hardcoded for simplicity
        
        # Get picks for current week and previous week
        for week in range(current_week, 0, -1):
            picks = Pick.query.join(Match).filter(
                Pick.user_id == user_id,
                Match.week == week
            ).all()
            
            for pick in picks:
                # Get team and match info
                team = db.session.get(Team, pick.chosen_team_id)
                match = db.session.get(Match, pick.match_id)
                
                # Calculate if pick is correct
                is_correct = False
                if match and match.is_completed and match.winner_team_id == pick.chosen_team_id:
                    is_correct = True
                
                recent_picks.append({
                    'week': match.week,
                    'team': team.name,
                    'team_logo': team.logo_url,
                    'is_completed': match.is_completed,
                    'is_correct': is_correct
                })
        
        return jsonify({
            'picks': recent_picks
        }), 200
    except Exception as e:
        print(f"Error in get_recent_picks: {e}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

@app.route('/api/picks/eliminated', methods=['GET'])
def get_eliminated_teams():
    try:
        user_id = request.args.get('user_id', type=int)
        
        if not user_id:
            return jsonify({'error': 'User ID required'}), 400
            
        # Get the user
        user = db.session.get(User, user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        # Get eliminated teams
        eliminated_teams = EliminatedTeam.query.filter_by(user_id=user_id).all()
        
        eliminated_list = []
        seen_teams = set()  # Track seen team+type combinations to prevent duplicates
        
        for elim_team in eliminated_teams:
            team = db.session.get(Team, elim_team.team_id)
            if team:
                # Create unique key for team+elimination_type combination
                team_key = f"{team.id}_{elim_team.elimination_type}"
                
                # Only add if we haven't seen this team+type combination before
                if team_key not in seen_teams:
                    seen_teams.add(team_key)
                    eliminated_list.append({
                        'id': team.id,
                        'name': team.name,
                        'abbreviation': team.abbreviation,
                        'logo_url': team.logo_url,
                        'elimination_type': elim_team.elimination_type
                    })
        
        return jsonify({
            'eliminated_teams': eliminated_list
        }), 200
    except Exception as e:
        print(f"Error in get_eliminated_teams: {e}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

@app.route('/api/picks/team-usage', methods=['GET'])
def get_team_winner_usage():
    try:
        user_id = request.args.get('user_id', type=int)
        
        if not user_id:
            return jsonify({'error': 'User ID required'}), 400
            
        # Get the user
        user = db.session.get(User, user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        # Get team winner usage - only for teams the user actually picked as winners
        team_usage = TeamWinnerUsage.query.filter_by(user_id=user_id).filter(TeamWinnerUsage.usage_count > 0).all()
        team_status = []
        for usage in team_usage:
            team_status.append({
                'team': usage.team.to_dict(),
                'usage_count': usage.usage_count,
                'status': 'used_once' if usage.usage_count == 1 else 'max_used'
            })
        
        return jsonify({
            'team_usage': team_status
        }), 200
    except Exception as e:
        print(f"Error in get_team_winner_usage: {e}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

@app.route('/api/picks/loser-usage', methods=['GET'])
def get_team_loser_usage():
    """Get teams that have been used as losers by a user"""
    try:
        user_id = request.args.get('user_id', type=int)
        
        if not user_id:
            return jsonify({'error': 'User ID required'}), 400
            
        # Get the user
        user = db.session.get(User, user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        # Get teams used as losers
        loser_usage = TeamLoserUsage.query.filter_by(user_id=user_id).all()
        
        loser_teams = []
        for usage in loser_usage:
            loser_teams.append(usage.team.to_dict())
        
        return jsonify({
            'loser_teams': loser_teams
        }), 200
    except Exception as e:
        print(f"Error in get_team_loser_usage: {e}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    try:
        users = User.query.all()
        
        # Calculate scores and sort by score (descending)
        leaderboard = []
        for user in users:
            score = user.get_score()
            leaderboard.append({
                'id': user.id,
                'username': user.username,
                'score': score
            })
            
        leaderboard.sort(key=lambda x: x['score'], reverse=True)
        
        # Add emojis for first and last place (if not tied)
        if len(leaderboard) > 1:
            # Check if first place is not tied
            if leaderboard[0]['score'] > leaderboard[1]['score']:
                leaderboard[0]['emoji'] = '💪'
                
            # Check if last place is not tied
            if leaderboard[-1]['score'] < leaderboard[-2]['score']:
                leaderboard[-1]['emoji'] = '💩'
        
        return jsonify({
            'leaderboard': leaderboard
        }), 200
    except Exception as e:
        print(f"Error in get_leaderboard: {e}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

# Get user rank
@app.route('/api/user/rank', methods=['GET'])
def get_user_rank():
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'User ID is required'}), 400
            
        # Get all users and calculate scores
        users = User.query.all()
        
        # Calculate scores and sort by score (descending)
        leaderboard = []
        for user in users:
            score = user.get_score()
            leaderboard.append({
                'id': user.id,
                'username': user.username,
                'score': score
            })
            
        leaderboard.sort(key=lambda x: x['score'], reverse=True)
        
        # Find the user's rank (handle ties correctly)
        user_rank = None
        current_rank = 1
        for i, user in enumerate(leaderboard):
            # If this user has a lower score than the previous user, update rank
            if i > 0 and leaderboard[i]['score'] < leaderboard[i-1]['score']:
                current_rank = i + 1
            
            if user['id'] == int(user_id):
                user_rank = current_rank
                break
                
        if user_rank is None:
            return jsonify({'error': 'User not found'}), 404
            
        return jsonify({
            'rank': user_rank
        }), 200
    except Exception as e:
        print(f"Error in get_user_rank: {e}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

# Scheduler API endpoints
@app.route('/api/scheduler/status', methods=['GET'])
def get_scheduler_status():
    """Get current scheduler status"""
    try:
        # Get current week info
        current_week = 2  # This could be dynamic
        
        # Get completed matches count
        completed_matches = Match.query.filter_by(status='completed').count()
        total_matches = Match.query.count()
        
        return jsonify({
            'status': 'running',
            'current_week': current_week,
            'completed_matches': completed_matches,
            'total_matches': total_matches,
            'last_update': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        print(f"Error in get_scheduler_status: {e}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

@app.route('/api/scheduler/manual-update', methods=['POST'])
def manual_update():
    """Manually trigger an update for a specific week"""
    try:
        data = request.get_json()
        week = data.get('week', 2)
        
        # Import and run the ESPN integration
        from espn_integration import ESPNIntegration
        espn = ESPNIntegration()
        
        success = espn.process_weekly_update(week)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Week {week} updated successfully',
                'week': week
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': f'Week {week} update failed or not completed',
                'week': week
            }), 400
            
    except Exception as e:
        print(f"Error in manual_update: {e}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

@app.route('/api/matches/results', methods=['GET'])
def get_match_results():
    """Get match results with scores"""
    try:
        week = request.args.get('week', type=int)
        
        query = Match.query
        if week:
            query = query.filter_by(week=week)
        
        matches = query.filter_by(status='completed').all()
        
        return jsonify({
            'matches': [match.to_dict() for match in matches]
        }), 200
    except Exception as e:
        print(f"Error in get_match_results: {e}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

# Serve static files
@app.route('/')
def index():
    """Serve the main application page"""
    return render_template('index.html')

@app.route('/picks')
def picks():
    """Serve the picks page"""
    return render_template('index.html')

@app.route('/leaderboard')
def leaderboard():
    """Serve the leaderboard page"""
    return render_template('index.html')

@app.route('/alle-picks')
def alle_picks():
    """Serve the alle-picks page"""
    return render_template('index.html')

@app.route('/<path:path>')
def serve_static(path):
    """Serve static files"""
    return send_from_directory('static', path)

# Initialize database
with app.app_context():
    db.create_all()

# Register Database Sync API
from database_sync_api import register_database_sync_api
register_database_sync_api(app)
logger.info("Database Sync API registered successfully")

# Start validation service with toggle
enable_validator = os.getenv('ENABLE_VALIDATOR', 'true').lower() == 'true'

if enable_validator:
    # PRODUCTION MODE - Start validation service
    try:
        from game_validator import start_validation_service_thread
        validation_thread = start_validation_service_thread()
        logger.info("NFL Game Validation Service started successfully (PRODUCTION MODE)")
    except ImportError as e:
        logger.warning(f"Could not start validation service: {e}")
    except Exception as e:
        logger.error(f"Error starting validation service: {e}")
else:
    # TEST MODE - Skip validation service
    logger.info("Game Validation Service DISABLED for testing (TEST MODE)")

if __name__ == '__main__':
    # Disable caching for development
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    port = int(os.environ.get('FLASK_RUN_PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)





@app.route('/api/users', methods=['GET'])
def get_users():
    try:
        users = User.query.all()
        return jsonify([user.to_dict() for user in users]), 200
    except Exception as e:
        print(f"Error in get_users: {e}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500


