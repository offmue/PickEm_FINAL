#!/usr/bin/env python3
"""
App Launcher für NFL PickEm 2025 auf Render.com
Initialisiert Datenbank und startet die App
"""

import os
import sys
import logging
from app import app, initialize_database

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Hauptfunktion für App-Start auf Render.com"""
    logger.info("🚀 Starting NFL PickEm 2025 App Launcher...")
    
    try:
        # Datenbank initialisieren
        logger.info("🔧 Initializing database...")
        initialize_database()
        
        # Port von Umgebungsvariable oder Default
        port = int(os.environ.get('PORT', 5000))
        
        # App starten
        logger.info(f"🌐 Starting app on port {port}...")
        app.run(host='0.0.0.0', port=port, debug=False)
        
    except Exception as e:
        logger.error(f"❌ Error starting app: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()

