import feedparser
from datetime import datetime
import logging
import time
from models import RSSFeed, Article, db

# Global variables to track scan progress
current_scan_progress = {
    'is_scanning': False,
    'current_feed': None,
    'current_index': 0,
    'total_feeds': 0,
    'completed': False
}

def update_single_feed(feed):
    try:
        current_time = datetime.utcnow()
        parsed = feedparser.parse(feed.url)
        feed.title = parsed.feed.title if hasattr(parsed.feed, 'title') else feed.url
        feed.last_updated = current_time
        feed.last_scan_time = current_time  # Update the scan time
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

        # Return updated feed data for frontend
        return {
            'message': 'Feed refreshed successfully',
            'feed': {
                'last_scan_time': feed.last_scan_time.isoformat() if feed.last_scan_time else None,
                'last_article_date': feed.last_article_date.isoformat() if feed.last_article_date else None
            }
        }
    except Exception as e:
        feed.status = 'error'
        feed.error_count += 1
        feed.last_error = str(e)
        db.session.commit()
        raise

def update_all_feeds(trigger='manual'):
    global current_scan_progress
    feeds = RSSFeed.query.all()
    current_time = datetime.utcnow()

    # Initialize scan progress
    current_scan_progress = {
        'is_scanning': True,
        'current_feed': None,
        'current_index': 0,
        'total_feeds': len(feeds),
        'completed': False
    }

    try:
        for index, feed in enumerate(feeds, 1):
            # Update scan progress
            current_scan_progress.update({
                'current_feed': feed.title or feed.url,
                'current_index': index,
                'completed': False
            })

            try:
                # Add 1-second pause between feeds
                if index > 1:  # Don't pause before the first feed
                    time.sleep(1)

                parsed = feedparser.parse(feed.url)
                feed.title = parsed.feed.title if hasattr(parsed.feed, 'title') else feed.url
                feed.last_updated = current_time
                feed.last_scan_time = current_time  # Ensure this is set before any potential error
                feed.last_scan_trigger = trigger
                feed.status = 'active'
                feed.error_count = 0
                # Commit the scan time update immediately to ensure it's saved
                db.session.commit()

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
                feed.last_scan_time = current_time  # Still record the scan attempt time
                feed.last_scan_trigger = trigger
                db.session.commit()  # Commit the error status and scan time
                logging.error(f"Error updating feed {feed.url}: {str(e)}")
                continue

        db.session.commit()
    except Exception as e:
        logging.error(f"Error in update_all_feeds: {str(e)}")
        raise
    finally:
        current_scan_progress.update({
            'is_scanning': False,
            'completed': True
        })
