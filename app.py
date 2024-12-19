import os
from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()

# Create app
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "venture_weekly_secret"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///rss_feeds.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize extensions
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

# Import routes after app initialization to avoid circular imports
from auth import auth_bp
from feed_manager import feed_bp

app.register_blueprint(auth_bp)
app.register_blueprint(feed_bp)

with app.app_context():
    db.drop_all()  # Temporarily drop all tables to recreate with new schema
    db.create_all()
