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
# Use stdout/stderr for Gunicorn's own logging
accesslog = '-'  # Log to stdout
errorlog = '-'   # Log to stderr
capture_output = True  # Capture and redirect application stdout/stderr to logging
loglevel = 'info'

# Process naming
proc_name = 'rss-feed-manager'

# SSL (if needed, uncomment and configure)
# keyfile = '/path/to/keyfile'
# certfile = '/path/to/certfile'