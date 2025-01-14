import os
import logging
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from app import app
from auth import init_admin
from scheduler import init_scheduler

def setup_logging():
    """Configure centralized logging with monthly rotation"""
    try:
        # Get absolute path for logs directory
        base_dir = os.path.dirname(os.path.abspath(__file__))
        logs_dir = os.path.join(base_dir, 'logs')

        # Ensure logs directory exists
        if not os.path.exists(logs_dir):
            try:
                os.makedirs(logs_dir, mode=0o775, exist_ok=True)
            except PermissionError as e:
                print(f"Error creating logs directory: {e}")
                print(f"Please ensure {logs_dir} exists and has proper permissions")
                raise

        # Create formatter with consistent format for all logs
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            '%Y-%m-%d %H:%M:%S'
        )

        # Set up file handler with monthly rotation for application logs
        app_log_file = os.path.join(logs_dir, 'app.log')

        # Ensure log file exists with proper permissions
        if not os.path.exists(app_log_file):
            try:
                # Create the file
                with open(app_log_file, 'a') as f:
                    pass
                os.chmod(app_log_file, 0o664)
            except PermissionError as e:
                print(f"Error creating or setting permissions for log file: {e}")
                print(f"Please ensure {app_log_file} has proper permissions")
                raise

        # Test write access to log file
        try:
            with open(app_log_file, 'a') as f:
                f.write('')
        except PermissionError as e:
            print(f"Error writing to log file: {e}")
            print(f"Please check permissions for {app_log_file}")
            raise

        app_file_handler = TimedRotatingFileHandler(
            app_log_file,
            when='midnight',
            interval=30,  # Monthly rotation
            backupCount=12,  # Keep 12 months of logs
            encoding='utf-8'
        )
        app_file_handler.setFormatter(formatter)
        app_file_handler.setLevel(logging.INFO)

        # Set up console handler for development
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.DEBUG if app.debug else logging.INFO)

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG if app.debug else logging.INFO)

        # Remove any existing handlers
        root_logger.handlers = []

        # Add our handlers
        root_logger.addHandler(app_file_handler)
        root_logger.addHandler(console_handler)

        # Specific logger configurations
        logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
        logging.getLogger('werkzeug').setLevel(logging.INFO)

        # Log startup message with path information
        logging.info(f'Application logging initialized. Log directory: {logs_dir}')
        logging.info(f'Log file path: {app_log_file}')

        # Test log file write
        logging.info('Logging system initialized successfully')

    except Exception as e:
        print(f"Error setting up logging: {str(e)}")
        raise

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