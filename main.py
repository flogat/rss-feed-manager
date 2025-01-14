import os
import logging
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from app import app
from auth import init_admin
from scheduler import init_scheduler

def setup_logging():
    """Configure centralized logging with monthly rotation"""
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Set up file handler with monthly rotation
    log_file = os.path.join('logs', 'rss_feed.log')
    file_handler = TimedRotatingFileHandler(
        log_file,
        when='midnight',
        interval=30,  # Monthly rotation
        backupCount=12  # Keep 12 months of logs
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    # Set up console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG if app.debug else logging.INFO)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if app.debug else logging.INFO)

    # Remove any existing handlers
    root_logger.handlers = []

    # Add our handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Specific logger configurations
    # Set SQLAlchemy logging to WARNING to reduce noise
    logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
    # Set Werkzeug logging to INFO
    logging.getLogger('werkzeug').setLevel(logging.INFO)

if __name__ == "__main__":
    # Initialize logging first
    setup_logging()

    try:
        # Initialize admin user
        with app.app_context():
            init_admin()
            logging.info("Admin user initialized successfully")

        # Start the scheduler with app instance
        init_scheduler(app)
        logging.info("Scheduler started successfully")

        # Run the application
        app.run(host="0.0.0.0", port=5000, debug=True)
    except Exception as e:
        logging.error(f"Application startup failed: {str(e)}")
        raise