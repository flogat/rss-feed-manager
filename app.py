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

    return app

# Create the application instance
app = create_app()

# Database will be initialized through Flask-Migrate commands
