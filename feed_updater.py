import feedparser
from datetime import datetime
import logging
from models import RSSFeed, Article, ScanProgress, db
import socket
from sqlalchemy.exc import SQLAlchemyError

# Set socket timeout for feedparser
socket.setdefaulttimeout(10)  # 10 seconds timeout

def reset_scan_progress():
    """Reset scan progress in database"""
    try:
        progress = ScanProgress.get_current()
        progress.update(
            is_scanning=False,
            current_feed=None,
            current_index=0,
            total_feeds=0,
            completed=True
        )
    except Exception as e:
        logging.error(f"Error resetting scan progress: {str(e)}")

def update_scan_progress(**kwargs):
    """Update scan progress in database"""
    try:
        progress = ScanProgress.get_current()
        progress.update(**kwargs)
    except Exception as e:
        logging.error(f"Error updating scan progress: {str(e)}")

def update_single_feed(feed):
    try:
        current_time = datetime.utcnow()
        # Set timeout for feedparser
        parsed = feedparser.parse(feed.url)

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
            try:
                db.session.bulk_save_objects(articles_to_add)
                db.session.commit()
            except SQLAlchemyError as e:
                db.session.rollback()
                logging.error(f"Error saving articles: {str(e)}")
                raise

        feed.num_articles = current_count + new_articles
        if latest_date:
            feed.last_article_date = latest_date

        try:
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            logging.error(f"Error updating feed: {str(e)}")
            raise

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
        try:
            db.session.commit()
        except SQLAlchemyError as commit_error:
            db.session.rollback()
            logging.error(f"Error updating feed error status: {str(commit_error)}")
        raise

def update_all_feeds(trigger='manual'):
    try:
        # Reset scan progress at the start
        reset_scan_progress()

        # Get all feeds within this session
        feeds = RSSFeed.query.all()
        total_feeds = len(feeds)

        if total_feeds == 0:
            return

        # Initialize scan progress
        update_scan_progress(
            is_scanning=True,
            current_feed=None,
            current_index=0,
            total_feeds=total_feeds,
            completed=False
        )

        current_time = datetime.utcnow()
        batch_size = 1  # Process one feed at a time for more granular updates
        processed_count = 0

        # Process feeds in batches
        for i in range(0, total_feeds, batch_size):
            batch = feeds[i:i + batch_size]

            for feed in batch:
                try:
                    # Refresh the feed object for this iteration
                    feed = db.session.merge(feed)
                    processed_count += 1

                    # Update scan progress for each feed
                    update_scan_progress(
                        current_feed=feed.title or feed.url,
                        current_index=processed_count,
                        completed=False
                    )

                    parsed = feedparser.parse(feed.url)

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

                    for entry_index, entry in enumerate(parsed.entries):
                        try:
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

                            # Update progress for every few articles
                            if entry_index % 5 == 0:  # Update every 5 articles
                                update_scan_progress(
                                    current_feed=f"{feed.title or feed.url} (processing article {entry_index + 1})",
                                    current_index=processed_count - 1 + ((entry_index + 1) / len(parsed.entries)),
                                    completed=False
                                )
                        except Exception as article_error:
                            logging.error(f"Error processing article {entry_index} for feed {feed.url}: {str(article_error)}")
                            continue

                    # Batch add articles with error handling
                    if articles_to_add:
                        try:
                            db.session.bulk_save_objects(articles_to_add)
                            db.session.commit()
                        except SQLAlchemyError as e:
                            db.session.rollback()
                            logging.error(f"Error saving articles batch: {str(e)}")
                            continue

                    feed.num_articles = current_count + new_articles
                    if latest_date:
                        feed.last_article_date = latest_date

                    try:
                        db.session.commit()
                    except SQLAlchemyError as e:
                        db.session.rollback()
                        logging.error(f"Error updating feed status: {str(e)}")
                        continue

                except Exception as feed_error:
                    db.session.rollback()
                    feed.status = 'error'
                    feed.error_count += 1
                    feed.last_error = str(feed_error)
                    feed.last_scan_time = current_time
                    feed.last_scan_trigger = trigger
                    try:
                        db.session.commit()
                    except SQLAlchemyError as commit_error:
                        db.session.rollback()
                        logging.error(f"Error updating feed error status: {str(commit_error)}")
                    logging.error(f"Error updating feed {feed.url}: {str(feed_error)}")
                    continue

    except Exception as e:
        logging.error(f"Error in update_all_feeds: {str(e)}")
        raise
    finally:
        # Reset scan progress when done
        reset_scan_progress()