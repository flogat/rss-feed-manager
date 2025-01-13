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
    num_articles = db.Column(db.Integer, default=0)
    last_article_date = db.Column(db.DateTime)
    last_scan_trigger = db.Column(db.String(50), default='manual')  # 'manual' or 'automatic'
    last_scan_time = db.Column(db.DateTime)

class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    feed_id = db.Column(db.Integer, db.ForeignKey('rss_feed.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    link = db.Column(db.String(500), unique=True, nullable=False)
    description = db.Column(db.Text)
    published_date = db.Column(db.DateTime)
    collected_date = db.Column(db.DateTime, default=datetime.utcnow)
    feed = db.relationship('RSSFeed', backref=db.backref('articles', lazy='dynamic'))

class ScanProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    is_scanning = db.Column(db.Boolean, default=False)
    current_feed = db.Column(db.String(500))
    current_index = db.Column(db.Integer, default=0)
    total_feeds = db.Column(db.Integer, default=0)
    completed = db.Column(db.Boolean, default=True)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

    @staticmethod
    def get_current():
        progress = ScanProgress.query.first()
        if not progress:
            progress = ScanProgress()
            db.session.add(progress)
            db.session.commit()
        return progress

    def update(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.last_updated = datetime.utcnow()
        db.session.commit()