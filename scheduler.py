from apscheduler.schedulers.background import BackgroundScheduler
from feed_manager import update_all_feeds
import logging

scheduler = BackgroundScheduler()

def init_scheduler():
    scheduler.add_job(
        func=lambda: update_all_feeds(trigger='automatic'),
        trigger="interval",
        minutes=3,
        id='refresh_feeds',
        name='Refresh RSS Feeds'
    )
    
    try:
        scheduler.start()
        logging.info("Scheduler started successfully")
        # Calculate and log next run time
        next_run = scheduler.get_job('refresh_feeds').next_run_time
        logging.info(f"Next automatic scan scheduled for: {next_run}")
    except Exception as e:
        logging.error(f"Error starting scheduler: {str(e)}")
