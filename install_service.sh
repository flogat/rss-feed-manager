#!/bin/bash

# Ensure script is run with bash
if [ ! "$BASH_VERSION" ]; then
    echo "Please run this script with bash"
    exit 1
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Ensure script is not run as root directly
if [ "$EUID" -eq 0 ]; then 
    echo "Please do not run this script as root"
    exit 1
fi

# Check if systemd is available
if ! command_exists systemctl; then
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

echo "Using virtual environment: $VENV_PATH"

# Create service user if it doesn't exist
echo "Creating service user..."
sudo useradd -r -s /bin/false rss_manager 2>/dev/null || true

# Set ownership of the installation directory
echo "Setting directory permissions..."
sudo chown -R rss_manager:rss_manager "$INSTALL_DIR"

# Create systemd service file
echo "Creating systemd service file..."
cat << EOF | sudo tee /etc/systemd/system/rss-feed-manager.service
[Unit]
Description=RSS Feed Manager Service
After=network.target

[Service]
Type=simple
User=rss_manager
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$VENV_PATH/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONPATH=$INSTALL_DIR"
ExecStart=$VENV_PATH/bin/gunicorn --config gunicorn.conf.py wsgi:app
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