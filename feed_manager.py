import feedparser
from datetime import datetime, timedelta
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required
import csv
from io import StringIO
from models import RSSFeed, Article, db
import logging

feed_bp = Blueprint('feed', __name__)

@feed_bp.route('/')
@feed_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@feed_bp.route('/api/feeds', methods=['GET'])
@login_required
def get_feeds():
    feeds = RSSFeed.query.all()
    return jsonify([{
        'id': feed.id,
        'url': feed.url,
        'title': feed.title,
        'last_updated': feed.last_updated.isoformat(),
        'status': feed.status,
        'error_count': feed.error_count
    } for feed in feeds])

@feed_bp.route('/api/feeds', methods=['POST'])
@login_required
def add_feed():
    url = request.json.get('url')
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    
    try:
        feed = RSSFeed(url=url)
        db.session.add(feed)
        db.session.commit()
        return jsonify({'message': 'Feed added successfully'})
    except Exception as e:
        logging.error(f"Error adding feed: {str(e)}")
        return jsonify({'error': str(e)}), 500

@feed_bp.route('/api/feeds/<int:feed_id>', methods=['DELETE'])
@login_required
def delete_feed(feed_id):
    feed = RSSFeed.query.get_or_404(feed_id)
    db.session.delete(feed)
    db.session.commit()
    return jsonify({'message': 'Feed deleted successfully'})

@feed_bp.route('/api/feeds/refresh', methods=['POST'])
@login_required
def refresh_feeds():
    try:
        update_all_feeds()
        return jsonify({'message': 'Feeds refreshed successfully'})
    except Exception as e:
        logging.error(f"Error refreshing feeds: {str(e)}")
        return jsonify({'error': str(e)}), 500

def update_all_feeds():
    feeds = RSSFeed.query.all()
    for feed in feeds:
        try:
            parsed = feedparser.parse(feed.url)
            feed.title = parsed.feed.title
            feed.last_updated = datetime.utcnow()
            feed.status = 'active'
            feed.error_count = 0
            
            for entry in parsed.entries:
                if not Article.query.filter_by(link=entry.link).first():
                    article = Article(
                        feed_id=feed.id,
                        title=entry.title,
                        link=entry.link,
                        description=entry.get('description', ''),
                        published_date=datetime(*entry.published_parsed[:6]) if 'published_parsed' in entry else None
                    )
                    db.session.add(article)
        except Exception as e:
            feed.status = 'error'
            feed.error_count += 1
            feed.last_error = str(e)
            logging.error(f"Error updating feed {feed.url}: {str(e)}")
    
    db.session.commit()

@feed_bp.route('/api/articles/download', methods=['GET'])
@login_required
def download_articles():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = Article.query
    if start_date:
        query = query.filter(Article.collected_date >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.filter(Article.collected_date <= datetime.fromisoformat(end_date))
    
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['Title', 'Link', 'Description', 'Published Date', 'Collected Date'])
    
    for article in query.all():
        cw.writerow([
            article.title,
            article.link,
            article.description,
            article.published_date,
            article.collected_date
        ])
    
    output = si.getvalue()
    si.close()
    return output, 200, {
        'Content-Type': 'text/csv',
        'Content-Disposition': 'attachment; filename=articles.csv'
    }
