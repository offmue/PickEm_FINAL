#!/usr/bin/env python3
"""
Backend Pick-Logik für NFL PickEm 2025
Handles Pick-Erstellung, -Änderung und Team Usage Validierung
"""

from datetime import datetime
import pytz
from typing import Dict, List, Optional, Tuple
import logging

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PickLogicBackend:
    def __init__(self):
        """Backend Pick-Logik Handler"""
        self.vienna_tz = pytz.timezone('Europe/Vienna')
    
    def create_or_update_pick(self, user_id: int, match_id: int, chosen_team_id: int) -> Dict:
        """
        Erstellt oder aktualisiert einen Pick für einen User
        
        Args:
            user_id: ID des Users
            match_id: ID des Matches
            chosen_team_id: ID des gewählten Teams (Gewinner)
            
        Returns:
            Dict: Ergebnis der Pick-Operation
        """
        try:
            from app import db, User, Match, Pick, Team, TeamWinnerUsage, TeamLoserUsage
            
            # 1. Validierungen
            validation_result = self._validate_pick_request(user_id, match_id, chosen_team_id)
            if not validation_result['valid']:
                return validation_result
            
            user = User.query.get(user_id)
            match = Match.query.get(match_id)
            chosen_team = Team.query.get(chosen_team_id)
            
            # 2. Bestimme Verlierer-Team
            if match.home_team_id == chosen_team_id:
                loser_team_id = match.away_team_id
            else:
                loser_team_id = match.home_team_id
            
            # 3. Prüfe ob User bereits einen Pick für diese Woche hat
            existing_pick = Pick.query.filter_by(user_id=user_id).join(Match).filter(Match.week == match.week).first()
            
            if existing_pick:
                # Pick ändern
                result = self._update_existing_pick(existing_pick, match_id, chosen_team_id, loser_team_id)
            else:
                # Neuen Pick erstellen
                result = self._create_new_pick(user_id, match_id, chosen_team_id, loser_team_id)
            
            db.session.commit()
            
            logger.info(f"✅ Pick operation successful: {user.username} chose {chosen_team.name} in Week {match.week}")
            
            return {
                'success': True,
                'message': 'Pick erfolgreich gespeichert',
                'pick_id': result['pick_id'],
                'chosen_team': chosen_team.name,
                'week': match.week
            }
            
        except Exception as e:
            logger.error(f"❌ Error in create_or_update_pick: {e}")
            return {
                'success': False,
                'message': f'Fehler beim Speichern des Picks: {str(e)}'
            }
    
    def _validate_pick_request(self, user_id: int, match_id: int, chosen_team_id: int) -> Dict:
        """
        Validiert eine Pick-Anfrage
        
        Returns:
            Dict: Validierungsergebnis
        """
        from app import User, Match, Team, TeamWinnerUsage, TeamLoserUsage
        
        # User existiert?
        user = User.query.get(user_id)
        if not user:
            return {'valid': False, 'success': False, 'message': 'User nicht gefunden'}
        
        # Match existiert?
        match = Match.query.get(match_id)
        if not match:
            return {'valid': False, 'success': False, 'message': 'Spiel nicht gefunden'}
        
        # Team existiert?
        chosen_team = Team.query.get(chosen_team_id)
        if not chosen_team:
            return {'valid': False, 'success': False, 'message': 'Team nicht gefunden'}
        
        # Team spielt in diesem Match?
        if chosen_team_id not in [match.home_team_id, match.away_team_id]:
            return {'valid': False, 'success': False, 'message': 'Team spielt nicht in diesem Spiel'}
        
        # Spiel bereits gestartet?
        if self._is_game_started(match):
            return {'valid': False, 'success': False, 'message': 'Spiel bereits gestartet - Pick nicht mehr möglich'}
        
        # Team Usage Validierung
        usage_validation = self._validate_team_usage(user_id, match, chosen_team_id)
        if not usage_validation['valid']:
            return usage_validation
        
        return {'valid': True}
    
    def _is_game_started(self, match) -> bool:
        """
        Prüft ob ein Spiel bereits gestartet ist
        
        Args:
            match: Match-Objekt
            
        Returns:
            bool: True wenn Spiel gestartet
        """
        if match.is_completed:
            return True
        
        now = datetime.now(self.vienna_tz)
        game_start = match.start_time.replace(tzinfo=self.vienna_tz)
        
        return now >= game_start
    
    def _validate_team_usage(self, user_id: int, match, chosen_team_id: int) -> Dict:
        """
        Validiert Team Usage Regeln
        
        Args:
            user_id: User ID
            match: Match-Objekt
            chosen_team_id: Gewähltes Team
            
        Returns:
            Dict: Validierungsergebnis
        """
        from app import TeamWinnerUsage, TeamLoserUsage
        
        # Bestimme Verlierer-Team
        if match.home_team_id == chosen_team_id:
            loser_team_id = match.away_team_id
        else:
            loser_team_id = match.home_team_id
        
        # Prüfe Winner Usage (max 2x pro Team)
        winner_usage_count = TeamWinnerUsage.query.filter_by(
            user_id=user_id,
            team_id=chosen_team_id
        ).count()
        
        if winner_usage_count >= 2:
            from app import Team
            team = Team.query.get(chosen_team_id)
            return {
                'valid': False,
                'success': False,
                'message': f'{team.name} bereits 2x als Gewinner verwendet'
            }
        
        # Prüfe Loser Usage (max 1x pro Team)
        loser_usage_count = TeamLoserUsage.query.filter_by(
            user_id=user_id,
            team_id=loser_team_id
        ).count()
        
        if loser_usage_count >= 1:
            from app import Team
            team = Team.query.get(loser_team_id)
            return {
                'valid': False,
                'success': False,
                'message': f'{team.name} bereits 1x als Verlierer verwendet'
            }
        
        return {'valid': True}
    
    def _create_new_pick(self, user_id: int, match_id: int, chosen_team_id: int, loser_team_id: int) -> Dict:
        """
        Erstellt einen neuen Pick
        
        Returns:
            Dict: Ergebnis mit pick_id
        """
        from app import db, Pick, TeamWinnerUsage, TeamLoserUsage
        
        # Neuen Pick erstellen
        new_pick = Pick(
            user_id=user_id,
            match_id=match_id,
            chosen_team_id=chosen_team_id,
            created_at=datetime.utcnow()
        )
        db.session.add(new_pick)
        db.session.flush()  # Um pick.id zu bekommen
        
        # Team Usage erstellen
        self._create_team_usage(user_id, chosen_team_id, loser_team_id)
        
        logger.info(f"➕ Created new pick: User {user_id}, Match {match_id}, Team {chosen_team_id}")
        
        return {'pick_id': new_pick.id}
    
    def _update_existing_pick(self, existing_pick, new_match_id: int, new_chosen_team_id: int, new_loser_team_id: int) -> Dict:
        """
        Aktualisiert einen bestehenden Pick
        
        Returns:
            Dict: Ergebnis mit pick_id
        """
        from app import db, Match
        
        old_match = Match.query.get(existing_pick.match_id)
        old_chosen_team_id = existing_pick.chosen_team_id
        
        # Bestimme altes Verlierer-Team
        if old_match.home_team_id == old_chosen_team_id:
            old_loser_team_id = old_match.away_team_id
        else:
            old_loser_team_id = old_match.home_team_id
        
        # Alte Team Usage entfernen
        self._remove_team_usage(existing_pick.user_id, old_chosen_team_id, old_loser_team_id)
        
        # Pick aktualisieren
        existing_pick.match_id = new_match_id
        existing_pick.chosen_team_id = new_chosen_team_id
        existing_pick.updated_at = datetime.utcnow()
        
        # Neue Team Usage erstellen
        self._create_team_usage(existing_pick.user_id, new_chosen_team_id, new_loser_team_id)
        
        logger.info(f"🔄 Updated pick: User {existing_pick.user_id}, Old Team {old_chosen_team_id} → New Team {new_chosen_team_id}")
        
        return {'pick_id': existing_pick.id}
    
    def _create_team_usage(self, user_id: int, winner_team_id: int, loser_team_id: int):
        """Erstellt Team Usage Einträge"""
        from app import db, TeamWinnerUsage, TeamLoserUsage
        
        # Winner Usage
        winner_usage = TeamWinnerUsage(user_id=user_id, team_id=winner_team_id)
        db.session.add(winner_usage)
        
        # Loser Usage
        loser_usage = TeamLoserUsage(user_id=user_id, team_id=loser_team_id)
        db.session.add(loser_usage)
        
        logger.info(f"📈 Created team usage: User {user_id}, Winner {winner_team_id}, Loser {loser_team_id}")
    
    def _remove_team_usage(self, user_id: int, winner_team_id: int, loser_team_id: int):
        """Entfernt Team Usage Einträge"""
        from app import db, TeamWinnerUsage, TeamLoserUsage
        
        # Winner Usage entfernen
        winner_usage = TeamWinnerUsage.query.filter_by(
            user_id=user_id,
            team_id=winner_team_id
        ).first()
        if winner_usage:
            db.session.delete(winner_usage)
        
        # Loser Usage entfernen
        loser_usage = TeamLoserUsage.query.filter_by(
            user_id=user_id,
            team_id=loser_team_id
        ).first()
        if loser_usage:
            db.session.delete(loser_usage)
        
        logger.info(f"📉 Removed team usage: User {user_id}, Winner {winner_team_id}, Loser {loser_team_id}")
    
    def get_available_teams_for_user(self, user_id: int, week: int) -> Dict:
        """
        Ermittelt verfügbare Teams für einen User in einer bestimmten Woche
        
        Args:
            user_id: User ID
            week: NFL Woche
            
        Returns:
            Dict: Verfügbare Teams und Usage-Informationen
        """
        from app import Team, Match, TeamWinnerUsage, TeamLoserUsage
        
        # Alle Teams
        all_teams = Team.query.all()
        
        # Team Usage für diesen User
        winner_usage = TeamWinnerUsage.query.filter_by(user_id=user_id).all()
        loser_usage = TeamLoserUsage.query.filter_by(user_id=user_id).all()
        
        # Usage Counts erstellen
        winner_counts = {}
        loser_counts = {}
        
        for usage in winner_usage:
            winner_counts[usage.team_id] = winner_counts.get(usage.team_id, 0) + 1
        
        for usage in loser_usage:
            loser_counts[usage.team_id] = loser_counts.get(usage.team_id, 0) + 1
        
        # Spiele dieser Woche
        week_matches = Match.query.filter_by(week=week).all()
        
        team_availability = {}
        
        for team in all_teams:
            winner_count = winner_counts.get(team.id, 0)
            loser_count = loser_counts.get(team.id, 0)
            
            # Prüfe ob Team in dieser Woche spielt
            plays_this_week = any(
                team.id in [match.home_team_id, match.away_team_id]
                for match in week_matches
            )
            
            team_availability[team.id] = {
                'team_name': team.name,
                'team_abbr': team.abbreviation,
                'winner_usage': winner_count,
                'loser_usage': loser_count,
                'can_pick_as_winner': winner_count < 2,
                'can_pick_as_loser': loser_count < 1,
                'plays_this_week': plays_this_week,
                'available': plays_this_week and winner_count < 2
            }
        
        return team_availability
    
    def get_user_pick_for_week(self, user_id: int, week: int) -> Optional[Dict]:
        """
        Holt den Pick eines Users für eine bestimmte Woche
        
        Args:
            user_id: User ID
            week: NFL Woche
            
        Returns:
            Optional[Dict]: Pick-Informationen oder None
        """
        from app import Pick, Match, Team
        
        pick = Pick.query.filter_by(user_id=user_id).join(Match).filter(Match.week == week).first()
        
        if not pick:
            return None
        
        match = Match.query.get(pick.match_id)
        chosen_team = Team.query.get(pick.chosen_team_id)
        home_team = Team.query.get(match.home_team_id)
        away_team = Team.query.get(match.away_team_id)
        
        # Bestimme Verlierer-Team
        if pick.chosen_team_id == match.home_team_id:
            loser_team = away_team
        else:
            loser_team = home_team
        
        return {
            'pick_id': pick.id,
            'match_id': match.id,
            'week': week,
            'chosen_team': {
                'id': chosen_team.id,
                'name': chosen_team.name,
                'abbreviation': chosen_team.abbreviation
            },
            'loser_team': {
                'id': loser_team.id,
                'name': loser_team.name,
                'abbreviation': loser_team.abbreviation
            },
            'match_info': {
                'home_team': home_team.name,
                'away_team': away_team.name,
                'start_time': match.start_time.isoformat(),
                'is_started': self._is_game_started(match),
                'is_completed': match.is_completed
            },
            'can_change': not self._is_game_started(match)
        }

