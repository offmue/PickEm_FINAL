"""
NFL PickEm 2025 App Launcher for Render.com
Handles initialization and startup for production deployment
"""

import logging
import os
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main launcher function"""
    try:
        logger.info("🚀 Starting NFL PickEm 2025 App Launcher...")
        
        # Import and start the Flask app
        from app import app, initialize_database
        
        # Initialize database in app context
        with app.app_context():
            logger.info("🔧 Initializing database...")
            if initialize_database():
                logger.info("✅ Database initialization completed")
            else:
                logger.warning("⚠️ Database initialization had issues, but continuing...")
        
        # Get port from environment
        port = int(os.environ.get('PORT', 10000))
        logger.info(f"🌐 Starting app on port {port}...")
        
        # Start the Flask app
        app.run(
            host='0.0.0.0',
            port=port,
            debug=False,
            threaded=True
        )
        
    except Exception as e:
        logger.error(f"❌ Error starting app: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()

