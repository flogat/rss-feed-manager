from apscheduler.schedulers.background import BackgroundScheduler
from feed_updater import update_all_feeds
import logging

scheduler = None

def init_scheduler(app):
    """Initialize the scheduler with the Flask app context"""
    global scheduler
    if scheduler is None:
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
    with app.app_context():
        update_all_feeds(trigger='automatic')

def get_next_scan_time():
    """Helper function to safely get next scan time"""
    global scheduler
    if scheduler and scheduler.get_job('refresh_feeds'):
        return scheduler.get_job('refresh_feeds').next_run_time
    return None