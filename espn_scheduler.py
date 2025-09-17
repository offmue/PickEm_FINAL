"""
ESPN Scheduler for NFL PickEm 2025
Handles automatic scheduling of ESPN data syncs
"""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

logger = logging.getLogger(__name__)

class ESPNScheduler:
    """Handles automatic scheduling of ESPN data syncs"""
    
    def __init__(self, app, espn_sync, points_calculator):
        self.app = app
        self.espn_sync = espn_sync
        self.points_calculator = points_calculator
        self.scheduler = BackgroundScheduler()
        
        # Vienna timezone for scheduling
        self.vienna_tz = pytz.timezone('Europe/Vienna')
    
    def start_scheduler(self):
        """Start the background scheduler"""
        try:
            logger.info("🚀 Starting ESPN scheduler...")
            
            # Daily sync at 07:00 Vienna time
            self.scheduler.add_job(
                func=self.daily_sync,
                trigger=CronTrigger(
                    hour=7,
                    minute=0,
                    timezone=self.vienna_tz
                ),
                id='daily_espn_sync',
                name='Daily ESPN Data Sync',
                replace_existing=True
            )
            
            # Weekly schedule sync on Tuesday at 07:00 Vienna time
            self.scheduler.add_job(
                func=self.weekly_schedule_sync,
                trigger=CronTrigger(
                    day_of_week='tue',
                    hour=7,
                    minute=0,
                    timezone=self.vienna_tz
                ),
                id='weekly_schedule_sync',
                name='Weekly ESPN Schedule Sync',
                replace_existing=True
            )
            
            # Hourly game validation during game days (Sunday)
            self.scheduler.add_job(
                func=self.hourly_game_validation,
                trigger=CronTrigger(
                    day_of_week='sun',
                    hour='*',
                    minute=0,
                    timezone=self.vienna_tz
                ),
                id='hourly_game_validation',
                name='Hourly Game Validation on Sundays',
                replace_existing=True
            )
            
            self.scheduler.start()
            logger.info("✅ ESPN scheduler started successfully")
            
            # Log scheduled jobs
            jobs = self.scheduler.get_jobs()
            for job in jobs:
                logger.info(f"📅 Scheduled job: {job.name} - {job.trigger}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error starting scheduler: {e}")
            return False
    
    def stop_scheduler(self):
        """Stop the background scheduler"""
        try:
            if self.scheduler.running:
                self.scheduler.shutdown()
                logger.info("✅ ESPN scheduler stopped")
            return True
        except Exception as e:
            logger.error(f"❌ Error stopping scheduler: {e}")
            return False
    
    def daily_sync(self):
        """Daily sync job - runs every day at 07:00 Vienna time"""
        try:
            logger.info("🔄 Running daily ESPN sync...")
            
            with self.app.app_context():
                # Get current week
                current_week = self.espn_sync.get_current_week()
                
                # Sync results for current and previous weeks
                for week in range(max(1, current_week - 1), current_week + 1):
                    self.espn_sync.sync_results(week)
                
                # Validate completed games and calculate points
                self.points_calculator.validate_completed_games()
                
                logger.info("✅ Daily ESPN sync completed")
                
        except Exception as e:
            logger.error(f"❌ Error in daily sync: {e}")
    
    def weekly_schedule_sync(self):
        """Weekly schedule sync job - runs every Tuesday at 07:00 Vienna time"""
        try:
            logger.info("🔄 Running weekly ESPN schedule sync...")
            
            with self.app.app_context():
                # Sync complete schedule to catch any changes
                self.espn_sync.sync_schedule()
                
                logger.info("✅ Weekly ESPN schedule sync completed")
                
        except Exception as e:
            logger.error(f"❌ Error in weekly schedule sync: {e}")
    
    def hourly_game_validation(self):
        """Hourly game validation - runs every hour on Sundays"""
        try:
            logger.info("🔄 Running hourly game validation...")
            
            with self.app.app_context():
                # Get current week
                current_week = self.espn_sync.get_current_week()
                
                # Sync results for current week
                self.espn_sync.sync_results(current_week)
                
                # Validate completed games and calculate points
                self.points_calculator.validate_completed_games()
                
                logger.info("✅ Hourly game validation completed")
                
        except Exception as e:
            logger.error(f"❌ Error in hourly validation: {e}")
    
    def manual_sync(self):
        """Manual sync for testing purposes"""
        try:
            logger.info("🔄 Running manual ESPN sync...")
            
            with self.app.app_context():
                # Full sync
                if self.espn_sync.full_sync():
                    # Validate and calculate points
                    self.points_calculator.validate_completed_games()
                    logger.info("✅ Manual ESPN sync completed successfully")
                    return True
                else:
                    logger.error("❌ Manual ESPN sync failed")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Error in manual sync: {e}")
            return False
    
    def get_scheduler_status(self):
        """Get current scheduler status"""
        try:
            status = {
                'running': self.scheduler.running if hasattr(self, 'scheduler') else False,
                'jobs': []
            }
            
            if hasattr(self, 'scheduler') and self.scheduler.running:
                jobs = self.scheduler.get_jobs()
                for job in jobs:
                    status['jobs'].append({
                        'id': job.id,
                        'name': job.name,
                        'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                        'trigger': str(job.trigger)
                    })
            
            return status
            
        except Exception as e:
            logger.error(f"❌ Error getting scheduler status: {e}")
            return {'running': False, 'jobs': [], 'error': str(e)}

# Test function
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # This would normally be called with Flask app and other components
    print("ESPN Scheduler module loaded successfully")

