# RSS Feed Manager

A comprehensive RSS feed management system designed for efficient tracking, monitoring, and analysis of multiple RSS feeds with advanced administrative capabilities.

## Features

- Python Flask backend with robust feed management architecture
- SQLite database with Flask-Migrate for schema migrations
- Secure user authentication
- Asynchronous background feed scanning with optimized scanning speed
- Advanced article metadata processing and export
- Responsive web interface with enhanced feed display and status tracking
- Improved CSV export functionality with newline handling
- Enhanced progress tracking during feed scanning

## Setup

1. Clone the repository:
```bash
git clone https://github.com/flogat/rss-feed-manager.git
cd rss-feed-manager
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Initialize the database:
```bash
flask db upgrade
```

4. Run the application:

For development:
```bash
python main.py
```

For production (recommended):
```bash
gunicorn --config gunicorn.conf.py wsgi:app
```

Note: Always use gunicorn for production deployment as it properly initializes the feed scheduler and handles multiple worker processes.

The application will be available at `http://localhost:5000`

## Usage
1. Log in to the admin interface
2. Add RSS feeds through the web interface
3. Monitor feed statuses and article collection
4. Export collected articles as CSV
5. View individual articles and their content

## Setting up as a System Service

### Create Service User (Optional but recommended)
```bash
sudo useradd -r -s /bin/false rss_manager
sudo chown -R rss_manager:rss_manager /path/to/rss-feed-manager
```

### Create Systemd Service File
Create a new service file at `/etc/systemd/system/rss-feed-manager.service`:

```ini
[Unit]
Description=RSS Feed Manager Service
After=network.target

[Service]
Type=simple
User=rss_manager
WorkingDirectory=/path/to/rss-feed-manager
Environment="PATH=/path/to/rss-feed-manager/venv/bin"
ExecStart=/path/to/rss-feed-manager/venv/bin/gunicorn --config gunicorn.conf.py wsgi:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Install and Enable Service
```bash
# Reload systemd to recognize the new service
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable rss-feed-manager

# Start the service
sudo systemctl start rss-feed-manager
```

### Service Management Commands
```bash
# Check service status
sudo systemctl status rss-feed-manager

# Start service
sudo systemctl start rss-feed-manager

# Stop service
sudo systemctl stop rss-feed-manager

# Restart service
sudo systemctl restart rss-feed-manager

# View logs
sudo journalctl -u rss-feed-manager
```

## Export Features

- Download all articles as CSV
- Export feed list with status information
- Filter articles by date range
- Clean text formatting in exports (removes newlines and special characters)

## Development

The project uses:
- Flask for the web framework
- SQLAlchemy for database operations
- APScheduler for background tasks
- Bootstrap for the frontend

## License

MIT License