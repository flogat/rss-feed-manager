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

For development (not recommended for production):
```bash
flask run --host=0.0.0.0 --port=5000
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

## Admin Password Reset

If you need to reset the admin password, use the provided script:

```bash
# Make the script executable (first time only)
chmod +x reset_admin_password.sh

# Reset the admin password
./reset_admin_password.sh <new_password>

Example:
./reset_admin_password.sh mynewpassword123
```

## Setting up as a System Service

The project includes an automated installation script that sets up the RSS Feed Manager as a system service. This script will:
- Create a dedicated service user
- Configure the necessary permissions
- Create and enable a systemd service
- Start the service automatically

### Installing the Service

1. Make sure you are in the project directory and have your virtual environment activated.

2. Run the installation script:
```bash
./install_service.sh
```

The script will automatically:
- Detect your virtual environment
- Set up the service using the current directory
- Configure systemd
- Start the service

### Service Management Commands

After installation, you can manage the service using these commands:
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