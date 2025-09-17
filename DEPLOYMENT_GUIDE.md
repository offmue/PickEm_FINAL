# NFL PickEm 2025 - Deployment Guide

## 🚀 Vollständiges NFL PickEm System mit SportsData.io Integration

### ✅ Features
- **SportsData.io Integration** für echte NFL Ergebnisse
- **Automatische Punkte-Berechnung** basierend auf echten Spielergebnissen
- **Team Usage Validierung** (1x Verlierer, 2x Gewinner pro Saison)
- **Live Pick-System** mit Spiel-Status Prüfung
- **NFL Team-Logos** (ESPN CDN, hochqualitativ)
- **Responsive Frontend** mit professionellem Design
- **Automatische Scheduler** für tägliche/wöchentliche Syncs

### 📦 Deployment auf Render.com

#### 1. Repository Setup
```bash
# Alle Dateien in Git Repository hochladen
git add .
git commit -m "NFL PickEm 2025 Complete System"
git push origin main
```

#### 2. Render.com Konfiguration
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python app_launcher.py`
- **Environment**: Python 3.11+

#### 3. Umgebungsvariablen (Optional)
```
SPORTSDATA_API_KEY=your_api_key_here
SECRET_KEY=your_secret_key_here
```

### 🔧 Lokale Entwicklung

#### Installation
```bash
pip install -r requirements.txt
```

#### Start
```bash
python app.py
```

#### Zugriff
- **URL**: http://localhost:5000
- **Test-User**: 
  - Manuel / Manuel1
  - Daniel / Daniel1
  - Raff / Raff1
  - Haunschi / Haunschi1

### 🏈 System-Architektur

#### Backend-Module
- **app.py**: Haupt-Flask-App mit allen Endpoints
- **sportsdata_integration.py**: SportsData.io API Client
- **pick_logic_backend.py**: Pick-Logik und Team Usage Validierung
- **pick_api_endpoints.py**: API Endpoints für Pick-System
- **nfl_results_validator.py**: Tägliche NFL Ergebnis-Validierung
- **nfl_team_logos.py**: Team-Logo Management

#### Frontend-Module
- **templates/index.html**: Haupt-HTML Template
- **static/picks_frontend.js**: JavaScript für Picks-Funktionalität
- **static/picks_frontend.css**: CSS für Picks-Design

#### Datenbank-Modelle
- **User**: Spieler-Accounts
- **Team**: NFL Teams mit Logos
- **Match**: NFL Spiele mit Ergebnissen
- **Pick**: Spieler-Tipps
- **TeamWinnerUsage**: Gewinner-Team Usage Tracking
- **TeamLoserUsage**: Verlierer-Team Usage Tracking

### ⚙️ Automatische Prozesse

#### Täglicher Sync (07:00 Wiener Zeit)
- Lädt NFL Ergebnisse von SportsData.io
- Validiert alle Spieler-Picks
- Berechnet Punkte automatisch
- Aktualisiert Team Usage

#### Wöchentlicher Sync (Dienstag 07:00 Wiener Zeit)
- Lädt NFL Schedule Updates
- Fügt neue Spiele hinzu
- Verhindert Duplikate

### 🎮 Spielregeln

#### Pick-System
1. **Ein Pick pro Woche**: Spieler wählt einen Gewinner
2. **Team Usage Limits**: 
   - Jedes Team max. 2x als Gewinner
   - Jedes Team max. 1x als Verlierer
3. **Pick-Deadline**: Bis Spielbeginn änderbar
4. **Punkte**: 1 Punkt für richtigen Tipp

#### Eliminierungslogik
- Teams werden nach Usage-Limits gesperrt
- Visuelle Anzeige verfügbarer Teams
- Automatische Validierung vor Pick-Speicherung

### 🔍 API Endpoints

#### Authentifizierung
- `POST /api/auth/login` - User Login
- `POST /api/auth/logout` - User Logout
- `GET /api/auth/session` - Session Check

#### Picks
- `GET /api/current-week` - Aktuelle NFL Woche
- `POST /api/picks/create` - Pick erstellen/ändern
- `GET /api/picks/user/<week>` - User Pick für Woche
- `GET /api/teams/available/<week>` - Verfügbare Teams
- `GET /api/matches/<week>` - Spiele mit Pick-Status

#### Leaderboard
- `GET /api/leaderboard` - Rangliste aller Spieler
- `GET /api/user/team-usage` - Team Usage für User

### 🐛 Troubleshooting

#### Häufige Probleme
1. **SportsData.io API**: Ohne API-Key werden Mock-Daten verwendet
2. **Team-Logos**: ESPN CDN sollte immer verfügbar sein
3. **Scheduler**: Läuft nur in Production (nicht Debug-Modus)
4. **Datenbank**: SQLite wird automatisch erstellt

#### Logs prüfen
```bash
# Render.com Logs
# Dashboard → Service → Logs

# Lokal
python app.py  # Logs in Console
```

### 📈 Monitoring

#### Wichtige Metriken
- **User-Logins**: Session-Management
- **Pick-Erfolgsrate**: API Response Times
- **NFL Sync-Status**: Tägliche/Wöchentliche Updates
- **Team Usage**: Verfügbarkeits-Tracking

### 🔒 Sicherheit

#### Implementierte Maßnahmen
- **Session-Management**: Flask Sessions
- **Password-Hashing**: Werkzeug Security
- **Input-Validierung**: API Parameter Checks
- **CORS**: Cross-Origin Request Handling

### 🎯 Nächste Schritte

#### Mögliche Erweiterungen
1. **Email-Benachrichtigungen** für Pick-Deadlines
2. **Push-Notifications** für Spielergebnisse
3. **Erweiterte Statistiken** und Analytics
4. **Mobile App** (React Native)
5. **Social Features** (Chat, Kommentare)

---

## 🏆 Das System ist bereit für Live-Betrieb!

**Deployment-Status**: ✅ Production Ready
**Testing**: ✅ Vollständig getestet
**Documentation**: ✅ Vollständig dokumentiert

