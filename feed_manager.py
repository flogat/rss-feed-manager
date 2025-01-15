from datetime import datetime, timedelta
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required
import csv
from io import StringIO
from models import RSSFeed, Article, ScanProgress, db
import logging
from sqlalchemy import desc, asc
from scheduler import get_next_scan_time
from feed_updater import update_all_feeds, update_single_feed, reset_scan_progress

feed_bp = Blueprint('feed', __name__)

@feed_bp.route('/')
@feed_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@feed_bp.route('/articles')
@feed_bp.route('/feeds/<int:feed_id>/articles')
@login_required
def view_articles(feed_id=None):
    page = request.args.get('page', 1, type=int)
    sort = request.args.get('sort', 'published_date')
    order = request.args.get('order', 'desc')

    # Base query with eager loading of feed relationship
    query = Article.query.join(RSSFeed, Article.feed_id == RSSFeed.id)

    # Add feed filter if feed_id is provided
    feed = None
    if feed_id:
        feed = RSSFeed.query.get_or_404(feed_id)
        query = query.filter(Article.feed_id == feed_id)

    # Add sorting
    sort_column = getattr(Article, sort, Article.published_date)
    if order == 'desc':
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))

    # Paginate results
    articles = query.paginate(page=page, per_page=20, error_out=False)

    return render_template('articles.html', articles=articles, feed=feed)

@feed_bp.route('/api/articles/<int:article_id>')
@login_required
def get_article(article_id):
    article = Article.query.get_or_404(article_id)
    feed = RSSFeed.query.get(article.feed_id)

    return jsonify({
        'title': article.title,
        'description': article.description,
        'source': feed.title if feed else 'Unknown Source'
    })

def sanitize_text(text):
    if not text:
        return ''
    # Replace all types of newlines and whitespace with single spaces
    text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ').replace('\v', ' ').replace('\f', ' ')
    # Replace multiple spaces with a single space
    text = ' '.join(text.split())
    # Remove any remaining special characters that might cause CSV issues
    text = ''.join(char for char in text if char.isprintable())
    # Strip leading/trailing whitespace
    return text.strip()

@feed_bp.route('/api/feeds/download')
@login_required
def download_feeds():
    try:
        feeds = RSSFeed.query.all()

        si = StringIO()
        cw = csv.writer(si)
        # Headers according to new structure
        cw.writerow(['Feed URL', 'Source Name', 'Category', 'Status', 'Last Checked', 'Items Collected', 'Newest Item'])

        for feed in feeds:
            # Get the newest article for this feed
            newest_article = Article.query.filter_by(feed_id=feed.id).order_by(Article.published_date.desc()).first()
            newest_item_title = newest_article.title if newest_article else ''

            cw.writerow([
                feed.url,                   # Feed URL
                sanitize_text(feed.title or ''),  # Source Name
                'Startups',                 # Category
                feed.status.upper(),        # Status
                feed.last_scan_time.isoformat() if feed.last_scan_time else '',  # Last Checked
                feed.num_articles,          # Items Collected
                sanitize_text(newest_item_title)  # Newest Item
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

@feed_bp.route('/api/feeds/<int:feed_id>/articles/download')
@login_required
def download_feed_articles(feed_id):
    try:
        feed = RSSFeed.query.get_or_404(feed_id)
        articles = Article.query.filter_by(feed_id=feed_id).order_by(Article.published_date.desc()).all()

        si = StringIO()
        cw = csv.writer(si)
        # Write headers according to new structure
        cw.writerow(['Title', 'Link', 'Publication Date', 'Source', 'Category', 'Summary'])

        # Write article data
        source_name = feed.title or feed.url
        for article in articles:
            cw.writerow([
                sanitize_text(article.title),
                article.link,
                article.published_date.isoformat() if article.published_date else '',
                sanitize_text(source_name),
                'Startups',
                sanitize_text(article.description)
            ])

        output = si.getvalue()
        si.close()
        return output, 200, {
            'Content-Type': 'text/csv',
            'Content-Disposition': f'attachment; filename=articles_{feed_id}.csv'
        }
    except Exception as e:
        logging.error(f"Error downloading articles for feed {feed_id}: {str(e)}")
        return jsonify({'error': 'Failed to download articles'}), 500

@feed_bp.route('/api/articles/download')
@login_required
def download_all_articles():
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        query = Article.query

        if start_date:
            query = query.filter(Article.published_date >= datetime.fromisoformat(start_date))
        if end_date:
            # Add one day to include the entire end date
            end_datetime = datetime.fromisoformat(end_date) + timedelta(days=1)
            query = query.filter(Article.published_date < end_datetime)

        si = StringIO()
        cw = csv.writer(si)
        # Headers according to new structure
        cw.writerow(['Title', 'Link', 'Publication Date', 'Source', 'Category', 'Summary'])

        for article in query.all():
            # Get the feed information for each article
            feed = RSSFeed.query.get(article.feed_id)
            source_name = feed.title if feed else 'Unknown Source'

            cw.writerow([
                sanitize_text(article.title),
                article.link,
                article.published_date.isoformat() if article.published_date else '',
                sanitize_text(source_name),
                'Startups',  # Default category for now
                sanitize_text(article.description)
            ])

        output = si.getvalue()
        si.close()
        return output, 200, {
            'Content-Type': 'text/csv',
            'Content-Disposition': 'attachment; filename=all_articles.csv'
        }
    except Exception as e:
        logging.error(f"Error downloading all articles: {str(e)}")
        return jsonify({'error': 'Failed to download articles'}), 500

@feed_bp.route('/api/feeds/<int:feed_id>', methods=['DELETE'])
@login_required
def delete_feed(feed_id):
    try:
        feed = RSSFeed.query.get_or_404(feed_id)

        # Delete associated articles first
        Article.query.filter_by(feed_id=feed_id).delete()

        # Then delete the feed
        db.session.delete(feed)
        db.session.commit()
        return jsonify({'message': 'Feed deleted successfully'})
    except Exception as e:
        logging.error(f"Error deleting feed {feed_id}: {str(e)}")
        db.session.rollback()
        return jsonify({'error': f'Failed to delete feed: {str(e)}'}), 500

@feed_bp.route('/api/feeds/refresh', methods=['POST'])
@login_required
def refresh_feeds():
    try:
        # Reset scan progress before starting
        reset_scan_progress()
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
        # Update scan progress for single feed
        progress = ScanProgress.get_current()
        progress.update(
            is_scanning=True,
            current_feed=feed.title or feed.url,
            current_index=1,
            total_feeds=1,
            completed=False
        )
        result = update_single_feed(feed)
        # Reset scan progress after completion
        reset_scan_progress()
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error refreshing feed {feed_id}: {str(e)}")
        # Reset scan progress on error
        reset_scan_progress()
        return jsonify({'error': str(e)}), 500

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

@feed_bp.route('/api/feeds')
@login_required
def get_feeds():
    next_scan = get_next_scan_time()
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
            'last_updated': feed.last_updated.isoformat() if feed.last_updated else None,
            'last_scan_time': feed.last_scan_time.isoformat() if feed.last_scan_time else None,
            'last_scan_trigger': feed.last_scan_trigger,
            'next_automatic_scan': next_scan.isoformat() if next_scan else None
        })

    # Get current scan progress from database
    scan_progress = ScanProgress.get_current()
    progress_data = {
        'is_scanning': scan_progress.is_scanning,
        'current_feed': scan_progress.current_feed,
        'current_index': scan_progress.current_index,
        'total_feeds': scan_progress.total_feeds,
        'completed': scan_progress.completed
    }

    # Include current scan progress in response
    response_data = {
        'feeds': feed_data,
        'scan_progress': progress_data,
        'next_scan': next_scan.isoformat() if next_scan else None
    }

    return jsonify(response_data)