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
# Use our application's logging system instead of separate files
accesslog = None  # Disable access log file (will go through app logging)
errorlog = None  # Disable error log file (will go through app logging)
capture_output = True  # Capture and redirect stdout/stderr to logging
loglevel = 'info'

# Process naming
proc_name = 'rss-feed-manager'

# SSL (if needed, uncomment and configure)
# keyfile = '/path/to/keyfile'
# certfile = '/path/to/certfile'