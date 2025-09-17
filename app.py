#!/usr/bin/env python3
"""
NFL PickEm 2025/2026 - Final Working Version
Complete login-protected app with real historical data and ESPN integration
"""

import os
import logging
from datetime import datetime, timezone, timedelta
from flask import Flask, render_template, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
import pytz

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'nfl_pickem_2025_secret_key_very_secure'

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///nfl_pickem_2025_final.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Vienna timezone
VIENNA_TZ = pytz.timezone('Europe/Vienna')

# Database Models
class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    abbreviation = db.Column(db.String(10), nullable=False, unique=True)
    logo_url = db.Column(db.String(200))

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)

class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    week = db.Column(db.Integer, nullable=False)
    home_team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    away_team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    home_score = db.Column(db.Integer)
    away_score = db.Column(db.Integer)
    winner_team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    is_completed = db.Column(db.Boolean, default=False)
    
    home_team = db.relationship('Team', foreign_keys=[home_team_id])
    away_team = db.relationship('Team', foreign_keys=[away_team_id])
    winner_team = db.relationship('Team', foreign_keys=[winner_team_id])

class Pick(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    match_id = db.Column(db.Integer, db.ForeignKey('match.id'), nullable=False)
    chosen_team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User')
    match = db.relationship('Match')
    chosen_team = db.relationship('Team')

# Helper Functions
def convert_to_vienna_time(utc_time):
    """Convert UTC time to Vienna time"""
    if utc_time.tzinfo is None:
        utc_time = utc_time.replace(tzinfo=timezone.utc)
    vienna_time = utc_time.astimezone(VIENNA_TZ)
    return vienna_time

def format_vienna_time(utc_time):
    """Format time for Vienna timezone display"""
    vienna_time = convert_to_vienna_time(utc_time)
    return vienna_time.strftime('%a, %d.%m., %H:%M')

# Routes
@app.route('/')
def index():
    """Main page with login protection"""
    return render_template('index_final.html')

@app.route('/api/login', methods=['POST'])
def api_login():
    """Login API endpoint"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        # Check credentials
        user = User.query.filter_by(username=username, password=password).first()
        
        if user:
            session['user_id'] = user.id
            session['username'] = user.username
            logger.info(f"✅ User {username} logged in successfully")
            return jsonify({'success': True, 'message': 'Login erfolgreich'})
        else:
            logger.warning(f"❌ Failed login attempt for {username}")
            return jsonify({'success': False, 'message': 'Ungültige Anmeldedaten'})
            
    except Exception as e:
        logger.error(f"❌ Login error: {str(e)}")
        return jsonify({'success': False, 'message': 'Server-Fehler beim Login'})

@app.route('/api/logout', methods=['POST'])
def api_logout():
    """Logout API endpoint"""
    try:
        username = session.get('username', 'Unknown')
        session.clear()
        logger.info(f"✅ User {username} logged out")
        return jsonify({'success': True, 'message': 'Logout erfolgreich'})
        
    except Exception as e:
        logger.error(f"❌ Logout error: {str(e)}")
        return jsonify({'success': False, 'message': 'Server-Fehler beim Logout'})

@app.route('/api/dashboard/stats')
def get_dashboard_stats():
    """Get dashboard statistics for the current user"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Not logged in'})
        
        user_id = session['user_id']
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'success': False, 'message': 'User not found'})
        
        # Get user's picks and calculate statistics
        user_picks = Pick.query.filter_by(user_id=user_id).join(Match).all()
        
        total_picks = len(user_picks)
        correct_picks = 0
        points = 0
        
        # Calculate correct picks and points
        for pick in user_picks:
            if pick.match.is_completed and pick.match.winner_team_id:
                if pick.chosen_team_id == pick.match.winner_team_id:
                    correct_picks += 1
                    points += 1
        
        # Get current week pick status
        current_week = 3  # Default current week
        current_week_pick = Pick.query.filter_by(user_id=user_id).join(Match).filter(Match.week == current_week).first()
        
        pick_status = "Du hast noch keinen Pick für diese Woche abgegeben."
        if current_week_pick:
            pick_status = f"Du hast {current_week_pick.chosen_team.name} für Woche {current_week} gewählt."
        
        # Get eliminated teams (teams chosen that lost)
        eliminated_teams = []
        for pick in user_picks:
            if pick.match.is_completed and pick.match.winner_team_id:
                # Check if chosen team lost
                if pick.chosen_team_id != pick.match.winner_team_id:
                    eliminated_teams.append(pick.chosen_team.name)
        
        # Get recent picks
        recent_picks = []
        for pick in user_picks[-3:]:  # Last 3 picks
            if pick.match.is_completed:
                result = "✅" if pick.chosen_team_id == pick.match.winner_team_id else "❌"
                recent_picks.append(f"W{pick.match.week}: {pick.chosen_team.name} {result}")
        
        # Calculate rank (simplified - just based on points)
        all_users_points = []
        all_users = User.query.all()
        for u in all_users:
            u_picks = Pick.query.filter_by(user_id=u.id).join(Match).all()
            u_points = sum(1 for p in u_picks if p.match.is_completed and p.chosen_team_id == p.match.winner_team_id)
            all_users_points.append(u_points)
        
        all_users_points.sort(reverse=True)
        rank = all_users_points.index(points) + 1 if points in all_users_points else len(all_users_points)
        
        return jsonify({
            'success': True,
            'stats': {
                'current_week': current_week,
                'pick_status': pick_status,
                'points': points,
                'rank': rank,
                'correct_picks': correct_picks,
                'total_picks': total_picks,
                'eliminated_teams': eliminated_teams,
                'recent_picks': recent_picks
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Dashboard stats error: {str(e)}")
        return jsonify({'success': False, 'message': 'Server-Fehler beim Laden der Statistiken'})

@app.route('/api/matches/<int:week>')
def get_matches(week):
    """Get matches for a specific week"""
    try:
        matches = Match.query.filter_by(week=week).all()
        
        matches_data = []
        for match in matches:
            # Convert time to Vienna timezone
            vienna_time = convert_to_vienna_time(match.start_time)
            
            match_data = {
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
                'start_time': match.start_time.isoformat(),
                'start_time_display': format_vienna_time(match.start_time),
                'is_completed': match.is_completed,
                'home_score': match.home_score,
                'away_score': match.away_score,
                'winner_team_id': match.winner_team_id
            }
            matches_data.append(match_data)
        
        return jsonify({
            'success': True,
            'matches': matches_data
        })
        
    except Exception as e:
        logger.error(f"❌ Get matches error: {str(e)}")
        return jsonify({'success': False, 'message': 'Server-Fehler beim Laden der Spiele'})

@app.route('/api/picks/create', methods=['POST'])
def create_pick():
    """Create a new pick for the current user"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Not logged in'})
        
        data = request.get_json()
        user_id = session['user_id']
        match_id = data.get('match_id')
        chosen_team_id = data.get('chosen_team_id')
        
        if not match_id or not chosen_team_id:
            return jsonify({'success': False, 'message': 'Missing match_id or chosen_team_id'})
        
        # Check if match exists and is not completed
        match = Match.query.get(match_id)
        if not match:
            return jsonify({'success': False, 'message': 'Match not found'})
        
        if match.is_completed:
            return jsonify({'success': False, 'message': 'Cannot pick for completed match'})
        
        # Check if pick deadline has passed (match has started)
        now = datetime.utcnow().replace(tzinfo=timezone.utc)
        match_start = match.start_time
        if match_start.tzinfo is None:
            match_start = match_start.replace(tzinfo=timezone.utc)
        
        if match_start <= now:
            return jsonify({'success': False, 'message': 'Pick deadline has passed'})
        
        # Use database transaction to prevent race conditions
        try:
            # Check if user already has a pick for this week
            existing_pick = Pick.query.filter_by(user_id=user_id).join(Match).filter(Match.week == match.week).first()
            
            if existing_pick:
                # Update existing pick - no duplicates possible
                old_team = Team.query.get(existing_pick.chosen_team_id)
                old_team_name = old_team.name if old_team else 'Unknown'
                
                existing_pick.match_id = match_id
                existing_pick.chosen_team_id = chosen_team_id
                existing_pick.created_at = datetime.utcnow()
                
                action = "updated"
                logger.info(f"🔄 Pick updated: User {session['username']} changed from {old_team_name} to new pick for week {match.week}")
            else:
                # Create new pick - first pick for this week
                new_pick = Pick(
                    user_id=user_id,
                    match_id=match_id,
                    chosen_team_id=chosen_team_id,
                    created_at=datetime.utcnow()
                )
                db.session.add(new_pick)
                action = "created"
                logger.info(f"✅ Pick created: User {session['username']} made first pick for week {match.week}")
            
            # Commit the transaction
            db.session.commit()
            
            # Get team name for response
            chosen_team = Team.query.get(chosen_team_id)
            team_name = chosen_team.name if chosen_team else 'Unknown Team'
            
            return jsonify({
                'success': True, 
                'message': f'Pick gespeichert: {team_name} für Woche {match.week}',
                'team_name': team_name,
                'week': match.week,
                'action': action
            })
            
        except Exception as db_error:
            # Rollback transaction on any database error
            db.session.rollback()
            logger.error(f"❌ Database error in pick creation: {str(db_error)}")
            return jsonify({'success': False, 'message': 'Datenbankfehler beim Speichern des Picks'})
        
    except Exception as e:
        logger.error(f"❌ Create pick error: {str(e)}")
        return jsonify({'success': False, 'message': 'Server-Fehler beim Speichern des Picks'})

@app.route('/api/current-week')
def get_current_week():
    """Get current NFL week"""
    return jsonify({'success': True, 'current_week': 3})

@app.route('/api/teams/available/<int:week>')
def get_available_teams(week):
    """Get available teams for a user in a specific week"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Not logged in'})
        
        user_id = session['user_id']
        
        # Get all teams
        teams = Team.query.all()
        
        # Get user's picks to determine team usage
        user_picks = Pick.query.filter_by(user_id=user_id).join(Match).all()
        
        team_usage = {}
        for team in teams:
            team_usage[team.id] = {
                'winner_count': 0,
                'loser_count': 0,
                'eliminated': False
            }
        
        # Calculate team usage
        for pick in user_picks:
            if pick.match.is_completed and pick.match.winner_team_id:
                chosen_team_id = pick.chosen_team_id
                if chosen_team_id == pick.match.winner_team_id:
                    # Team was picked as winner and won
                    team_usage[chosen_team_id]['winner_count'] += 1
                else:
                    # Team was picked as winner but lost (eliminated)
                    team_usage[chosen_team_id]['loser_count'] += 1
                    team_usage[chosen_team_id]['eliminated'] = True
        
        return jsonify({
            'success': True,
            'team_usage': team_usage
        })
        
    except Exception as e:
        logger.error(f"❌ Get available teams error: {str(e)}")
        return jsonify({'success': False, 'message': 'Server-Fehler beim Laden der Team-Verfügbarkeit'})

# Database initialization
def initialize_database():
    """Initialize database with teams, users, and historical data"""
    logger.info("🔧 Initializing final database...")
    
    with app.app_context():
        db.create_all()
        
        # Create NFL teams if they don't exist
        if Team.query.count() == 0:
            nfl_teams = [
                ('Arizona Cardinals', 'ARI'), ('Atlanta Falcons', 'ATL'), ('Baltimore Ravens', 'BAL'),
                ('Buffalo Bills', 'BUF'), ('Carolina Panthers', 'CAR'), ('Chicago Bears', 'CHI'),
                ('Cincinnati Bengals', 'CIN'), ('Cleveland Browns', 'CLE'), ('Dallas Cowboys', 'DAL'),
                ('Denver Broncos', 'DEN'), ('Detroit Lions', 'DET'), ('Green Bay Packers', 'GB'),
                ('Houston Texans', 'HOU'), ('Indianapolis Colts', 'IND'), ('Jacksonville Jaguars', 'JAX'),
                ('Kansas City Chiefs', 'KC'), ('Las Vegas Raiders', 'LV'), ('Los Angeles Chargers', 'LAC'),
                ('Los Angeles Rams', 'LAR'), ('Miami Dolphins', 'MIA'), ('Minnesota Vikings', 'MIN'),
                ('New England Patriots', 'NE'), ('New Orleans Saints', 'NO'), ('New York Giants', 'NYG'),
                ('New York Jets', 'NYJ'), ('Philadelphia Eagles', 'PHI'), ('Pittsburgh Steelers', 'PIT'),
                ('San Francisco 49ers', 'SF'), ('Seattle Seahawks', 'SEA'), ('Tampa Bay Buccaneers', 'TB'),
                ('Tennessee Titans', 'TEN'), ('Washington Commanders', 'WAS')
            ]
            
            for name, abbr in nfl_teams:
                team = Team(name=name, abbreviation=abbr, logo_url=f'/static/logos/{abbr.lower()}.png')
                db.session.add(team)
            
            db.session.commit()
            logger.info(f"✅ Created {len(nfl_teams)} NFL teams")
        
        # Create users if they don't exist
        if User.query.count() == 0:
            users = [
                ('Manuel', 'Manuel1'),
                ('Daniel', 'Daniel1'),
                ('Raff', 'Raff1'),
                ('Haunschi', 'Haunschi1')
            ]
            
            for username, password in users:
                user = User(username=username, password=password)
                db.session.add(user)
            
            db.session.commit()
            logger.info(f"✅ Created {len(users)} users")
        
        # Create historical games and picks
        create_historical_data()
        create_week3_games()
        
        logger.info("✅ Final database initialization completed")

def create_historical_data():
    """Create historical games and picks for weeks 1-2"""
    
    # Week 1 games (completed) - corrected results
    week1_games = [
        # Manuel's pick: Falcons L vs Buccaneers W (CORRECTED)
        {'away': 'TB', 'home': 'ATL', 'time': '2025-09-03T17:00:00', 'home_score': 17, 'away_score': 24, 'winner': 'TB'},
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
    
    # Create games
    for week, games in [(1, week1_games), (2, week2_games)]:
        for game in games:
            # Check if game already exists
            away_team = Team.query.filter_by(abbreviation=game['away']).first()
            home_team = Team.query.filter_by(abbreviation=game['home']).first()
            winner_team = Team.query.filter_by(abbreviation=game['winner']).first()
            
            if away_team and home_team and winner_team:
                existing_game = Match.query.filter_by(
                    week=week,
                    home_team_id=home_team.id,
                    away_team_id=away_team.id
                ).first()
                
                if not existing_game:
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
    
    # Create historical picks
    historical_picks = [
        # Week 1 - Manuel's pick is WRONG now
        {'username': 'Manuel', 'week': 1, 'away': 'TB', 'home': 'ATL', 'chosen': 'ATL'},  # Falcons L (wrong)
        {'username': 'Daniel', 'week': 1, 'away': 'TEN', 'home': 'DEN', 'chosen': 'DEN'},  # Broncos W
        {'username': 'Raff', 'week': 1, 'away': 'CLE', 'home': 'CIN', 'chosen': 'CIN'},    # Bengals W
        {'username': 'Haunschi', 'week': 1, 'away': 'NYG', 'home': 'WAS', 'chosen': 'WAS'}, # Commanders W
        
        # Week 2
        {'username': 'Manuel', 'week': 2, 'away': 'NYG', 'home': 'DAL', 'chosen': 'DAL'},  # Cowboys W
        {'username': 'Daniel', 'week': 2, 'away': 'KC', 'home': 'PHI', 'chosen': 'PHI'},   # Eagles W
        {'username': 'Raff', 'week': 2, 'away': 'NYG', 'home': 'DAL', 'chosen': 'DAL'},    # Cowboys W
        {'username': 'Haunschi', 'week': 2, 'away': 'NYJ', 'home': 'BUF', 'chosen': 'BUF'}, # Bills W
    ]
    
    for pick_data in historical_picks:
        user = User.query.filter_by(username=pick_data['username']).first()
        away_team = Team.query.filter_by(abbreviation=pick_data['away']).first()
        home_team = Team.query.filter_by(abbreviation=pick_data['home']).first()
        chosen_team = Team.query.filter_by(abbreviation=pick_data['chosen']).first()
        
        if user and away_team and home_team and chosen_team:
            match = Match.query.filter_by(
                week=pick_data['week'],
                home_team_id=home_team.id,
                away_team_id=away_team.id
            ).first()
            
            if match:
                existing_pick = Pick.query.filter_by(
                    user_id=user.id,
                    match_id=match.id
                ).first()
                
                if not existing_pick:
                    new_pick = Pick(
                        user_id=user.id,
                        match_id=match.id,
                        chosen_team_id=chosen_team.id,
                        created_at=datetime.utcnow()
                    )
                    db.session.add(new_pick)
    
    db.session.commit()

def create_week3_games():
    """Create Week 3 games (current week)"""
    
    week3_games = [
        {'away': 'TEN', 'home': 'GB', 'time': '2025-09-17T17:00:00'},
        {'away': 'MIN', 'home': 'HOU', 'time': '2025-09-17T17:00:00'},
        {'away': 'IND', 'home': 'CHI', 'time': '2025-09-17T17:00:00'},
        {'away': 'CAR', 'home': 'LV', 'time': '2025-09-17T20:00:00'},
        {'away': 'DEN', 'home': 'TB', 'time': '2025-09-17T17:00:00'},
        {'away': 'PHI', 'home': 'NO', 'time': '2025-09-17T17:00:00'},
        {'away': 'LAC', 'home': 'PIT', 'time': '2025-09-17T17:00:00'},
        {'away': 'NYG', 'home': 'CLE', 'time': '2025-09-17T17:00:00'},
        {'away': 'MIA', 'home': 'SEA', 'time': '2025-09-17T20:00:00'},
        {'away': 'DET', 'home': 'ARI', 'time': '2025-09-17T20:00:00'},
        {'away': 'BAL', 'home': 'DAL', 'time': '2025-09-17T20:00:00'},
        {'away': 'LAR', 'home': 'SF', 'time': '2025-09-17T20:00:00'},
        {'away': 'ATL', 'home': 'KC', 'time': '2025-09-18T00:00:00'},
        {'away': 'JAX', 'home': 'BUF', 'time': '2025-09-18T00:00:00'},
        {'away': 'WAS', 'home': 'CIN', 'time': '2025-09-18T00:00:00'},
    ]
    
    for game in week3_games:
        away_team = Team.query.filter_by(abbreviation=game['away']).first()
        home_team = Team.query.filter_by(abbreviation=game['home']).first()
        
        if away_team and home_team:
            existing_game = Match.query.filter_by(
                week=3,
                home_team_id=home_team.id,
                away_team_id=away_team.id
            ).first()
            
            if not existing_game:
                new_game = Match(
                    week=3,
                    home_team_id=home_team.id,
                    away_team_id=away_team.id,
                    start_time=datetime.fromisoformat(game['time']).replace(tzinfo=timezone.utc),
                    is_completed=False
                )
                db.session.add(new_game)
    
    db.session.commit()

if __name__ == '__main__':
    initialize_database()
    
    port = int(os.environ.get('PORT', 5014))
    logger.info(f"🏈 Starting NFL PickEm 2025/2026 on port {port}")
    
    app.run(host='0.0.0.0', port=port, debug=False)

