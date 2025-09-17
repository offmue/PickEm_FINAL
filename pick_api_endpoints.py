#!/usr/bin/env python3
"""
Flask API Endpoints für NFL PickEm 2025 Pick-System
"""

from flask import request, jsonify, session
from pick_logic_backend import PickLogicBackend
from sportsdata_integration import SportsDataAPI
import logging

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def register_pick_endpoints(app):
    """
    Registriert alle Pick-bezogenen API Endpoints
    
    Args:
        app: Flask App Instanz
    """
    
    pick_logic = PickLogicBackend()
    sportsdata_api = SportsDataAPI()
    
    @app.route('/api/current-week', methods=['GET'])
    def get_current_week():
        """API Endpoint: Aktuelle NFL Woche"""
        try:
            current_week = sportsdata_api.get_current_week()
            return jsonify({
                'success': True,
                'current_week': current_week
            })
        except Exception as e:
            logger.error(f"Error getting current week: {e}")
            return jsonify({
                'success': False,
                'message': 'Fehler beim Laden der aktuellen Woche'
            }), 500
    
    @app.route('/api/picks/create', methods=['POST'])
    def create_pick():
        """API Endpoint: Pick erstellen oder ändern"""
        try:
            # Session-Check
            if 'user_id' not in session:
                return jsonify({
                    'success': False,
                    'message': 'Nicht eingeloggt'
                }), 401
            
            data = request.get_json()
            user_id = session['user_id']
            match_id = data.get('match_id')
            chosen_team_id = data.get('chosen_team_id')
            
            if not all([match_id, chosen_team_id]):
                return jsonify({
                    'success': False,
                    'message': 'Fehlende Parameter'
                }), 400
            
            # Pick erstellen/ändern
            result = pick_logic.create_or_update_pick(user_id, match_id, chosen_team_id)
            
            if result['success']:
                return jsonify(result)
            else:
                return jsonify(result), 400
                
        except Exception as e:
            logger.error(f"Error creating pick: {e}")
            return jsonify({
                'success': False,
                'message': 'Fehler beim Speichern des Picks'
            }), 500
    
    @app.route('/api/picks/user/<int:week>', methods=['GET'])
    def get_user_pick_for_week(week):
        """API Endpoint: User Pick für bestimmte Woche"""
        try:
            # Session-Check
            if 'user_id' not in session:
                return jsonify({
                    'success': False,
                    'message': 'Nicht eingeloggt'
                }), 401
            
            user_id = session['user_id']
            pick_info = pick_logic.get_user_pick_for_week(user_id, week)
            
            return jsonify({
                'success': True,
                'pick': pick_info
            })
            
        except Exception as e:
            logger.error(f"Error getting user pick: {e}")
            return jsonify({
                'success': False,
                'message': 'Fehler beim Laden des Picks'
            }), 500
    
    @app.route('/api/teams/available/<int:week>', methods=['GET'])
    def get_available_teams(week):
        """API Endpoint: Verfügbare Teams für User in bestimmter Woche"""
        try:
            # Session-Check
            if 'user_id' not in session:
                return jsonify({
                    'success': False,
                    'message': 'Nicht eingeloggt'
                }), 401
            
            user_id = session['user_id']
            team_availability = pick_logic.get_available_teams_for_user(user_id, week)
            
            return jsonify({
                'success': True,
                'teams': team_availability
            })
            
        except Exception as e:
            logger.error(f"Error getting available teams: {e}")
            return jsonify({
                'success': False,
                'message': 'Fehler beim Laden der verfügbaren Teams'
            }), 500
    
    @app.route('/api/matches/<int:week>', methods=['GET'])
    def get_matches_for_week(week):
        """API Endpoint: Alle Matches für bestimmte Woche mit Pick-Status"""
        try:
            from app import Match, Team
            
            # Session-Check für Pick-Status
            user_id = session.get('user_id')
            
            # Matches für diese Woche laden
            matches = Match.query.filter_by(week=week).all()
            
            matches_data = []
            user_pick = None
            
            if user_id:
                user_pick = pick_logic.get_user_pick_for_week(user_id, week)
            
            for match in matches:
                home_team = Team.query.get(match.home_team_id)
                away_team = Team.query.get(match.away_team_id)
                
                # Prüfe ob Spiel gestartet
                is_started = pick_logic._is_game_started(match)
                
                # Prüfe ob User dieses Match gepickt hat
                is_user_pick = user_pick and user_pick['match_id'] == match.id
                
                match_data = {
                    'id': match.id,
                    'week': match.week,
                    'home_team': {
                        'id': home_team.id,
                        'name': home_team.name,
                        'abbreviation': home_team.abbreviation,
                        'logo_url': home_team.logo_url
                    },
                    'away_team': {
                        'id': away_team.id,
                        'name': away_team.name,
                        'abbreviation': away_team.abbreviation,
                        'logo_url': away_team.logo_url
                    },
                    'start_time': match.start_time.isoformat(),
                    'is_started': is_started,
                    'is_completed': match.is_completed,
                    'is_user_pick': is_user_pick,
                    'can_pick': not is_started and (not user_pick or is_user_pick),
                    'home_score': match.home_score,
                    'away_score': match.away_score,
                    'winner_team_id': match.winner_team_id
                }
                
                # Wenn User dieses Match gepickt hat, füge Pick-Info hinzu
                if is_user_pick:
                    match_data['user_chosen_team_id'] = user_pick['chosen_team']['id']
                
                matches_data.append(match_data)
            
            return jsonify({
                'success': True,
                'matches': matches_data,
                'user_pick': user_pick
            })
            
        except Exception as e:
            logger.error(f"Error getting matches for week {week}: {e}")
            return jsonify({
                'success': False,
                'message': 'Fehler beim Laden der Spiele'
            }), 500
    
    @app.route('/api/picks/validate', methods=['POST'])
    def validate_pick():
        """API Endpoint: Pick-Validierung ohne Speichern"""
        try:
            # Session-Check
            if 'user_id' not in session:
                return jsonify({
                    'success': False,
                    'message': 'Nicht eingeloggt'
                }), 401
            
            data = request.get_json()
            user_id = session['user_id']
            match_id = data.get('match_id')
            chosen_team_id = data.get('chosen_team_id')
            
            if not all([match_id, chosen_team_id]):
                return jsonify({
                    'success': False,
                    'message': 'Fehlende Parameter'
                }), 400
            
            # Nur Validierung, kein Speichern
            validation_result = pick_logic._validate_pick_request(user_id, match_id, chosen_team_id)
            
            return jsonify({
                'success': validation_result.get('valid', False),
                'message': validation_result.get('message', 'Validierung erfolgreich'),
                'can_pick': validation_result.get('valid', False)
            })
            
        except Exception as e:
            logger.error(f"Error validating pick: {e}")
            return jsonify({
                'success': False,
                'message': 'Fehler bei der Pick-Validierung'
            }), 500
    
    logger.info("✅ Pick API endpoints registered successfully")

# Beispiel für Integration in main app.py:
"""
from pick_api_endpoints import register_pick_endpoints

# In app.py nach Flask app creation:
register_pick_endpoints(app)
"""

