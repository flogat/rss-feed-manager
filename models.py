from datetime import datetime
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class RSSFeed(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), unique=True, nullable=False)
    title = db.Column(db.String(200))
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default='active')
    error_count = db.Column(db.Integer, default=0)
    last_error = db.Column(db.String(500))

class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    feed_id = db.Column(db.Integer, db.ForeignKey('rss_feed.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    link = db.Column(db.String(500), unique=True, nullable=False)
    description = db.Column(db.Text)
    published_date = db.Column(db.DateTime)
    collected_date = db.Column(db.DateTime, default=datetime.utcnow)
