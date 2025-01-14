#!/bin/bash

# Ensure script is run with bash
if [ ! "$BASH_VERSION" ]; then
    echo "Please run this script with bash"
    exit 1
fi

# Check if systemd is available
if ! command -v systemctl >/dev/null 2>&1; then
    echo "systemd is required but not found"
    exit 1
fi

# Get absolute path of the current directory
INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "Installing from directory: $INSTALL_DIR"

# Use virtual environment from user's home directory
VENV_PATH="$HOME/.venv"
if [ ! -d "$VENV_PATH" ]; then
    echo "Virtual environment not found at $VENV_PATH"
    echo "Please ensure Python virtual environment is set up in your home directory"
    exit 1
fi

# Verify current user
if [ -z "$USER" ]; then
    echo "Could not determine current user"
    exit 1
fi

echo "Using virtual environment: $VENV_PATH"
echo "Service will run as user: $USER"

# Create logs directory with proper permissions
LOGS_DIR="$INSTALL_DIR/logs"
echo "Creating logs directory at: $LOGS_DIR"
mkdir -p "$LOGS_DIR"

# Set ownership and permissions for logs directory
sudo chown -R $USER:$USER "$LOGS_DIR"
sudo chmod 775 "$LOGS_DIR"

# Create and set permissions for log files
touch "$LOGS_DIR/app.log"
sudo chown $USER:$USER "$LOGS_DIR/app.log"
sudo chmod 664 "$LOGS_DIR/app.log"

# Create systemd service file
echo "Creating systemd service file..."
cat << EOF | sudo tee /etc/systemd/system/rss-feed-manager.service
[Unit]
Description=RSS Feed Manager Service
After=network.target

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$INSTALL_DIR
Environment=PATH=/usr/local/bin:/usr/bin:/bin:$VENV_PATH/bin
Environment=PYTHONPATH=$INSTALL_DIR
Environment=HOME=$HOME
# Ensure directory permissions
ExecStartPre=/bin/bash -c 'mkdir -p $LOGS_DIR && chown -R $USER:$USER $LOGS_DIR && chmod 775 $LOGS_DIR'
ExecStartPre=/bin/bash -c 'touch $LOGS_DIR/app.log && chown $USER:$USER $LOGS_DIR/app.log && chmod 664 $LOGS_DIR/app.log'
ExecStart=/bin/bash -c 'source $VENV_PATH/bin/activate && exec gunicorn --config $INSTALL_DIR/gunicorn.conf.py wsgi:app'
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd to recognize the new service
echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

# Enable and start the service
echo "Enabling and starting service..."
sudo systemctl enable rss-feed-manager
sudo systemctl start rss-feed-manager

# Check service status
echo "Checking service status..."
sudo systemctl status rss-feed-manager

echo "
Installation complete! You can manage the service with these commands:
- Check status: sudo systemctl status rss-feed-manager
- Start service: sudo systemctl start rss-feed-manager
- Stop service: sudo systemctl stop rss-feed-manager
- Restart service: sudo systemctl restart rss-feed-manager
- View logs: sudo journalctl -u rss-feed-manager
"