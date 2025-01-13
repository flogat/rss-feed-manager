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
```bash
python main.py
```

The application will be available at `http://localhost:5000`

## Usage

1. Log in to the admin interface
2. Add RSS feeds through the web interface
3. Monitor feed statuses and article collection
4. Export collected articles as CSV
5. View individual articles and their content

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
