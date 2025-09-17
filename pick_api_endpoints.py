"""
Pick API Endpoints for NFL PickEm 2025
Additional API endpoints for pick functionality
"""

import logging
from flask import jsonify, session, request
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

def register_pick_endpoints(app):
    """Register additional pick-related API endpoints"""
    
    @app.route('/api/picks/user/<int:week>')
    def get_user_pick_for_week(week):
        """Get user's pick for a specific week"""
        try:
            if 'user_id' not in session:
                return jsonify({'success': False, 'message': 'Not logged in'})
            
            user_id = session['user_id']
            
            # Import models within app context
            from app import Pick, Match
            
            # Get user's pick for this week
            pick = Pick.query.join(Match).filter(
                Pick.user_id == user_id,
                Match.week == week
            ).first()
            
            if pick:
                return jsonify({
                    'success': True,
                    'pick': {
                        'match_id': pick.match_id,
                        'chosen_team_id': pick.chosen_team_id,
                        'chosen_team_name': pick.chosen_team.name
                    }
                })
            else:
                return jsonify({'success': True, 'pick': None})
                
        except Exception as e:
            logger.error(f"❌ Error getting user pick: {e}")
            return jsonify({'success': False, 'pick': None})
    
    @app.route('/api/teams/available/<int:week>')
    def get_available_teams(week):
        """Get teams available for picking in a specific week"""
        try:
            if 'user_id' not in session:
                return jsonify({'success': False, 'message': 'Not logged in'})
            
            user_id = session['user_id']
            
            # Import models within app context
            from app import Team, TeamWinnerUsage, TeamLoserUsage
            
            # Get all teams
            all_teams = Team.query.all()
            
            # Get user's team usage
            winner_usage = TeamWinnerUsage.query.filter_by(user_id=user_id).all()
            loser_usage = TeamLoserUsage.query.filter_by(user_id=user_id).all()
            
            used_winners = [usage.team_id for usage in winner_usage]
            used_losers = [usage.team_id for usage in loser_usage]
            
            available_teams = []
            for team in all_teams:
                winner_count = used_winners.count(team.id)
                loser_count = used_losers.count(team.id)
                
                available_teams.append({
                    'id': team.id,
                    'name': team.name,
                    'abbreviation': team.abbreviation,
                    'logo_url': team.logo_url,
                    'can_pick_as_winner': winner_count < 2,
                    'can_pick_as_loser': loser_count < 1,
                    'winner_usage_count': winner_count,
                    'loser_usage_count': loser_count
                })
            
            return jsonify({'success': True, 'teams': available_teams})
            
        except Exception as e:
            logger.error(f"❌ Error getting available teams: {e}")
            return jsonify({'success': False, 'teams': []})
    
    @app.route('/api/picks/validate', methods=['POST'])
    def validate_pick():
        """Validate a pick before saving"""
        try:
            if 'user_id' not in session:
                return jsonify({'success': False, 'message': 'Not logged in'})
            
            data = request.get_json()
            user_id = session['user_id']
            match_id = data.get('match_id')
            chosen_team_id = data.get('chosen_team_id')
            
            # Import models within app context
            from app import Match, Team, TeamWinnerUsage, TeamLoserUsage
            
            # Validate match exists
            match = Match.query.get(match_id)
            if not match:
                return jsonify({'success': False, 'message': 'Match not found'})
            
            # Check if game has started
            now = datetime.now(timezone.utc)
            if match.start_time and match.start_time <= now:
                return jsonify({'success': False, 'message': 'Game has already started'})
            
            # Validate chosen team
            chosen_team = Team.query.get(chosen_team_id)
            if not chosen_team:
                return jsonify({'success': False, 'message': 'Team not found'})
            
            # Check if chosen team is in this match
            if chosen_team_id not in [match.home_team_id, match.away_team_id]:
                return jsonify({'success': False, 'message': 'Team not in this match'})
            
            # Check team usage limits
            winner_usage_count = TeamWinnerUsage.query.filter_by(
                user_id=user_id, 
                team_id=chosen_team_id
            ).count()
            
            if winner_usage_count >= 2:
                return jsonify({'success': False, 'message': f'{chosen_team.name} already used as winner 2 times'})
            
            # Check loser team usage
            loser_team_id = match.away_team_id if chosen_team_id == match.home_team_id else match.home_team_id
            loser_usage_count = TeamLoserUsage.query.filter_by(
                user_id=user_id,
                team_id=loser_team_id
            ).count()
            
            if loser_usage_count >= 1:
                loser_team = Team.query.get(loser_team_id)
                return jsonify({'success': False, 'message': f'{loser_team.name} already used as loser'})
            
            return jsonify({'success': True, 'message': 'Pick is valid'})
            
        except Exception as e:
            logger.error(f"❌ Error validating pick: {e}")
            return jsonify({'success': False, 'message': 'Validation failed'})
    
    logger.info("✅ Pick API endpoints registered successfully")

