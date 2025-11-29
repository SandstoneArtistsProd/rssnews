"""
CSV export module for exporting articles to CSV format.
"""

import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional


class CSVExporter:
    """Handles exporting articles to CSV files."""

    def __init__(self, export_dir: str = "exports"):
        """
        Initialize CSV exporter.

        Args:
            export_dir: Directory for export files
        """
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)

    def export_articles(self, articles: List[Dict], filename: Optional[str] = None,
                       source_filter: Optional[str] = None) -> str:
        """
        Export articles to CSV file.

        Args:
            articles: List of article dictionaries
            filename: Custom filename (optional)
            source_filter: Source name for filename (optional)

        Returns:
            Path to exported file
        """
        if not articles:
            self.logger.warning("No articles to export")
            return ""

        # Generate filename
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            if source_filter:
                filename = f"{source_filter.lower()}_articles_{timestamp}.csv"
            else:
                filename = f"articles_{timestamp}.csv"

        filepath = self.export_dir / filename

        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                # Define CSV columns
                fieldnames = [
                    'id',
                    'url',
                    'title',
                    'source',
                    'publication_date',
                    'text_length',
                    'full_text',
                    'is_duplicate',
                    'created_at'
                ]

                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()

                for article in articles:
                    writer.writerow(article)

            self.logger.info(f"Exported {len(articles)} articles to {filepath}")
            return str(filepath)

        except Exception as e:
            self.logger.error(f"Export failed: {e}")
            raise

    def export_summary(self, articles: List[Dict], filename: Optional[str] = None) -> str:
        """
        Export summary (without full text) to CSV.

        Args:
            articles: List of article dictionaries
            filename: Custom filename (optional)

        Returns:
            Path to exported file
        """
        if not articles:
            self.logger.warning("No articles to export")
            return ""

        # Generate filename
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"articles_summary_{timestamp}.csv"

        filepath = self.export_dir / filename

        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'id',
                    'url',
                    'title',
                    'source',
                    'publication_date',
                    'text_length',
                    'is_duplicate',
                    'created_at'
                ]

                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()

                for article in articles:
                    writer.writerow({k: v for k, v in article.items() if k in fieldnames})

            self.logger.info(f"Exported summary of {len(articles)} articles to {filepath}")
            return str(filepath)

        except Exception as e:
            self.logger.error(f"Summary export failed: {e}")
            raise

    def export_statistics(self, stats: Dict, filename: Optional[str] = None) -> str:
        """
        Export statistics to text file.

        Args:
            stats: Statistics dictionary
            filename: Custom filename (optional)

        Returns:
            Path to exported file
        """
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"statistics_{timestamp}.txt"

        filepath = self.export_dir / filename

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("DEADLINE COLLECTOR STATISTICS\n")
                f.write("=" * 50 + "\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

                # Overall stats
                overall = stats.get('overall', {})
                f.write("OVERALL STATISTICS\n")
                f.write("-" * 50 + "\n")
                f.write(f"Total Articles: {overall.get('total_articles', 0):,}\n")
                f.write(f"Total Characters: {overall.get('total_chars', 0):,}\n")
                f.write(f"Average Length: {overall.get('avg_length', 0):,.0f} chars\n")
                f.write(f"Earliest Article: {overall.get('earliest', 'N/A')}\n")
                f.write(f"Latest Article: {overall.get('latest', 'N/A')}\n")
                f.write(f"Duplicates Filtered: {stats.get('duplicates', 0):,}\n\n")

                # By source
                by_source = stats.get('by_source', [])
                if by_source:
                    f.write("BY SOURCE\n")
                    f.write("-" * 50 + "\n")
                    for source in by_source:
                        f.write(f"{source['source']}:\n")
                        f.write(f"  Articles: {source['count']:,}\n")
                        f.write(f"  Avg Length: {source.get('avg_length', 0):,.0f} chars\n\n")

            self.logger.info(f"Exported statistics to {filepath}")
            return str(filepath)

        except Exception as e:
            self.logger.error(f"Statistics export failed: {e}")
            raise
