import os
import logging
from datetime import datetime
from app import app
from auth import init_admin
from scheduler import init_scheduler

if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Initialize logging configuration first
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f'logs/rss_feed_{datetime.now().strftime("%Y_%m")}.log'),
            logging.StreamHandler()
        ]
    )
    
    # Initialize admin user
    with app.app_context():
        init_admin()
    
    # Start the scheduler
    init_scheduler()
    
    # Run the application
    app.run(host="0.0.0.0", port=5000, debug=True)
