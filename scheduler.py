from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from feed_updater import update_all_feeds
import logging
import threading
import atexit

scheduler = None
scheduler_lock = threading.Lock()
job_lock = threading.Lock()

def init_scheduler(app):
    """Initialize the scheduler with the Flask app context"""
    global scheduler
    with scheduler_lock:
        if scheduler is not None:
            logging.info("Scheduler already initialized, skipping")
            return

        logging.info("Initializing background scheduler")

        # Configure thread pool executor with max workers
        executors = {
            'default': ThreadPoolExecutor(max_workers=1)
        }

        # Create scheduler with proper configuration
        scheduler = BackgroundScheduler(
            executors=executors,
            job_defaults={
                'coalesce': True,  # Combine multiple pending executions of the same job into one
                'max_instances': 1,  # Only allow one instance of each job running at a time
                'misfire_grace_time': 60  # Allow jobs to start within 60 seconds of their scheduled time
            }
        )

        try:
            scheduler.add_job(
                func=lambda: run_update_with_context(app),
                trigger="interval",
                minutes=30,  # Changed from 3 to 30 minutes
                id='refresh_feeds',
                name='Refresh RSS Feeds',
                replace_existing=True  # Replace any existing job with same ID
            )

            scheduler.start()
            logging.info("Scheduler started successfully")

            # Register shutdown handler
            atexit.register(lambda: shutdown_scheduler())

            # Calculate and log next run time
            next_run = scheduler.get_job('refresh_feeds').next_run_time
            logging.info(f"Next automatic scan scheduled for: {next_run}")

        except Exception as e:
            logging.error(f"Error starting scheduler: {str(e)}")
            raise

def run_update_with_context(app):
    """Run the update with the provided app context"""
    # Use job_lock to prevent multiple parallel executions
    if not job_lock.acquire(blocking=False):
        logging.warning("Feed update already in progress, skipping this execution")
        return

    try:
        logging.info("Starting scheduled feed update")
        with app.app_context():
            try:
                update_all_feeds(trigger='automatic')
                logging.info("Scheduled feed update completed successfully")
            except Exception as e:
                logging.error(f"Error during scheduled feed update: {str(e)}")
    finally:
        job_lock.release()

def get_next_scan_time():
    """Helper function to safely get next scan time"""
    global scheduler
    if scheduler and scheduler.get_job('refresh_feeds'):
        try:
            next_run = scheduler.get_job('refresh_feeds').next_run_time
            logging.debug(f"Next scheduled scan time: {next_run}")
            return next_run
        except Exception as e:
            logging.error(f"Error getting next scan time: {str(e)}")
    logging.warning("Scheduler or refresh job not found")
    return None

def shutdown_scheduler():
    """Safely shut down the scheduler"""
    global scheduler
    if scheduler:
        try:
            scheduler.shutdown(wait=False)
            logging.info("Scheduler shut down successfully")
        except Exception as e:
            logging.error(f"Error shutting down scheduler: {str(e)}")