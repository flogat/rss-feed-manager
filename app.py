import os
from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from sqlalchemy.orm import DeclarativeBase
import logging

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()
migrate = Migrate()

def create_app():
    # Create app
    app = Flask(__name__)

    # Ensure instance directory exists
    os.makedirs(app.instance_path, exist_ok=True)

    app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "venture_weekly_secret"
    # Configure SQLite database in instance folder
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(app.instance_path, 'rss_feeds.db')}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,
        "pool_size": 10,
        "max_overflow": 20,
        "pool_recycle": 3600,
        "pool_timeout": 30,
        "max_overflow": 5,
        "echo": False,  # Disable SQL query logging
    }

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    login_manager.login_view = 'auth.login'

    # Import routes after app initialization to avoid circular imports
    from auth import auth_bp
    from feed_manager import feed_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(feed_bp)

    @app.template_filter('relative_time')
    def relative_time(date):
        if not date:
            return ''

        now = datetime.utcnow()
        diff = now - date

        seconds = diff.total_seconds()
        minutes = seconds // 60
        hours = minutes // 60
        days = diff.days

        if seconds < 60:
            return 'just now'
        elif minutes < 10:
            # Show minutes and seconds when less than 10 minutes
            secs = int(seconds % 60)
            return f'{int(minutes)} minute{"s" if minutes != 1 else ""} {secs} second{"s" if secs != 1 else ""} ago'
        elif minutes < 60:
            return f'{int(minutes)} minute{"s" if minutes != 1 else ""} ago'
        elif hours < 10:
            # Show hours and minutes when less than 10 hours
            mins = int(minutes % 60)
            return f'{int(hours)} hour{"s" if hours != 1 else ""} {mins} minute{"s" if mins != 1 else ""} ago'
        elif hours < 24:
            return f'{int(hours)} hour{"s" if hours != 1 else ""} ago'
        elif days < 10:
            # Show days and hours when less than 10 days
            hrs = int(hours % 24)
            return f'{days} day{"s" if days != 1 else ""} {hrs} hour{"s" if hrs != 1 else ""} ago'
        elif days < 30:
            return f'{days} day{"s" if days != 1 else ""} ago'
        else:
            return date.strftime('%Y-%m-%d')

    return app

# Create the application instance
app = create_app()