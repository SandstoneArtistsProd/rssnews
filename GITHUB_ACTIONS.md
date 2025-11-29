# Running on GitHub Actions - Quick Guide

This guide shows you how to run the Deadline Collector automatically on GitHub's servers (no need for your own server!).

## Why Use GitHub Actions?

✅ **Free** - 2,000 minutes/month (private repos), unlimited (public repos)
✅ **No server needed** - Runs on GitHub's infrastructure
✅ **Automatic** - Schedule collections hourly, daily, etc.
✅ **Easy downloads** - CSV exports available as artifacts
✅ **Reliable** - GitHub handles uptime and maintenance

## Setup (3 Steps)

### Step 1: Push to GitHub

```bash
cd /Users/kevinnicklaus/deadline-collector

# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit: Deadline article collector"

# Add your GitHub repo as remote
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPO-NAME.git

# Push to GitHub
git push -u origin main
```

### Step 2: Enable GitHub Actions

1. Go to your repository on GitHub
2. Click the **"Actions"** tab
3. If you see a button, click **"I understand my workflows, go ahead and enable them"**
4. You should see 3 workflows listed:
   - ✅ **Simple Deadline Collector** (use this one!)
   - Advanced Collector (optional)
   - Python Application (for testing)

### Step 3: Test Run

1. In the Actions tab, click **"Simple Deadline Collector"**
2. Click the **"Run workflow"** dropdown button (right side)
3. Click the green **"Run workflow"** button
4. Wait 1-2 minutes for it to complete
5. Click on the completed run to see results

## Downloading Your CSV Files

After a workflow runs:

1. Go to **Actions** tab
2. Click on any **completed** (green checkmark) workflow run
3. Scroll to the bottom → **"Artifacts"** section
4. Click **"deadline-articles"** to download
5. Unzip the downloaded file → CSV inside!

## Schedule

By default, the collector runs **every hour** automatically.

To change the schedule:

1. Edit `.github/workflows/simple-collector.yml`
2. Change the `cron:` line:

```yaml
# Current (every hour)
- cron: '0 * * * *'

# Every 30 minutes
- cron: '*/30 * * * *'

# Every 2 hours
- cron: '0 */2 * * *'

# Daily at 9 AM UTC
- cron: '0 9 * * *'
```

3. Commit and push:
```bash
git add .github/workflows/simple-collector.yml
git commit -m "Update collection schedule"
git push
```

## What Gets Collected

Each run:
1. Fetches RSS feeds from Deadline, Variety, Hollywood Reporter
2. Extracts full article content
3. Detects and removes duplicates
4. Exports to CSV
5. Uploads CSV as downloadable artifact

## Cost

- **Public repository**: Unlimited minutes (FREE)
- **Private repository**: 2,000 free minutes/month
  - Each run takes ~2-5 minutes
  - Running hourly = ~3,600 minutes/month
  - **You'll need a paid plan for hourly private repo runs**

**Recommendation**: Make your repo public or reduce frequency (every 6 hours = ~600 minutes/month = FREE)

## Viewing Logs

To see what happened during collection:

1. Go to Actions tab
2. Click on a workflow run
3. Click **"run-collector"** job
4. Expand the steps to see detailed logs

## Troubleshooting

### "No workflows found"

- Make sure you pushed the `.github/workflows/` directory
- Check that workflow files end in `.yml`

### Workflow doesn't run on schedule

- GitHub Actions may delay up to 10 minutes during high load
- First scheduled run happens at next cron interval
- Use "Run workflow" to test immediately

### Collection fails

- Click on the failed run to see error logs
- Common issues:
  - Website blocking (try adjusting user-agent in config)
  - RSS feed down (temporary)
  - Timeout (increase in config.yaml)

### Want to run on YOUR server instead?

See the main README.md for:
- Cron job setup
- Systemd service
- PM2 process manager

## Comparison: GitHub Actions vs Your Server

| Feature | GitHub Actions | Your Server |
|---------|---------------|-------------|
| Cost | Free (limits apply) | Server cost |
| Setup | Push & done | Install, configure |
| Maintenance | None | You maintain |
| Reliability | GitHub SLA | Your uptime |
| Database | Fresh each run* | Persistent |
| Access | Download artifacts | Direct access |

*Use `collector.yml` (advanced) for persistent database

## Next Steps

1. ✅ Push to GitHub
2. ✅ Enable Actions
3. ✅ Test run manually
4. ✅ Wait for scheduled run
5. ✅ Download CSV exports
6. 🎉 Enjoy automated article collection!

## Advanced: Persistent Database

If you need the database to persist between runs:

1. Use `.github/workflows/collector.yml` instead
2. This workflow:
   - Saves database after each run
   - Restores it for next run
   - Creates releases with CSV exports
3. Database stored as artifact (90-day retention)

Enable by renaming:
```bash
mv .github/workflows/collector.yml .github/workflows/main.yml
rm .github/workflows/simple-collector.yml  # Remove simple version
git add .github/workflows/
git commit -m "Switch to persistent database workflow"
git push
```

## Questions?

- Check `.github/workflows/README.md` for detailed info
- Review logs in Actions tab
- Check main README.md for configuration options
