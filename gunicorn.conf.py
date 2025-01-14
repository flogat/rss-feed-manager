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
os.makedirs('logs', exist_ok=True)

# Configure logging paths in the logs directory
accesslog = os.path.join('logs', 'gunicorn_access.log')
errorlog = os.path.join('logs', 'gunicorn_error.log')
capture_output = True  # Capture and redirect application stdout/stderr to logging
loglevel = 'info'

# Log formatting
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = 'rss-feed-manager'

# SSL (if needed, uncomment and configure)
# keyfile = '/path/to/keyfile'
# certfile = '/path/to/certfile'