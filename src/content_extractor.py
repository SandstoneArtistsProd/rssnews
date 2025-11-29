"""
Content extraction module for fetching and parsing article content.
"""

import requests
from bs4 import BeautifulSoup
import logging
import time
from typing import Optional, Dict
from urllib.parse import urlparse


class ContentExtractor:
    """Handles fetching and extracting content from article URLs."""

    def __init__(self, config: Dict):
        """
        Initialize content extractor.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': config.get('user_agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
        })

    def fetch_url(self, url: str, timeout: int = 10, retries: int = 3) -> Optional[str]:
        """
        Fetch URL content with retries.

        Args:
            url: URL to fetch
            timeout: Request timeout in seconds
            retries: Number of retry attempts

        Returns:
            HTML content or None if failed
        """
        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=timeout)
                response.raise_for_status()
                self.logger.debug(f"Fetched URL: {url}")
                return response.text

            except requests.RequestException as e:
                self.logger.warning(f"Fetch attempt {attempt + 1}/{retries} failed for {url}: {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                continue

        self.logger.error(f"Failed to fetch URL after {retries} attempts: {url}")
        return None

    def extract_content(self, html: str, url: str) -> Optional[str]:
        """
        Extract main content from HTML.

        Args:
            html: HTML content
            url: URL of the article (for site-specific extraction)

        Returns:
            Extracted text content or None
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')

            # Remove unwanted elements
            for element in soup.find_all(['script', 'style', 'nav', 'header', 'footer',
                                         'aside', 'iframe', 'noscript']):
                element.decompose()

            # Remove common advertising/promotional classes
            for class_name in ['ads', 'advertisement', 'social-share', 'newsletter-signup',
                              'related-articles', 'comments', 'promo']:
                for element in soup.find_all(class_=lambda x: x and class_name in x.lower()):
                    element.decompose()

            # Site-specific selectors
            domain = urlparse(url).netloc

            content = None
            selectors = []

            if 'deadline.com' in domain:
                selectors = [
                    '.c-content__body',
                    '.entry-content',
                    '.post-content',
                    'article .content',
                    '[class*="article-body"]',
                    '[class*="article-content"]'
                ]
            elif 'variety.com' in domain:
                selectors = [
                    '.c-content',
                    '.o-article-detail__content',
                    '.entry-content',
                    'article .content'
                ]
            elif 'hollywoodreporter.com' in domain:
                selectors = [
                    '.a-article-body',
                    '.c-content',
                    '.entry-content',
                    'article .content'
                ]
            else:
                # Generic fallback selectors
                selectors = [
                    'article',
                    '[role="main"]',
                    '.entry-content',
                    '.post-content',
                    '.article-content',
                    '.article-body',
                    '.content'
                ]

            # Try each selector
            for selector in selectors:
                elements = soup.select(selector)
                if elements:
                    content = ' '.join(elem.get_text(separator=' ', strip=True) for elem in elements)
                    if len(content) > 200:  # Minimum content length
                        break

            # Ultimate fallback: get body text
            if not content or len(content) < 200:
                body = soup.find('body')
                if body:
                    content = body.get_text(separator=' ', strip=True)

            if content:
                # Clean up the content
                content = self._clean_content(content)
                self.logger.debug(f"Extracted {len(content)} characters from {url}")
                return content

            self.logger.warning(f"No content extracted from {url}")
            return None

        except Exception as e:
            self.logger.error(f"Content extraction failed for {url}: {e}")
            return None

    def _clean_content(self, content: str) -> str:
        """
        Clean extracted content.

        Args:
            content: Raw extracted content

        Returns:
            Cleaned content
        """
        import re

        # Normalize whitespace
        content = re.sub(r'\s+', ' ', content)

        # Remove common promotional text
        patterns = [
            r'Get our Alerts.*',
            r'Subscribe to.*',
            r'Sign up for.*',
            r'Newsletter.*',
            r'Click here to.*',
            r'Read more:.*',
            r'Related:.*'
        ]

        for pattern in patterns:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE)

        return content.strip()

    def get_article_content(self, url: str) -> Optional[str]:
        """
        Fetch and extract content from article URL.

        Args:
            url: Article URL

        Returns:
            Extracted content or None
        """
        html = self.fetch_url(
            url,
            timeout=self.config.get('request_timeout', 10),
            retries=self.config.get('retry_attempts', 3)
        )

        if not html:
            return None

        content = self.extract_content(html, url)

        # Validate minimum content length
        min_length = self.config.get('min_content_length', 200)
        if content and len(content) < min_length:
            self.logger.warning(f"Content too short ({len(content)} chars) for {url}")
            return None

        return content

    def extract_metadata(self, html: str) -> Dict:
        """
        Extract metadata from HTML (optional, for future enhancements).

        Args:
            html: HTML content

        Returns:
            Dictionary of metadata
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            metadata = {}

            # Try to get author
            author_meta = soup.find('meta', attrs={'name': 'author'})
            if author_meta:
                metadata['author'] = author_meta.get('content', '')

            # Try to get description
            desc_meta = soup.find('meta', attrs={'name': 'description'})
            if desc_meta:
                metadata['description'] = desc_meta.get('content', '')

            # Try to get published date
            pub_meta = soup.find('meta', attrs={'property': 'article:published_time'})
            if pub_meta:
                metadata['published_time'] = pub_meta.get('content', '')

            return metadata

        except Exception as e:
            self.logger.error(f"Metadata extraction failed: {e}")
            return {}

    def close(self):
        """Close session."""
        self.session.close()
