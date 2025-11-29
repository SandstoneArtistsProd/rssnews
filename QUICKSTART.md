# Quick Start Guide

Get up and running with Deadline Collector in 5 minutes.

## 1. Installation

```bash
# Clone or navigate to the repository
cd deadline-collector

# Run the setup script
./setup.sh
```

The setup script will:
- Check Python version
- Create a virtual environment
- Install all dependencies

## 2. First Run

Activate the virtual environment and run a test collection:

```bash
# Activate virtual environment
source venv/bin/activate

# Run a single collection
python collector.py
```

This will:
- Fetch RSS feeds from Deadline, Variety, and Hollywood Reporter
- Extract full article content
- Store in SQLite database
- Log results

## 3. View Results

Check what was collected:

```bash
# Show statistics
python collector.py --stats
```

Expected output:
```
==============================================================
DEADLINE COLLECTOR STATISTICS
==============================================================

Total Unique Articles: 42
Duplicates Filtered: 3
Total Characters: 123,456
Average Article Length: 2,939 chars
Date Range: 2025-01-01 to 2025-01-15

BY SOURCE:
------------------------------------------------------------
  Deadline                    25 articles  (avg: 3,214 chars)
  Variety                     12 articles  (avg: 2,455 chars)
  Hollywood Reporter           5 articles  (avg: 3,102 chars)
==============================================================
```

## 4. Export Data

Export to CSV:

```bash
# Export all articles with full text
python collector.py --export

# Export Deadline articles only
python collector.py --export --source Deadline

# Export summary (without full text)
python collector.py --export --summary
```

Files will be saved to `exports/` directory.

## 5. Set Up Continuous Collection

### Option A: Run in Schedule Mode

Keep the collector running continuously:

```bash
python collector.py --schedule
```

Press Ctrl+C to stop.

### Option B: Set Up Cron Job

Add to crontab to run every hour:

```bash
# Edit crontab
crontab -e

# Add this line (replace paths)
0 * * * * cd /path/to/deadline-collector && /path/to/deadline-collector/venv/bin/python collector.py >> logs/cron.log 2>&1
```

### Option C: Use systemd (Linux)

```bash
# Edit the service file with your paths
nano deadline-collector.service

# Copy to systemd
sudo cp deadline-collector.service /etc/systemd/system/

# Enable and start
sudo systemctl enable deadline-collector
sudo systemctl start deadline-collector

# Check status
sudo systemctl status deadline-collector
```

## Configuration

Edit `config/config.yaml` to customize:

```yaml
collection:
  # Adjust collection schedule
  min_year: 2025  # Only articles from 2025 onwards

  # Add/remove feeds
  feeds:
    - name: "Deadline"
      url: "https://deadline.com/feed/"
      domain: "deadline.com"

  # Deduplication sensitivity (0.0 to 1.0)
  similarity_threshold: 0.7

  # Rate limiting (seconds)
  delay_between_requests: 1.0
```

## Common Tasks

### Check logs
```bash
tail -f logs/collector.log
```

### Browse database
```bash
sqlite3 articles.db
sqlite> SELECT title, source, publication_date FROM articles ORDER BY id DESC LIMIT 10;
sqlite> .exit
```

### Clean start
```bash
# Remove database and start fresh
rm articles.db
python collector.py
```

## Troubleshooting

### "No module named 'feedparser'"
- Activate virtual environment: `source venv/bin/activate`
- Or reinstall: `pip install -r requirements.txt`

### No articles collected
- Check `config/config.yaml` - ensure `min_year` is correct
- Check logs: `tail -f logs/collector.log`
- Test RSS feed: `curl https://deadline.com/feed/`

### Database locked
- Only run one instance at a time
- If using cron + manual, wait for cron job to finish

## Next Steps

- Read the full [README.md](README.md) for all features
- Customize configuration in `config/config.yaml`
- Set up automated collection (cron/systemd)
- Integrate exports into your workflow

## Support

- Check logs in `logs/collector.log`
- Review configuration in `config/config.yaml`
- Ensure all dependencies are installed: `pip list`
