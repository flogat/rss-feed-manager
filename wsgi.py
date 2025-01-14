from app import app
from scheduler import init_scheduler
from main import setup_logging
import logging

# Initialize logging first
setup_logging()
logging.info("Starting application under Gunicorn WSGI server")

# Initialize scheduler when running under WSGI server
# The scheduler's own locking mechanism will prevent multiple initializations
init_scheduler(app)

# Make the application available to gunicorn
application = app

if __name__ == "__main__":
    app.run()