"""
Database module for managing article storage and deduplication.
"""

import sqlite3
import hashlib
from datetime import datetime
from typing import Optional, Dict, List, Tuple
import logging


class ArticleDatabase:
    """Handles all database operations for article storage and retrieval."""

    def __init__(self, db_path: str = "articles.db"):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        self.logger = logging.getLogger(__name__)

    def connect(self):
        """Establish database connection and create tables if needed."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            self._create_tables()
            self.logger.info(f"Connected to database: {self.db_path}")
        except sqlite3.Error as e:
            self.logger.error(f"Database connection failed: {e}")
            raise

    def _create_tables(self):
        """Create necessary database tables."""
        cursor = self.conn.cursor()

        # Main articles table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                title TEXT,
                normalized_title TEXT,
                publication_date TEXT,
                source TEXT,
                full_text TEXT,
                text_length INTEGER,
                content_hash TEXT,
                is_duplicate BOOLEAN DEFAULT 0,
                original_article_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (original_article_id) REFERENCES articles(id)
            )
        """)

        # Indexes for performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_content_hash
            ON articles(content_hash)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_normalized_title
            ON articles(normalized_title)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_publication_date
            ON articles(publication_date)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_source
            ON articles(source)
        """)

        # System tracking table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_tracking (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                last_collection_time TIMESTAMP,
                last_successful_run TIMESTAMP,
                total_runs INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Initialize system tracking
        cursor.execute("""
            INSERT OR IGNORE INTO system_tracking
            (id, last_collection_time, last_successful_run, total_runs)
            VALUES (1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 0)
        """)

        self.conn.commit()
        self.logger.info("Database tables created/verified")

    def normalize_title(self, title: str) -> str:
        """
        Normalize title for deduplication comparison.

        Args:
            title: Original article title

        Returns:
            Normalized title string
        """
        if not title:
            return ""

        import re
        normalized = title.lower()
        normalized = re.sub(r'[^\w\s]', '', normalized)  # Remove punctuation
        normalized = re.sub(r'\s+', ' ', normalized)      # Normalize whitespace
        return normalized.strip()[:100]                   # Limit length

    def create_content_hash(self, content: str) -> str:
        """
        Create hash of content for deduplication.

        Args:
            content: Full article text

        Returns:
            Hash string
        """
        if not content:
            return ""

        # Use first 500 and last 500 characters
        start = content[:500].lower().replace(' ', '')
        end = content[-500:].lower().replace(' ', '')
        combined = start + end

        return hashlib.md5(combined.encode()).hexdigest()

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate Jaccard similarity between two texts.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score (0.0 to 1.0)
        """
        if not text1 or not text2:
            return 0.0

        # Get words longer than 3 characters
        words1 = set(w.lower() for w in text1.split() if len(w) > 3)
        words2 = set(w.lower() for w in text2.split() if len(w) > 3)

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0

    def check_duplicate(self, title: str, content: str,
                       similarity_threshold: float = 0.7) -> Tuple[bool, Optional[int], Optional[str]]:
        """
        Check if article is a duplicate.

        Args:
            title: Article title
            content: Article content
            similarity_threshold: Threshold for considering articles similar

        Returns:
            Tuple of (is_duplicate, original_article_id, original_source)
        """
        normalized_title = self.normalize_title(title)
        content_hash = self.create_content_hash(content)

        cursor = self.conn.cursor()

        # Check by content hash first (fastest)
        cursor.execute("""
            SELECT id, source FROM articles
            WHERE content_hash = ? AND is_duplicate = 0
        """, (content_hash,))

        result = cursor.fetchone()
        if result:
            return True, result['id'], result['source']

        # Check by normalized title
        cursor.execute("""
            SELECT id, source, full_text FROM articles
            WHERE normalized_title = ? AND is_duplicate = 0
        """, (normalized_title,))

        result = cursor.fetchone()
        if result:
            # Additional similarity check
            similarity = self.calculate_similarity(content, result['full_text'])
            if similarity > similarity_threshold:
                return True, result['id'], result['source']

        return False, None, None

    def insert_article(self, url: str, title: str, publication_date: str,
                      source: str, full_text: str, is_duplicate: bool = False,
                      original_article_id: Optional[int] = None) -> Optional[int]:
        """
        Insert new article into database.

        Args:
            url: Article URL
            title: Article title
            publication_date: Publication date
            source: Source name (e.g., 'Deadline')
            full_text: Full article content
            is_duplicate: Whether this is a duplicate
            original_article_id: ID of original article if duplicate

        Returns:
            Inserted article ID or None if failed
        """
        try:
            normalized_title = self.normalize_title(title)
            content_hash = self.create_content_hash(full_text)
            text_length = len(full_text) if full_text else 0

            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO articles (
                    url, title, normalized_title, publication_date, source,
                    full_text, text_length, content_hash, is_duplicate, original_article_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (url, title, normalized_title, publication_date, source,
                  full_text, text_length, content_hash, is_duplicate, original_article_id))

            self.conn.commit()
            self.logger.info(f"Inserted article: {title[:50]}... (ID: {cursor.lastrowid})")
            return cursor.lastrowid

        except sqlite3.IntegrityError:
            self.logger.warning(f"Article already exists: {url}")
            return None
        except sqlite3.Error as e:
            self.logger.error(f"Failed to insert article: {e}")
            return None

    def url_exists(self, url: str) -> bool:
        """
        Check if URL already exists in database.

        Args:
            url: Article URL

        Returns:
            True if URL exists
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM articles WHERE url = ?", (url,))
        return cursor.fetchone() is not None

    def get_all_articles(self, source: Optional[str] = None,
                        include_duplicates: bool = False) -> List[Dict]:
        """
        Retrieve all articles from database.

        Args:
            source: Filter by source name (optional)
            include_duplicates: Whether to include duplicate articles

        Returns:
            List of article dictionaries
        """
        cursor = self.conn.cursor()

        query = "SELECT * FROM articles WHERE 1=1"
        params = []

        if not include_duplicates:
            query += " AND is_duplicate = 0"

        if source:
            query += " AND source = ?"
            params.append(source)

        query += " ORDER BY publication_date DESC"

        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def get_statistics(self) -> Dict:
        """
        Get database statistics.

        Returns:
            Dictionary with statistics
        """
        cursor = self.conn.cursor()

        # Overall stats
        cursor.execute("""
            SELECT
                COUNT(*) as total_articles,
                MIN(publication_date) as earliest,
                MAX(publication_date) as latest,
                AVG(text_length) as avg_length,
                SUM(text_length) as total_chars
            FROM articles
            WHERE is_duplicate = 0
        """)
        overall = dict(cursor.fetchone())

        # By source
        cursor.execute("""
            SELECT
                source,
                COUNT(*) as count,
                AVG(text_length) as avg_length
            FROM articles
            WHERE is_duplicate = 0
            GROUP BY source
            ORDER BY count DESC
        """)
        by_source = [dict(row) for row in cursor.fetchall()]

        # Duplicates
        cursor.execute("""
            SELECT COUNT(*) as duplicate_count
            FROM articles
            WHERE is_duplicate = 1
        """)
        duplicates = cursor.fetchone()['duplicate_count']

        return {
            'overall': overall,
            'by_source': by_source,
            'duplicates': duplicates
        }

    def update_tracking(self):
        """Update system tracking after successful collection."""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE system_tracking
            SET
                last_collection_time = CURRENT_TIMESTAMP,
                last_successful_run = CURRENT_TIMESTAMP,
                total_runs = total_runs + 1,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = 1
        """)
        self.conn.commit()

    def get_last_collection_time(self) -> Optional[datetime]:
        """
        Get timestamp of last collection.

        Returns:
            DateTime of last collection or None
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT last_collection_time
            FROM system_tracking
            WHERE id = 1
        """)
        result = cursor.fetchone()

        if result and result['last_collection_time']:
            return datetime.fromisoformat(result['last_collection_time'])
        return None

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.logger.info("Database connection closed")

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
