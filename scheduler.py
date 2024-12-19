from apscheduler.schedulers.background import BackgroundScheduler
from feed_manager import update_all_feeds
import logging

def init_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        func=update_all_feeds,
        trigger="interval",
        hours=1,
        id='refresh_feeds',
        name='Refresh RSS Feeds'
    )
    
    try:
        scheduler.start()
        logging.info("Scheduler started successfully")
    except Exception as e:
        logging.error(f"Error starting scheduler: {str(e)}")
