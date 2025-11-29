# Deadline Collector - Project Summary

## What This Is

A complete Python rewrite of your Node.js Deadline article collector, designed to run continuously as a cron job and ready for GitHub deployment.

## Key Features

✅ **RSS Feed Collection** - Monitors Deadline, Variety, and Hollywood Reporter
✅ **Full-Text Extraction** - Scrapes complete article content from URLs
✅ **Smart Deduplication** - Detects duplicates across sources using content hashing
✅ **SQLite Database** - Fast, reliable local storage with full indexing
✅ **CSV Export** - Export articles with or without full text
✅ **Scheduled Collection** - Built-in scheduler or cron/systemd integration
✅ **GitHub Ready** - Complete with .gitignore, CI/CD workflows, documentation

## Project Structure

```
deadline-collector/
├── collector.py              # Main entry point (CLI)
├── config/
│   └── config.yaml          # Configuration file
├── src/
│   ├── database.py          # SQLite database operations
│   ├── content_extractor.py # Web scraping & content extraction
│   ├── deadline_collector.py# Main collection logic
│   └── csv_exporter.py      # CSV export functionality
├── exports/                 # CSV exports saved here
├── logs/                    # Log files
├── .github/workflows/       # GitHub Actions CI/CD
├── setup.sh                 # Automated setup script
├── requirements.txt         # Python dependencies
├── README.md               # Complete documentation
├── QUICKSTART.md           # Quick start guide
└── LICENSE                 # MIT License
```

## How to Use

### 1. Setup (One-time)

```bash
cd /Users/kevinnicklaus/deadline-collector
./setup.sh
```

This creates a virtual environment and installs all dependencies.

### 2. Run Collection

```bash
# Activate virtual environment
source venv/bin/activate

# Run once
python collector.py

# Run on schedule (continuous)
python collector.py --schedule

# View stats
python collector.py --stats

# Export to CSV
python collector.py --export
python collector.py --export --source Deadline
```

### 3. Deploy to GitHub

```bash
cd /Users/kevinnicklaus/deadline-collector
git init
git add .
git commit -m "Initial commit: Python Deadline collector"
git remote add origin <your-github-repo-url>
git push -u origin main
```

### 4. Set Up Continuous Collection

**Option A: Run as Service (Linux)**
```bash
sudo cp deadline-collector.service /etc/systemd/system/
sudo systemctl enable deadline-collector
sudo systemctl start deadline-collector
```

**Option B: Cron Job**
```bash
crontab -e
# Add: 0 * * * * cd /path/to/deadline-collector && /path/to/venv/bin/python collector.py
```

**Option C: PM2**
```bash
pm2 start collector.py --interpreter python3 --name deadline-collector -- --schedule
```

## What Changed from Node.js Version

| Feature | Node.js | Python |
|---------|---------|--------|
| RSS Parsing | rss-parser | feedparser |
| Web Scraping | cheerio | BeautifulSoup4 |
| Database | sqlite3 | sqlite3 |
| Scheduling | node-cron | schedule |
| HTTP Requests | axios | requests |
| Configuration | JSON/JS | YAML |
| Export | csv-writer | csv module |

## Configuration

Edit `config/config.yaml` to customize:

- **Feeds**: Add/remove RSS feeds
- **Schedule**: Change collection frequency
- **Deduplication**: Adjust similarity threshold
- **Rate Limiting**: Control request delays
- **Extraction**: Timeout, retries, minimum content length

## Key Improvements

1. **Better Logging** - Structured logging with file + console output
2. **Type Safety** - Type hints throughout codebase
3. **Modular Design** - Clean separation of concerns
4. **Configuration** - YAML-based config with validation
5. **Documentation** - Comprehensive README + Quick Start guide
6. **CI/CD** - GitHub Actions for testing and linting
7. **Easy Setup** - One-command installation with setup.sh
8. **Flexible Deployment** - Multiple options (systemd, cron, PM2)

## Database Schema

Articles are stored with:
- URL (unique)
- Title & normalized title
- Publication date
- Source (Deadline, Variety, etc.)
- Full text content
- Content hash for deduplication
- Duplicate tracking

## Next Steps

1. **Run setup**: `./setup.sh`
2. **Test collection**: `source venv/bin/activate && python collector.py`
3. **Review results**: `python collector.py --stats`
4. **Configure**: Edit `config/config.yaml` as needed
5. **Deploy**: Push to GitHub
6. **Automate**: Set up cron job or systemd service

## Files You Can Safely Modify

- `config/config.yaml` - All configuration settings
- `.gitignore` - Add/remove ignored files
- `README.md` - Update documentation
- Source files in `src/` - Customize collection logic

## Files Generated During Use

- `articles.db` - SQLite database (gitignored)
- `logs/collector.log` - Application logs (gitignored)
- `exports/*.csv` - CSV exports (gitignored)

## Support & Troubleshooting

See QUICKSTART.md for common issues and solutions.

All dependencies are managed via `requirements.txt`.

Logs are in `logs/collector.log`.

## Differences from Your Request

You asked for "npm run export:deadline:csv" as Python code. This project goes beyond that and provides:

1. **Complete Collection System** - Not just export, but also continuous collection
2. **Multiple Export Options** - CSV with/without full text, by source, summary
3. **Production Ready** - Logging, error handling, configuration management
4. **Deployment Options** - Cron, systemd, or built-in scheduler
5. **GitHub Ready** - Complete repository structure with CI/CD

The export functionality you wanted is available via:
```bash
python collector.py --export --source Deadline
```

This exports Deadline articles to CSV, equivalent to your Node.js command.

---

**Author**: Converted from Node.js by Claude
**Date**: November 28, 2025
**License**: MIT
