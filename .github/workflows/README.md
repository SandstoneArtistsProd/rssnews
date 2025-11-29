# GitHub Actions Workflows

This directory contains GitHub Actions workflows for automated collection.

## Available Workflows

### 1. `simple-collector.yml` - Basic Scheduled Collection ⭐ **RECOMMENDED**

**What it does:**
- Runs every hour automatically
- Collects articles from RSS feeds
- Exports to CSV
- Uploads CSV files as artifacts

**Use this if:**
- You want simple, straightforward automation
- You're okay downloading CSV exports from GitHub Actions artifacts
- You don't need persistent database storage

**Schedule:** Every hour at :00 minutes

### 2. `collector.yml` - Advanced with Database Persistence

**What it does:**
- Runs every hour automatically
- Maintains persistent database across runs
- Exports to CSV
- Creates GitHub releases with exports
- Preserves database using artifacts

**Use this if:**
- You need the database to persist between runs
- You want automatic releases with each export
- You need advanced features

**Schedule:** Every hour at :00 minutes

### 3. `python-app.yml` - CI/CD Testing

**What it does:**
- Runs on every push/PR
- Tests code on multiple Python versions
- Checks code formatting
- Validates imports

**Use this for:**
- Development and testing
- Code quality checks
- NOT for running the collector

## How to Enable

1. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Add GitHub Actions workflows"
   git push origin main
   ```

2. **Enable GitHub Actions:**
   - Go to your repository on GitHub
   - Click "Actions" tab
   - If prompted, click "I understand my workflows, go ahead and enable them"

3. **Manual Test Run:**
   - Go to Actions tab
   - Select "Simple Deadline Collector" (or your chosen workflow)
   - Click "Run workflow" button
   - Click green "Run workflow" button

## Choosing a Schedule

Edit the `cron:` line in your chosen workflow:

```yaml
# Every hour at :00
- cron: '0 * * * *'

# Every 30 minutes
- cron: '*/30 * * * *'

# Every 2 hours
- cron: '0 */2 * * *'

# Every 6 hours (4 times daily)
- cron: '0 */6 * * *'

# Daily at 9 AM UTC
- cron: '0 9 * * *'

# Twice daily (6 AM and 6 PM UTC)
- cron: '0 6,18 * * *'
```

**Note:** GitHub Actions uses UTC time.

## Accessing Results

### CSV Exports (Artifacts)

1. Go to Actions tab
2. Click on a completed workflow run
3. Scroll to "Artifacts" section at the bottom
4. Download "deadline-articles" or "csv-exports-XXX"

Artifacts are kept for 30 days.

### Database (Advanced workflow only)

The database is saved as an artifact named "articles-database" and reused across runs.

### Releases (Advanced workflow only)

Exports are automatically published as GitHub releases:
- Go to "Releases" section of your repo
- Download the latest export

## Important Notes

### GitHub Actions Limitations

- **Free tier:** 2,000 minutes/month for private repos, unlimited for public
- **Storage:** Artifacts count against storage quota
- **Cron timing:** May be delayed by up to 10 minutes during high load
- **Database:** Not persisted by default (use advanced workflow)

### Recommended Setup

**For most users:**
1. Use `simple-collector.yml`
2. Delete or disable the other workflows
3. Download CSV exports from artifacts as needed

**For power users:**
1. Use `collector.yml` for database persistence
2. Keep `python-app.yml` for code quality checks
3. Access exports via Releases

## Troubleshooting

### Workflow not running

- Check that Actions are enabled in repository settings
- Verify the workflow file is in `.github/workflows/`
- Check GitHub Actions status page

### Collection fails

- View logs in Actions tab → click on failed run
- Check if dependencies installed correctly
- Verify Python version compatibility

### No artifacts

- Ensure the workflow completed successfully
- Check that export step ran (view logs)
- Artifacts expire after retention period (30 days default)

## Customization

### Change Python version

```yaml
- name: Set up Python
  uses: actions/setup-python@v4
  with:
    python-version: '3.11'  # Change this
```

### Add notifications

Add Slack, Discord, or email notifications on success/failure:

```yaml
- name: Notify on Slack
  if: failure()
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

### Store in Google Drive / S3

Add steps to upload exports to cloud storage:

```yaml
- name: Upload to Google Drive
  uses: adityak74/google-drive-upload-git-action@main
  with:
    credentials: ${{ secrets.DRIVE_CREDENTIALS }}
    filename: exports/*.csv
    folderId: ${{ secrets.DRIVE_FOLDER_ID }}
```

## Which Workflow Should I Use?

| Scenario | Recommended Workflow |
|----------|---------------------|
| Just want CSV exports | `simple-collector.yml` |
| Need persistent database | `collector.yml` |
| Running own server + GitHub backup | `simple-collector.yml` |
| Only using GitHub (no server) | `collector.yml` |
| Development/testing | `python-app.yml` |

## Disabling Workflows

To disable a workflow without deleting it:

1. Open the workflow file
2. Add to the top:
   ```yaml
   # Disabled - remove this comment to re-enable
   on: ~
   ```
3. Commit and push

Or delete the file entirely if not needed.
