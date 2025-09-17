#!/usr/bin/env python3
"""
SportsData.io Integration für NFL PickEm 2025
Lädt echte NFL Ergebnisse und validiert Spieler-Picks
"""

import requests
import os
from datetime import datetime, timedelta
import pytz
import logging
from typing import Dict, List, Optional

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SportsDataAPI:
    def __init__(self, api_key: str = None):
        """
        SportsData.io API Client
        
        Args:
            api_key: SportsData.io API Key (falls nicht gesetzt, wird Umgebungsvariable verwendet)
        """
        self.api_key = api_key or os.environ.get('SPORTSDATA_API_KEY')
        self.base_url = "https://api.sportsdata.io/v3/nfl"
        self.vienna_tz = pytz.timezone('Europe/Vienna')
        
        if not self.api_key:
            logger.warning("⚠️ No SportsData.io API key found. Using mock data for development.")
            self.use_mock_data = True
        else:
            self.use_mock_data = False
    
    def get_current_week(self) -> int:
        """
        Ermittelt die aktuelle NFL Woche basierend auf dem Datum
        
        Returns:
            int: Aktuelle NFL Woche (1-18)
        """
        try:
            if self.use_mock_data:
                return self._get_mock_current_week()
            
            # SportsData.io API Call für aktuelle Woche
            url = f"{self.base_url}/scores/json/CurrentWeek"
            headers = {"Ocp-Apim-Subscription-Key": self.api_key}
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            current_week = response.json()
            logger.info(f"📅 Current NFL Week from SportsData.io: {current_week}")
            
            return int(current_week)
            
        except Exception as e:
            logger.error(f"❌ Error getting current week: {e}")
            # Fallback: Berechne basierend auf Datum
            return self._calculate_week_from_date()
    
    def _get_mock_current_week(self) -> int:
        """Mock-Daten für Entwicklung"""
        # Simuliere dass wir in Woche 3 sind (Woche 1&2 abgeschlossen)
        return 3
    
    def _calculate_week_from_date(self) -> int:
        """
        Fallback: Berechne NFL Woche basierend auf aktuellem Datum
        NFL Saison 2025 startet ca. 8. September 2025
        """
        season_start = datetime(2025, 9, 8)  # Ungefährer NFL Season Start
        now = datetime.now()
        
        if now < season_start:
            return 1
        
        days_since_start = (now - season_start).days
        week = min(18, max(1, (days_since_start // 7) + 1))
        
        logger.info(f"📅 Calculated current week from date: {week}")
        return week
    
    def get_week_scores(self, week: int, season: int = 2025) -> List[Dict]:
        """
        Lädt alle Spielergebnisse für eine bestimmte Woche
        
        Args:
            week: NFL Woche (1-18)
            season: NFL Saison (2025)
            
        Returns:
            List[Dict]: Liste der Spielergebnisse
        """
        try:
            if self.use_mock_data:
                return self._get_mock_week_scores(week)
            
            # SportsData.io API Call für Wochenergebnisse
            url = f"{self.base_url}/scores/json/ScoresByWeek/{season}/{week}"
            headers = {"Ocp-Apim-Subscription-Key": self.api_key}
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            scores = response.json()
            logger.info(f"📊 Retrieved {len(scores)} games for Week {week}")
            
            return scores
            
        except Exception as e:
            logger.error(f"❌ Error getting week {week} scores: {e}")
            return self._get_mock_week_scores(week)
    
    def _get_mock_week_scores(self, week: int) -> List[Dict]:
        """Mock-Daten für Entwicklung und Testing"""
        mock_scores = {
            1: [
                {
                    "GameKey": "202509080001",
                    "Week": 1,
                    "HomeTeam": "ATL",
                    "AwayTeam": "TB", 
                    "HomeScore": 24,
                    "AwayScore": 17,
                    "IsGameOver": True,
                    "DateTime": "2025-09-08T19:00:00"
                },
                {
                    "GameKey": "202509080002", 
                    "Week": 1,
                    "HomeTeam": "DEN",
                    "AwayTeam": "TEN",
                    "HomeScore": 27,
                    "AwayScore": 14,
                    "IsGameOver": True,
                    "DateTime": "2025-09-08T19:00:00"
                },
                {
                    "GameKey": "202509080003",
                    "Week": 1, 
                    "HomeTeam": "CIN",
                    "AwayTeam": "CLE",
                    "HomeScore": 21,
                    "AwayScore": 14,
                    "IsGameOver": True,
                    "DateTime": "2025-09-08T19:00:00"
                },
                {
                    "GameKey": "202509080004",
                    "Week": 1,
                    "HomeTeam": "WAS", 
                    "AwayTeam": "NYG",
                    "HomeScore": 28,
                    "AwayScore": 21,
                    "IsGameOver": True,
                    "DateTime": "2025-09-08T19:00:00"
                }
            ],
            2: [
                {
                    "GameKey": "202509150001",
                    "Week": 2,
                    "HomeTeam": "DAL",
                    "AwayTeam": "NYG",
                    "HomeScore": 31,
                    "AwayScore": 17,
                    "IsGameOver": True,
                    "DateTime": "2025-09-15T19:00:00"
                },
                {
                    "GameKey": "202509150002",
                    "Week": 2,
                    "HomeTeam": "KC",
                    "AwayTeam": "PHI", 
                    "HomeScore": 24,
                    "AwayScore": 21,
                    "IsGameOver": True,
                    "DateTime": "2025-09-15T19:00:00"
                },
                {
                    "GameKey": "202509150003",
                    "Week": 2,
                    "HomeTeam": "BUF",
                    "AwayTeam": "NYJ",
                    "HomeScore": 28,
                    "AwayScore": 14,
                    "IsGameOver": True,
                    "DateTime": "2025-09-15T19:00:00"
                }
            ],
            3: [
                {
                    "GameKey": "202509220001",
                    "Week": 3,
                    "HomeTeam": "TB",
                    "AwayTeam": "ATL",
                    "HomeScore": None,
                    "AwayScore": None,
                    "IsGameOver": False,
                    "DateTime": "2025-09-22T19:00:00"
                },
                {
                    "GameKey": "202509220002",
                    "Week": 3,
                    "HomeTeam": "SF",
                    "AwayTeam": "LAR",
                    "HomeScore": None,
                    "AwayScore": None,
                    "IsGameOver": False,
                    "DateTime": "2025-09-22T19:00:00"
                }
            ]
        }
        
        return mock_scores.get(week, [])
    
    def process_game_results(self, scores: List[Dict]) -> List[Dict]:
        """
        Verarbeitet SportsData.io Ergebnisse für unsere Datenbank
        
        Args:
            scores: Rohe SportsData.io Ergebnisse
            
        Returns:
            List[Dict]: Verarbeitete Ergebnisse für Datenbank-Update
        """
        processed_results = []
        
        for game in scores:
            if not game.get('IsGameOver', False):
                continue  # Nur abgeschlossene Spiele verarbeiten
                
            home_team = game.get('HomeTeam')
            away_team = game.get('AwayTeam')
            home_score = game.get('HomeScore', 0)
            away_score = game.get('AwayScore', 0)
            
            # Gewinner ermitteln
            if home_score > away_score:
                winner_team = home_team
            elif away_score > home_score:
                winner_team = away_team
            else:
                winner_team = None  # Unentschieden (sehr selten in NFL)
            
            processed_result = {
                'week': game.get('Week'),
                'home_team_abbr': home_team,
                'away_team_abbr': away_team,
                'home_score': home_score,
                'away_score': away_score,
                'winner_team_abbr': winner_team,
                'is_completed': True,
                'game_key': game.get('GameKey')
            }
            
            processed_results.append(processed_result)
            logger.info(f"✅ Processed: Week {game.get('Week')} - {winner_team} wins ({home_team} {home_score}-{away_score} {away_team})")
        
        return processed_results

def test_sportsdata_api():
    """Test-Funktion für SportsData.io API"""
    api = SportsDataAPI()
    
    # Test aktuelle Woche
    current_week = api.get_current_week()
    print(f"Current Week: {current_week}")
    
    # Test Woche 1 Ergebnisse
    week1_scores = api.get_week_scores(1)
    processed = api.process_game_results(week1_scores)
    
    print(f"Week 1 Results: {len(processed)} completed games")
    for result in processed:
        print(f"  {result['winner_team_abbr']} wins: {result['home_team_abbr']} {result['home_score']}-{result['away_score']} {result['away_team_abbr']}")

if __name__ == '__main__':
    test_sportsdata_api()

