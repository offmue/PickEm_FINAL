# NFL PickEm 2025 - Schlankes Live Deployment

## 🚀 SCHNELL-DEPLOYMENT

### 1. Render.com Setup
- Repository: Dieses ZIP hochladen
- Build Command: `pip install -r requirements.txt`
- Start Command: `python3 app_launcher.py`
- Environment: Python 3.11

### 2. Automatische Initialisierung
- Datenbank wird automatisch erstellt
- Teams und Spiele werden von ESPN geladen
- Game Validator startet automatisch

### 3. Test-Accounts (automatisch erstellt)
- admin / admin123
- manuel / manuel123
- daniel / daniel123
- raff / raff123
- haunschi / haunschi123

## ✅ FEATURES ENTHALTEN
- Dashboard mit 4 Karten
- Picks mit Regelbox
- Eliminierungslogik
- ESPN-Integration
- Game Validator
- Responsive Design

## 📁 DATEIEN (nur 9 Dateien!)
- app.py (Haupt-App)
- app_launcher.py (Render-Starter)
- game_validator.py (Auto-Validierung)
- database_sync_api.py (ESPN-Sync)
- requirements.txt (Dependencies)
- templates/index.html (Frontend)
- static/app.js (JavaScript)
- static/styles.css (Styling)
- DEPLOYMENT_README.md (diese Datei)

## 🎯 NACH DEPLOYMENT TESTEN
1. Login funktioniert
2. Dashboard zeigt 4 Karten
3. Picks-Section mit Regeln
4. Wochenwechsel funktioniert
5. Team-Auswahl funktioniert

**Alles in 9 Dateien - GitHub-kompatibel!** 🎉

