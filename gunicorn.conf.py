import multiprocessing
import os

# Server socket
bind = "0.0.0.0:5000"
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
loglevel = 'info'

# Ensure Gunicorn can write to its log files
def on_starting(server):
    """Ensure log files exist and have proper permissions before starting"""
    for log_file in [accesslog, errorlog]:
        # Create log file if it doesn't exist
        if not os.path.exists(log_file):
            open(log_file, 'a').close()
        # Set permissions to 664
        os.chmod(log_file, 0o664)

# Log formatting
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = 'rss-feed-manager'

# SSL (if needed, uncomment and configure)
# keyfile = '/path/to/keyfile'
# certfile = '/path/to/certfile'