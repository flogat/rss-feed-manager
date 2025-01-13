import feedparser
from datetime import datetime
import logging
from models import RSSFeed, Article, db
import socket
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# Global variables to track scan progress
current_scan_progress = {
    'is_scanning': False,
    'current_feed': None,
    'current_index': 0,
    'total_feeds': 0,
    'completed': False
}

# Set socket timeout for feedparser
socket.setdefaulttimeout(10)  # 10 seconds timeout

def update_single_feed(feed):
    try:
        current_time = datetime.utcnow()
        # Set timeout for feedparser
        parsed = feedparser.parse(feed.url, timeout=10)

        feed.title = parsed.feed.title if hasattr(parsed.feed, 'title') else feed.url
        feed.last_updated = current_time
        feed.last_scan_time = current_time
        feed.status = 'active'
        feed.error_count = 0

        current_count = Article.query.filter_by(feed_id=feed.id).count()
        new_articles = 0
        latest_date = feed.last_article_date
        articles_to_add = []

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
                articles_to_add.append(article)
                new_articles += 1
                if published_date and (not latest_date or published_date > latest_date):
                    latest_date = published_date

        # Batch add articles
        if articles_to_add:
            db.session.bulk_save_objects(articles_to_add)

        feed.num_articles = current_count + new_articles
        if latest_date:
            feed.last_article_date = latest_date

        db.session.commit()
        db.session.expunge_all()  # Clear the session

        # Return updated feed data for frontend
        return {
            'message': 'Feed refreshed successfully',
            'feed': {
                'last_scan_time': feed.last_scan_time.isoformat() if feed.last_scan_time else None,
                'last_article_date': feed.last_article_date.isoformat() if feed.last_article_date else None
            }
        }
    except Exception as e:
        db.session.rollback()  # Rollback on error
        feed.status = 'error'
        feed.error_count += 1
        feed.last_error = str(e)
        db.session.commit()
        db.session.expunge_all()  # Clear the session
        raise

def update_all_feeds(trigger='manual'):
    global current_scan_progress

    try:
        feeds = RSSFeed.query.all()
        current_time = datetime.utcnow()
        batch_size = 10  # Process feeds in batches of 10

        # Initialize scan progress
        current_scan_progress = {
            'is_scanning': True,
            'current_feed': None,
            'current_index': 0,
            'total_feeds': len(feeds),
            'completed': False
        }

        # Process feeds in batches
        for i in range(0, len(feeds), batch_size):
            batch = feeds[i:i + batch_size]
            for index, feed in enumerate(batch, i + 1):
                # Update scan progress
                current_scan_progress.update({
                    'current_feed': feed.title or feed.url,
                    'current_index': index,
                    'completed': False
                })

                try:
                    # Set timeout for feedparser
                    parsed = feedparser.parse(feed.url, timeout=10)

                    feed.title = parsed.feed.title if hasattr(parsed.feed, 'title') else feed.url
                    feed.last_updated = current_time
                    feed.last_scan_time = current_time
                    feed.last_scan_trigger = trigger
                    feed.status = 'active'
                    feed.error_count = 0

                    current_count = Article.query.filter_by(feed_id=feed.id).count()
                    new_articles = 0
                    latest_date = feed.last_article_date
                    articles_to_add = []

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
                            articles_to_add.append(article)
                            new_articles += 1
                            if published_date and (not latest_date or published_date > latest_date):
                                latest_date = published_date

                    # Batch add articles
                    if articles_to_add:
                        db.session.bulk_save_objects(articles_to_add)

                    feed.num_articles = current_count + new_articles
                    if latest_date:
                        feed.last_article_date = latest_date

                except Exception as e:
                    feed.status = 'error'
                    feed.error_count += 1
                    feed.last_error = str(e)
                    feed.last_scan_time = current_time
                    feed.last_scan_trigger = trigger
                    logging.error(f"Error updating feed {feed.url}: {str(e)}")
                    continue

            # Commit after each batch
            try:
                db.session.commit()
                db.session.expunge_all()  # Clear session after each batch
            except Exception as e:
                db.session.rollback()
                logging.error(f"Error committing batch: {str(e)}")

    except Exception as e:
        logging.error(f"Error in update_all_feeds: {str(e)}")
        raise
    finally:
        current_scan_progress.update({
            'is_scanning': False,
            'completed': True
        })
        db.session.close()  # Ensure session is closed