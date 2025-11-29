"""
Main Deadline article collector module.
Fetches articles from RSS feeds and extracts full content.
"""

import feedparser
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time
from urllib.parse import urlparse

from database import ArticleDatabase
from content_extractor import ContentExtractor


class DeadlineCollector:
    """Main collector class for Deadline articles."""

    def __init__(self, config: Dict, db: ArticleDatabase, extractor: ContentExtractor):
        """
        Initialize collector.

        Args:
            config: Configuration dictionary
            db: Database instance
            extractor: Content extractor instance
        """
        self.config = config
        self.db = db
        self.extractor = extractor
        self.logger = logging.getLogger(__name__)

        # Stats tracking
        self.stats = {
            'total_found': 0,
            'new_articles': 0,
            'duplicates': 0,
            'errors': 0,
            'skipped': 0
        }

    def collect(self):
        """Run collection process."""
        self.logger.info("=" * 60)
        self.logger.info("DEADLINE ARTICLE COLLECTION STARTED")
        self.logger.info("=" * 60)

        start_time = datetime.now()

        try:
            # Get feeds from config
            feeds = self.config.get('feeds', [])

            if not feeds:
                self.logger.error("No feeds configured")
                return

            all_articles = []

            # Fetch from RSS feeds
            for feed in feeds:
                articles = self._fetch_rss_feed(feed)
                all_articles.extend(articles)
                time.sleep(self.config.get('delay_between_feeds', 2))

            # Fetch from archive (Deadline only)
            if self.config.get('enable_archive_collection', True):
                archive_articles = self._fetch_deadline_archive()
                all_articles.extend(archive_articles)

            self.stats['total_found'] = len(all_articles)
            self.logger.info(f"Found {len(all_articles)} total articles")

            # Process articles
            self._process_articles(all_articles)

            # Update tracking
            self.db.update_tracking()

            # Log results
            duration = (datetime.now() - start_time).total_seconds()
            self._log_results(duration)

        except Exception as e:
            self.logger.error(f"Collection failed: {e}", exc_info=True)
            raise

    def _fetch_rss_feed(self, feed: Dict) -> List[Dict]:
        """
        Fetch articles from RSS feed.

        Args:
            feed: Feed configuration dictionary

        Returns:
            List of article dictionaries
        """
        name = feed.get('name', 'Unknown')
        url = feed.get('url', '')
        domain = feed.get('domain', '')

        self.logger.info(f"Fetching RSS feed: {name}")

        try:
            parsed_feed = feedparser.parse(url)

            if parsed_feed.bozo:
                self.logger.warning(f"RSS feed parsing issue for {name}: {parsed_feed.bozo_exception}")

            articles = []
            min_year = self.config.get('min_year', 2025)

            for entry in parsed_feed.entries:
                try:
                    # Parse publication date
                    pub_date = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        pub_date = datetime(*entry.published_parsed[:6])
                    elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                        pub_date = datetime(*entry.updated_parsed[:6])

                    # Filter by year
                    if pub_date and pub_date.year >= min_year:
                        article = {
                            'url': entry.get('link', ''),
                            'title': entry.get('title', ''),
                            'publication_date': pub_date.isoformat() if pub_date else None,
                            'source': name,
                            'domain': domain,
                            'source_type': 'RSS'
                        }
                        articles.append(article)

                except Exception as e:
                    self.logger.warning(f"Error parsing RSS entry: {e}")
                    continue

            self.logger.info(f"{name} RSS: Found {len(articles)} articles from {min_year}+")
            return articles

        except Exception as e:
            self.logger.error(f"Failed to fetch RSS feed {name}: {e}")
            return []

    def _fetch_deadline_archive(self) -> List[Dict]:
        """
        Fetch articles from Deadline archive pages.

        Returns:
            List of article dictionaries
        """
        self.logger.info("Fetching Deadline archive articles...")

        articles = []

        try:
            from bs4 import BeautifulSoup
            import requests

            # Get current month archive
            now = datetime.now()
            year = now.year
            month = now.strftime('%m')

            archive_url = f"https://deadline.com/{year}/{month}/"

            self.logger.debug(f"Fetching archive: {archive_url}")

            html = self.extractor.fetch_url(archive_url, timeout=15)
            if not html:
                return articles

            soup = BeautifulSoup(html, 'html.parser')

            # Find article links
            selectors = [
                f'a[href*="/{year}/"]',
                '.entry-title a',
                'h2 a',
                'h3 a'
            ]

            found_urls = set()

            for selector in selectors:
                links = soup.select(selector)
                for link in links:
                    href = link.get('href', '')
                    title = link.get_text(strip=True)

                    # Filter valid article URLs
                    if (href and title and
                        f'/{year}/' in href and
                        '#' not in href and
                        len(href) > 30 and
                        href not in found_urls):

                        # Make absolute URL
                        if not href.startswith('http'):
                            href = f"https://deadline.com{href}"

                        found_urls.add(href)

                        article = {
                            'url': href,
                            'title': title,
                            'publication_date': f"{year}-{month}-01T00:00:00",
                            'source': 'Deadline',
                            'domain': 'deadline.com',
                            'source_type': 'Archive'
                        }
                        articles.append(article)

            self.logger.info(f"Deadline Archive: Found {len(articles)} articles")
            return articles

        except Exception as e:
            self.logger.error(f"Archive fetch failed: {e}")
            return []

    def _process_articles(self, articles: List[Dict]):
        """
        Process and store articles with deduplication.

        Args:
            articles: List of article dictionaries
        """
        self.logger.info(f"Processing {len(articles)} articles...")

        # Prioritize Deadline articles
        articles.sort(key=lambda x: 0 if x['source'] == 'Deadline' else 1)

        for i, article in enumerate(articles, 1):
            try:
                # Check if URL already exists
                if self.db.url_exists(article['url']):
                    self.stats['skipped'] += 1
                    continue

                self.logger.info(f"[{i}/{len(articles)}] Processing: {article['title'][:60]}...")

                # Fetch full content
                full_text = self.extractor.get_article_content(article['url'])

                if not full_text:
                    self.logger.warning(f"No content extracted from {article['url']}")
                    self.stats['errors'] += 1
                    continue

                # Check for duplicates
                is_duplicate, original_id, original_source = self.db.check_duplicate(
                    article['title'],
                    full_text,
                    similarity_threshold=self.config.get('similarity_threshold', 0.7)
                )

                # Insert article
                article_id = self.db.insert_article(
                    url=article['url'],
                    title=article['title'],
                    publication_date=article['publication_date'],
                    source=article['source'],
                    full_text=full_text,
                    is_duplicate=is_duplicate,
                    original_article_id=original_id
                )

                if article_id:
                    if is_duplicate:
                        self.stats['duplicates'] += 1
                        self.logger.info(f"Duplicate detected: {article['source']} matches {original_source}")
                    else:
                        self.stats['new_articles'] += 1
                        self.logger.info(f"New article saved (ID: {article_id})")

                # Rate limiting
                delay = self.config.get('delay_between_requests', 1.0)
                time.sleep(delay)

            except Exception as e:
                self.logger.error(f"Failed to process article {article.get('url')}: {e}")
                self.stats['errors'] += 1
                continue

    def _log_results(self, duration: float):
        """
        Log collection results.

        Args:
            duration: Collection duration in seconds
        """
        self.logger.info("=" * 60)
        self.logger.info("COLLECTION COMPLETE")
        self.logger.info("=" * 60)
        self.logger.info(f"Duration: {duration:.1f} seconds")
        self.logger.info(f"Total found: {self.stats['total_found']}")
        self.logger.info(f"New articles: {self.stats['new_articles']}")
        self.logger.info(f"Duplicates: {self.stats['duplicates']}")
        self.logger.info(f"Skipped (existing): {self.stats['skipped']}")
        self.logger.info(f"Errors: {self.stats['errors']}")

        # Get database stats
        db_stats = self.db.get_statistics()
        overall = db_stats['overall']

        self.logger.info("")
        self.logger.info("DATABASE STATISTICS")
        self.logger.info("-" * 60)
        self.logger.info(f"Total unique articles: {overall['total_articles']}")
        self.logger.info(f"Total duplicates: {db_stats['duplicates']}")
        self.logger.info(f"Date range: {overall['earliest']} to {overall['latest']}")
        self.logger.info(f"Average article length: {overall['avg_length']:.0f} chars")

        if db_stats['by_source']:
            self.logger.info("")
            self.logger.info("BY SOURCE:")
            for source in db_stats['by_source']:
                self.logger.info(f"  {source['source']}: {source['count']} articles")

        self.logger.info("=" * 60)

    def get_statistics(self) -> Dict:
        """
        Get current statistics.

        Returns:
            Statistics dictionary
        """
        return {
            'collection': self.stats,
            'database': self.db.get_statistics()
        }
