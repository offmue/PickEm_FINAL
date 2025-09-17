#!/usr/bin/env python3
"""
NFL PickEm 2025 - Render.com Launcher
Startet die Flask-Anwendung für Render.com Deployment
"""

import os
import sys
from app import app

if __name__ == '__main__':
    # Render.com Port aus Umgebungsvariable
    port = int(os.environ.get('PORT', 5000))
    
    # Produktions-Modus für Render.com
    os.environ['ENABLE_VALIDATOR'] = 'true'
    
    print(f"🚀 Starting NFL PickEm 2025 on port {port}")
    print("🎯 Game Validator: ENABLED (Production Mode)")
    
    # Flask-App starten
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False  # Produktions-Modus
    )

