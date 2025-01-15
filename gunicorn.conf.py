import multiprocessing
import os

# Server socket
bind = "0.0.0.0:5000"  # Changed back to port 5000
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'sync'
worker_connections = 1000
timeout = 30
keepalive = 2

# Logging
# Ensure logs directory exists
base_dir = os.path.dirname(os.path.abspath(__file__))
logs_dir = os.path.join(base_dir, 'logs')
os.makedirs(logs_dir, mode=0o755, exist_ok=True)

# Configure logging paths in the logs directory
accesslog = os.path.join(logs_dir, 'gunicorn_access.log')
errorlog = os.path.join(logs_dir, 'gunicorn_error.log')
capture_output = True  # Capture and redirect application stdout/stderr to logging
loglevel = 'debug'  # Changed to debug for more detailed logging
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = 'rss-feed-manager'

def post_worker_init(worker):
    """Ensure proper logging initialization after worker start"""
    import logging
    from main import setup_logging
    setup_logging()
    logging.info(f"Gunicorn worker {worker.pid} initialized")

# Ensure log files have proper permissions
def on_starting(server):
    """Ensure log files exist and have proper permissions before starting"""
    for log_file in [accesslog, errorlog]:
        # Create log file if it doesn't exist
        if not os.path.exists(log_file):
            open(log_file, 'a').close()
        # Set permissions to 664
        os.chmod(log_file, 0o664)