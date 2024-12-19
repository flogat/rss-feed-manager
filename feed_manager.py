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

@feed_bp.route('/api/feeds')
@login_required
def get_feeds():
    feeds = RSSFeed.query.all()
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    
    feed_data = []
    for feed in feeds:
        recent_articles = Article.query.filter(
            Article.feed_id == feed.id,
            Article.collected_date >= seven_days_ago
        ).count()
        
        feed_data.append({
            'id': feed.id,
            'url': feed.url,
            'title': feed.title,
            'status': feed.status,
            'num_articles': feed.num_articles,
            'recent_articles': recent_articles,
            'last_article_date': feed.last_article_date.isoformat() if feed.last_article_date else None,
            'last_updated': feed.last_updated.isoformat() if feed.last_updated else None
        })
    
    return jsonify(feed_data)

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

@feed_bp.route('/api/feeds/bulk', methods=['POST'])
@login_required
def add_feeds_bulk():
    try:
        urls = request.json.get('urls', [])
        if not urls:
            return jsonify({'error': 'No URLs provided'}), 400
        
        errors = []
        success_count = 0
        
        for url in urls:
            try:
                # Check if feed already exists
                if RSSFeed.query.filter_by(url=url).first():
                    errors.append(f"Feed already exists: {url}")
                    continue
                
                feed = RSSFeed(url=url)
                db.session.add(feed)
                success_count += 1
            except Exception as e:
                errors.append(f"Error adding {url}: {str(e)}")
        
        db.session.commit()
        
        response = {
            'message': f'Successfully added {success_count} feeds',
            'errors': errors if errors else None
        }
        return jsonify(response), 200 if success_count > 0 else 400
    except Exception as e:
        logging.error(f"Error in bulk feed addition: {str(e)}")
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

@feed_bp.route('/api/feeds/<int:feed_id>/refresh', methods=['POST'])
@login_required
def refresh_single_feed(feed_id):
    try:
        feed = RSSFeed.query.get_or_404(feed_id)
        update_single_feed(feed)
        return jsonify({'message': 'Feed refreshed successfully'})
    except Exception as e:
        logging.error(f"Error refreshing feed {feed_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

def update_single_feed(feed):
    try:
        parsed = feedparser.parse(feed.url)
        feed.title = parsed.feed.title
        feed.last_updated = datetime.utcnow()
        feed.status = 'active'
        feed.error_count = 0
        
        current_count = Article.query.filter_by(feed_id=feed.id).count()
        new_articles = 0
        latest_date = feed.last_article_date
        
        for entry in parsed.entries:
            if not Article.query.filter_by(link=entry.link).first():
                published_date = datetime(*entry.published_parsed[:6]) if 'published_parsed' in entry else None
                article = Article(
                    feed_id=feed.id,
                    title=entry.title,
                    link=entry.link,
                    description=entry.get('description', ''),
                    published_date=published_date
                )
                db.session.add(article)
                new_articles += 1
                if published_date and (not latest_date or published_date > latest_date):
                    latest_date = published_date
        
        feed.num_articles = current_count + new_articles
        if latest_date:
            feed.last_article_date = latest_date
            
        db.session.commit()
    except Exception as e:
        feed.status = 'error'
        feed.error_count += 1
        feed.last_error = str(e)
        db.session.commit()
        raise

def update_all_feeds():
    feeds = RSSFeed.query.all()
    for feed in feeds:
        try:
            parsed = feedparser.parse(feed.url)
            feed.title = parsed.feed.title
            feed.last_updated = datetime.utcnow()
            feed.status = 'active'
            feed.error_count = 0
            
            # Get current number of articles
            current_count = Article.query.filter_by(feed_id=feed.id).count()
            new_articles = 0
            latest_date = feed.last_article_date
            
            for entry in parsed.entries:
                if not Article.query.filter_by(link=entry.link).first():
                    published_date = datetime(*entry.published_parsed[:6]) if 'published_parsed' in entry else None
                    article = Article(
                        feed_id=feed.id,
                        title=entry.title,
                        link=entry.link,
                        description=entry.get('description', ''),
                        published_date=published_date
                    )
                    db.session.add(article)
                    new_articles += 1
                    if published_date and (not latest_date or published_date > latest_date):
                        latest_date = published_date
            
            feed.num_articles = current_count + new_articles
            if latest_date:
                feed.last_article_date = latest_date
        except Exception as e:
            feed.status = 'error'
            feed.error_count += 1
            feed.last_error = str(e)
            logging.error(f"Error updating feed {feed.url}: {str(e)}")
    
    db.session.commit()

@feed_bp.route('/api/articles/download', methods=['GET'])
@login_required
def download_articles():
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # If dates not provided, use default (7 days ago to today)
        if not start_date:
            start_date = (datetime.utcnow() - timedelta(days=7)).date().isoformat()
        if not end_date:
            end_date = datetime.utcnow().date().isoformat()
        
        query = Article.query
        if start_date:
            start_datetime = datetime.fromisoformat(start_date)
            query = query.filter(Article.collected_date >= start_datetime)
        if end_date:
            # Add one day to end_date to include the entire day
            end_datetime = datetime.fromisoformat(end_date) + timedelta(days=1)
            query = query.filter(Article.collected_date < end_datetime)
        
        si = StringIO()
        cw = csv.writer(si)
        # Headers are always included
        cw.writerow(['Title', 'Link', 'Description', 'Published Date', 'Collected Date'])
        
        for article in query.all():
            cw.writerow([
                article.title,
                article.link,
                article.description,
                article.published_date.isoformat() if article.published_date else '',
                article.collected_date.isoformat() if article.collected_date else ''
            ])
        
        output = si.getvalue()
        si.close()
        
        return output, 200, {
            'Content-Type': 'text/csv',
            'Content-Disposition': 'attachment; filename=collected_news.csv'
        }
    except Exception as e:
        logging.error(f"Error downloading articles: {str(e)}")
        return jsonify({'error': 'Failed to download articles'}), 500

@feed_bp.route('/api/feeds/download', methods=['GET'])
@login_required
def download_feeds():
    try:
        feeds = RSSFeed.query.all()
        
        si = StringIO()
        cw = csv.writer(si)
        # Headers are always included
        cw.writerow(['Title', 'URL', 'Status', 'Last Updated', 'Number of Articles', 'Last Article Date'])
        
        for feed in feeds:
            cw.writerow([
                feed.title,
                feed.url,
                feed.status,
                feed.last_updated.isoformat() if feed.last_updated else '',
                feed.num_articles,
                feed.last_article_date.isoformat() if feed.last_article_date else ''
            ])
        
        output = si.getvalue()
        si.close()
        return output, 200, {
            'Content-Type': 'text/csv',
            'Content-Disposition': 'attachment; filename=rss_feed_list.csv'
        }
    except Exception as e:
        logging.error(f"Error downloading feeds: {str(e)}")
        return jsonify({'error': 'Failed to download feeds'}), 500