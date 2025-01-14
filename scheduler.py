from apscheduler.schedulers.background import BackgroundScheduler
from feed_updater import update_all_feeds
import logging
import threading

scheduler = None
scheduler_lock = threading.Lock()

def init_scheduler(app):
    """Initialize the scheduler with the Flask app context"""
    global scheduler
    with scheduler_lock:
        if scheduler is None:
            logging.info("Initializing background scheduler")
            scheduler = BackgroundScheduler()
            scheduler.add_job(
                func=lambda: run_update_with_context(app),
                trigger="interval",
                minutes=3,  # Set to 3 minutes for testing
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

def run_update_with_context(app):
    """Run the update with the provided app context"""
    logging.info("Starting scheduled feed update")
    with app.app_context():
        try:
            update_all_feeds(trigger='automatic')
            logging.info("Scheduled feed update completed successfully")
        except Exception as e:
            logging.error(f"Error during scheduled feed update: {str(e)}")

def get_next_scan_time():
    """Helper function to safely get next scan time"""
    global scheduler
    if scheduler and scheduler.get_job('refresh_feeds'):
        next_run = scheduler.get_job('refresh_feeds').next_run_time
        logging.debug(f"Next scheduled scan time: {next_run}")
        return next_run
    logging.warning("Scheduler or refresh job not found")
    return None