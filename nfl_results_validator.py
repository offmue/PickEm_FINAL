#!/usr/bin/env python3
"""
NFL Results Validator für NFL PickEm 2025
Täglicher Sync um 07:00 für echte NFL Ergebnisse und Punkte-Validierung
"""

from sportsdata_integration import SportsDataAPI
from datetime import datetime
import logging
from typing import List, Dict

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NFLResultsValidator:
    def __init__(self):
        """NFL Results Validator mit SportsData.io Integration"""
        self.sportsdata_api = SportsDataAPI()
    
    def run_daily_validation(self):
        """
        Hauptfunktion für täglichen NFL Ergebnis-Sync
        Läuft jeden Tag um 07:00 Uhr
        """
        logger.info("🏈 Starting daily NFL results validation...")
        
        try:
            # Import hier um zirkuläre Imports zu vermeiden
            from app import app, db, Team, Match, Pick, User, TeamWinnerUsage, TeamLoserUsage
            
            with app.app_context():
                # 1. Aktuelle Woche ermitteln
                current_week = self.sportsdata_api.get_current_week()
                logger.info(f"📅 Current NFL Week: {current_week}")
                
                # 2. Ergebnisse für abgeschlossene Wochen validieren
                self._validate_completed_weeks(current_week)
                
                # 3. Punkte für alle Spieler neu berechnen
                self._recalculate_all_scores()
                
                logger.info("✅ Daily NFL results validation completed!")
                
        except Exception as e:
            logger.error(f"❌ Error in daily validation: {e}")
            raise
    
    def _validate_completed_weeks(self, current_week: int):
        """
        Validiert alle Wochen die abgeschlossen sein sollten
        
        Args:
            current_week: Aktuelle NFL Woche
        """
        from app import db, Team, Match
        
        # Validiere alle Wochen bis zur aktuellen Woche - 1
        # (aktuelle Woche könnte noch laufende Spiele haben)
        weeks_to_validate = list(range(1, current_week))
        
        for week in weeks_to_validate:
            logger.info(f"🔍 Validating Week {week}...")
            
            # SportsData.io Ergebnisse für diese Woche laden
            week_scores = self.sportsdata_api.get_week_scores(week)
            processed_results = self.sportsdata_api.process_game_results(week_scores)
            
            # Matches in Datenbank updaten
            for result in processed_results:
                self._update_match_result(result)
            
            db.session.commit()
            logger.info(f"✅ Week {week} validation completed")
    
    def _update_match_result(self, result: Dict):
        """
        Updated ein Match mit echten NFL Ergebnissen
        
        Args:
            result: Verarbeitetes Spielergebnis von SportsData.io
        """
        from app import db, Team, Match
        
        # Teams finden basierend auf Abkürzungen
        home_team = Team.query.filter_by(abbreviation=result['home_team_abbr']).first()
        away_team = Team.query.filter_by(abbreviation=result['away_team_abbr']).first()
        
        if not home_team or not away_team:
            logger.warning(f"⚠️ Teams not found: {result['home_team_abbr']} vs {result['away_team_abbr']}")
            return
        
        # Match finden
        match = Match.query.filter_by(
            week=result['week'],
            home_team_id=home_team.id,
            away_team_id=away_team.id
        ).first()
        
        if not match:
            logger.warning(f"⚠️ Match not found: Week {result['week']} - {result['home_team_abbr']} vs {result['away_team_abbr']}")
            return
        
        # Match bereits completed? Dann skip
        if match.is_completed:
            logger.debug(f"⏭️ Match already completed: Week {result['week']} - {result['home_team_abbr']} vs {result['away_team_abbr']}")
            return
        
        # Gewinner-Team finden
        winner_team = None
        if result['winner_team_abbr']:
            winner_team = Team.query.filter_by(abbreviation=result['winner_team_abbr']).first()
        
        # Match updaten
        match.home_score = result['home_score']
        match.away_score = result['away_score']
        match.winner_team_id = winner_team.id if winner_team else None
        match.is_completed = result['is_completed']
        match.status = 'completed' if result['is_completed'] else 'in_progress'
        match.updated_at = datetime.utcnow()
        
        logger.info(f"🏆 Updated match: Week {result['week']} - {result['winner_team_abbr']} wins ({result['home_team_abbr']} {result['home_score']}-{result['away_score']} {result['away_team_abbr']})")
        
        # Picks für dieses Match validieren
        self._validate_picks_for_match(match)
    
    def _validate_picks_for_match(self, match):
        """
        Validiert alle Picks für ein abgeschlossenes Match
        
        Args:
            match: Abgeschlossenes Match-Objekt
        """
        from app import db, Pick, User, TeamWinnerUsage, TeamLoserUsage
        
        if not match.is_completed or not match.winner_team_id:
            return
        
        # Alle Picks für dieses Match finden
        picks = Pick.query.filter_by(match_id=match.id).all()
        
        for pick in picks:
            user = User.query.get(pick.user_id)
            chosen_team = pick.chosen_team
            
            # Punkte vergeben basierend auf korrektem Tipp
            if pick.chosen_team_id == match.winner_team_id:
                # Richtiger Tipp → +1 Punkt
                pick.points_earned = 1
                pick.is_correct = True
                logger.info(f"✅ Correct pick: {user.username} chose {chosen_team.name} (Winner)")
            else:
                # Falscher Tipp → 0 Punkte
                pick.points_earned = 0
                pick.is_correct = False
                logger.info(f"❌ Incorrect pick: {user.username} chose {chosen_team.name} (Loser)")
            
            # Team Usage aktualisieren
            self._update_team_usage_for_pick(pick, match)
        
        db.session.commit()
    
    def _update_team_usage_for_pick(self, pick, match):
        """
        Aktualisiert Team Usage basierend auf validiertem Pick
        
        Args:
            pick: Pick-Objekt
            match: Match-Objekt
        """
        from app import db, TeamWinnerUsage, TeamLoserUsage
        
        if not match.is_completed or not match.winner_team_id:
            return
        
        user_id = pick.user_id
        chosen_team_id = pick.chosen_team_id
        
        # Bestimme welches Team als Verlierer gilt
        if match.home_team_id == match.winner_team_id:
            loser_team_id = match.away_team_id
        else:
            loser_team_id = match.home_team_id
        
        # Winner Usage: Gewähltes Team als Gewinner verwendet
        winner_usage = TeamWinnerUsage.query.filter_by(
            user_id=user_id,
            team_id=chosen_team_id
        ).first()
        
        if not winner_usage:
            winner_usage = TeamWinnerUsage(user_id=user_id, team_id=chosen_team_id)
            db.session.add(winner_usage)
            logger.info(f"📈 Added winner usage: User {user_id} used Team {chosen_team_id} as winner")
        
        # Loser Usage: Das andere Team als Verlierer verwendet
        loser_usage = TeamLoserUsage.query.filter_by(
            user_id=user_id,
            team_id=loser_team_id
        ).first()
        
        if not loser_usage:
            loser_usage = TeamLoserUsage(user_id=user_id, team_id=loser_team_id)
            db.session.add(loser_usage)
            logger.info(f"📉 Added loser usage: User {user_id} used Team {loser_team_id} as loser")
    
    def _recalculate_all_scores(self):
        """
        Berechnet alle Spieler-Scores neu basierend auf validierten Picks
        """
        from app import db, User, Pick
        
        logger.info("🧮 Recalculating all player scores...")
        
        users = User.query.all()
        
        for user in users:
            # Alle korrekten Picks für diesen User zählen
            correct_picks = Pick.query.filter_by(
                user_id=user.id,
                is_correct=True
            ).count()
            
            # Score in User-Objekt speichern (falls Feld existiert)
            # Oder über get_score() Methode berechnen lassen
            total_score = user.get_score()
            
            logger.info(f"📊 {user.username}: {total_score} points ({correct_picks} correct picks)")
        
        logger.info("✅ Score recalculation completed")

def run_daily_nfl_validation():
    """Hauptfunktion für täglichen NFL Validation Sync"""
    validator = NFLResultsValidator()
    validator.run_daily_validation()

if __name__ == '__main__':
    run_daily_nfl_validation()

