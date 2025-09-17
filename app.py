#!/usr/bin/env python3
"""
Vollständige NFL PickEm 2025 App
Integration aller Komponenten: SportsData.io, Pick-Logik, Frontend
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import pytz
import os
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

# Import unserer Module
from sportsdata_integration import SportsDataAPI
from pick_logic_backend import PickLogicBackend
from nfl_results_validator import NFLResultsValidator
from nfl_team_logos import update_team_logos_in_database, get_team_logo_url

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask App Setup
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'nfl-pickem-2025-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///nfl_pickem.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Database Setup
db = SQLAlchemy(app)

# Timezone
vienna_tz = pytz.timezone('Europe/Vienna')

# ===== DATABASE MODELS =====

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    picks = db.relationship('Pick', backref='user', lazy=True)
    winner_usage = db.relationship('TeamWinnerUsage', backref='user', lazy=True)
    loser_usage = db.relationship('TeamLoserUsage', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_score(self):
        """Berechnet die Gesamtpunkte des Users"""
        return Pick.query.filter_by(user_id=self.id, is_correct=True).count()
    
    def get_rank(self):
        """Berechnet den Rang des Users"""
        user_score = self.get_score()
        better_users = db.session.query(User).filter(
            User.id != self.id
        ).all()
        
        better_count = 0
        for user in better_users:
            if user.get_score() > user_score:
                better_count += 1
        
        return better_count + 1

class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    abbreviation = db.Column(db.String(5), unique=True, nullable=False)
    logo_url = db.Column(db.String(255))
    conference = db.Column(db.String(3))  # AFC/NFC
    division = db.Column(db.String(20))
    
    # Relationships
    home_matches = db.relationship('Match', foreign_keys='Match.home_team_id', backref='home_team', lazy=True)
    away_matches = db.relationship('Match', foreign_keys='Match.away_team_id', backref='away_team', lazy=True)
    picks = db.relationship('Pick', backref='chosen_team', lazy=True)

class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    week = db.Column(db.Integer, nullable=False)
    season = db.Column(db.Integer, default=2025)
    home_team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    away_team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    
    # Ergebnisse
    home_score = db.Column(db.Integer)
    away_score = db.Column(db.Integer)
    winner_team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    is_completed = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), default='scheduled')  # scheduled, in_progress, completed
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    picks = db.relationship('Pick', backref='match', lazy=True)
    winner_team = db.relationship('Team', foreign_keys=[winner_team_id])

class Pick(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    match_id = db.Column(db.Integer, db.ForeignKey('match.id'), nullable=False)
    chosen_team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    
    # Ergebnisse
    points_earned = db.Column(db.Integer, default=0)
    is_correct = db.Column(db.Boolean)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint: Ein User kann nur einen Pick pro Woche haben
    __table_args__ = (db.UniqueConstraint('user_id', 'match_id', name='unique_user_match_pick'),)

class TeamWinnerUsage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    team = db.relationship('Team', backref='winner_usage')

class TeamLoserUsage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    team = db.relationship('Team', backref='loser_usage')

# ===== INITIALIZATION =====

def initialize_database():
    """Initialisiert die Datenbank mit Teams und Test-Daten"""
    logger.info("🔧 Initializing database...")
    
    with app.app_context():
        db.create_all()
        
        # Teams erstellen falls nicht vorhanden
        if Team.query.count() == 0:
            create_nfl_teams()
        
        # Test-User erstellen falls nicht vorhanden
        if User.query.count() == 0:
            create_test_users()
        
        # Team-Logos aktualisieren
        update_team_logos_in_database()
        
        logger.info("✅ Database initialization completed")

def create_nfl_teams():
    """Erstellt alle 32 NFL Teams"""
    nfl_teams = [
        # AFC East
        ('Buffalo Bills', 'BUF', 'AFC', 'East'),
        ('Miami Dolphins', 'MIA', 'AFC', 'East'),
        ('New England Patriots', 'NE', 'AFC', 'East'),
        ('New York Jets', 'NYJ', 'AFC', 'East'),
        
        # AFC North
        ('Baltimore Ravens', 'BAL', 'AFC', 'North'),
        ('Cincinnati Bengals', 'CIN', 'AFC', 'North'),
        ('Cleveland Browns', 'CLE', 'AFC', 'North'),
        ('Pittsburgh Steelers', 'PIT', 'AFC', 'North'),
        
        # AFC South
        ('Houston Texans', 'HOU', 'AFC', 'South'),
        ('Indianapolis Colts', 'IND', 'AFC', 'South'),
        ('Jacksonville Jaguars', 'JAX', 'AFC', 'South'),
        ('Tennessee Titans', 'TEN', 'AFC', 'South'),
        
        # AFC West
        ('Denver Broncos', 'DEN', 'AFC', 'West'),
        ('Kansas City Chiefs', 'KC', 'AFC', 'West'),
        ('Las Vegas Raiders', 'LV', 'AFC', 'West'),
        ('Los Angeles Chargers', 'LAC', 'AFC', 'West'),
        
        # NFC East
        ('Dallas Cowboys', 'DAL', 'NFC', 'East'),
        ('New York Giants', 'NYG', 'NFC', 'East'),
        ('Philadelphia Eagles', 'PHI', 'NFC', 'East'),
        ('Washington Commanders', 'WAS', 'NFC', 'East'),
        
        # NFC North
        ('Chicago Bears', 'CHI', 'NFC', 'North'),
        ('Detroit Lions', 'DET', 'NFC', 'North'),
        ('Green Bay Packers', 'GB', 'NFC', 'North'),
        ('Minnesota Vikings', 'MIN', 'NFC', 'North'),
        
        # NFC South
        ('Atlanta Falcons', 'ATL', 'NFC', 'South'),
        ('Carolina Panthers', 'CAR', 'NFC', 'South'),
        ('New Orleans Saints', 'NO', 'NFC', 'South'),
        ('Tampa Bay Buccaneers', 'TB', 'NFC', 'South'),
        
        # NFC West
        ('Arizona Cardinals', 'ARI', 'NFC', 'West'),
        ('Los Angeles Rams', 'LAR', 'NFC', 'West'),
        ('San Francisco 49ers', 'SF', 'NFC', 'West'),
        ('Seattle Seahawks', 'SEA', 'NFC', 'West'),
    ]
    
    for name, abbr, conf, div in nfl_teams:
        logo_url = get_team_logo_url(abbr)
        team = Team(
            name=name,
            abbreviation=abbr,
            conference=conf,
            division=div,
            logo_url=logo_url
        )
        db.session.add(team)
    
    db.session.commit()
    logger.info("✅ Created 32 NFL teams")

def create_test_users():
    """Erstellt Test-User"""
    test_users = [
        ('Manuel', 'Manuel1'),
        ('Daniel', 'Daniel1'),
        ('Raff', 'Raff1'),
        ('Haunschi', 'Haunschi1')
    ]
    
    for username, password in test_users:
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
    
    db.session.commit()
    logger.info("✅ Created test users")

# ===== API ENDPOINTS =====

# Import Pick API Endpoints
from pick_api_endpoints import register_pick_endpoints

# Basis-Endpoints
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    user = User.query.filter_by(username=username).first()
    
    if user and user.check_password(password):
        session['user_id'] = user.id
        session['username'] = user.username
        
        return jsonify({
            'success': True,
            'message': 'Login erfolgreich',
            'user': {
                'id': user.id,
                'username': user.username
            }
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Ungültige Anmeldedaten'
        }), 401

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Logout erfolgreich'})

@app.route('/api/auth/session', methods=['GET'])
def check_session():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        return jsonify({
            'logged_in': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'score': user.get_score(),
                'rank': user.get_rank()
            }
        })
    else:
        return jsonify({'logged_in': False})

@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    users = User.query.all()
    leaderboard = []
    
    for user in users:
        leaderboard.append({
            'username': user.username,
            'score': user.get_score(),
            'rank': user.get_rank()
        })
    
    # Sortiere nach Punkten (höchste zuerst)
    leaderboard.sort(key=lambda x: x['score'], reverse=True)
    
    return jsonify({
        'success': True,
        'leaderboard': leaderboard
    })

@app.route('/api/user/team-usage', methods=['GET'])
def get_team_usage():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Nicht eingeloggt'}), 401
    
    user_id = session['user_id']
    
    # Winner Usage
    winner_usage = db.session.query(TeamWinnerUsage, Team).join(Team).filter(
        TeamWinnerUsage.user_id == user_id
    ).all()
    
    # Loser Usage
    loser_usage = db.session.query(TeamLoserUsage, Team).join(Team).filter(
        TeamLoserUsage.user_id == user_id
    ).all()
    
    winner_teams = [{'name': team.name, 'abbreviation': team.abbreviation} for _, team in winner_usage]
    loser_teams = [{'name': team.name, 'abbreviation': team.abbreviation} for _, team in loser_usage]
    
    return jsonify({
        'success': True,
        'winner_teams': winner_teams,
        'loser_teams': loser_teams
    })

# ===== SCHEDULER SETUP =====

def setup_scheduler():
    """Setzt den Scheduler für automatische NFL-Syncs auf"""
    scheduler = BackgroundScheduler()
    
    # Täglicher NFL Results Sync um 07:00 Wiener Zeit
    scheduler.add_job(
        func=run_daily_nfl_validation,
        trigger=CronTrigger(hour=7, minute=0, timezone=vienna_tz),
        id='daily_nfl_validation',
        name='Daily NFL Results Validation',
        replace_existing=True
    )
    
    # Wöchentlicher Schedule Sync jeden Dienstag um 07:00 Wiener Zeit
    scheduler.add_job(
        func=run_weekly_schedule_sync,
        trigger=CronTrigger(day_of_week=1, hour=7, minute=0, timezone=vienna_tz),  # Dienstag = 1
        id='weekly_schedule_sync',
        name='Weekly NFL Schedule Sync',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("✅ Scheduler started for NFL syncs")

def run_daily_nfl_validation():
    """Wrapper für tägliche NFL Validierung"""
    with app.app_context():
        validator = NFLResultsValidator()
        validator.run_daily_validation()

def run_weekly_schedule_sync():
    """Wrapper für wöchentlichen Schedule Sync"""
    with app.app_context():
        # Hier würde der NFL Schedule Sync laufen
        logger.info("🔄 Running weekly NFL schedule sync...")

# ===== MAIN =====

if __name__ == '__main__':
    # Registriere Pick API Endpoints
    register_pick_endpoints(app)
    
    # Initialisiere Datenbank
    initialize_database()
    
    # Starte Scheduler
    setup_scheduler()
    
    # Starte Flask App
    logger.info("🚀 Starting NFL PickEm 2025 App...")
    app.run(host='0.0.0.0', port=5000, debug=True)

