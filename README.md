# Bluesky Post Emailer

This script fetches the latest post from the 'esportesNaTv' account on Bluesky and sends it via email on a daily basis.

## ✨ Features

- 📧 **Daily email delivery** of latest Bluesky posts
- 🔄 **Smart deduplication** - never get the same post twice
- ⏰ **Optimized schedule** - runs 1 hour after typical posting time (22:00 UTC)
- 🆓 **100% free** with GitHub Actions
- 🔒 **Secure** - secrets stored in GitHub

## 🚀 Quick Start Options

- **[Deploy to GitHub Actions (Free)](GITHUB_ACTIONS_SETUP.md)** - ⭐ Recommended (10 min setup)

## Setup

1. **Install Python** (3.7 or higher) if you haven't already.

2. **Install the required packages**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Email (Resend)**:

   > 🎯 Use **[Resend](EASY_EMAIL_SETUP.md)** — 5 minute setup, no OAuth.
   
   - Copy `.env.example` to `.env`
   - Sign up at https://resend.com/signup and create an API key
   - Update `.env`: `RESEND_API_KEY`, `EMAIL_FROM` (use onboarding@resend.dev for testing), and `EMAIL_TO`
   - See **[EASY_EMAIL_SETUP.md](EASY_EMAIL_SETUP.md)** for details

   > **Note**: No Bluesky credentials needed! The script uses the public Bluesky API.

## Usage

### Run Manually (Local)
```bash
python bluesky_daily_post_resend.py
```

### Deploy to Cloud (Scheduled/Automated)

Want to run this automatically every day without self-hosting?
- 🚀 **[GitHub Actions Setup](GITHUB_ACTIONS_SETUP.md)** - Quick 10-min setup (⭐ Recommended)
- 📘 **[All Hosting Options](HOSTING_OPTIONS.md)** - Compare 5+ free platforms

**TL;DR:** Push to GitHub, add 3 email secrets, done! Runs daily at 9:00 UTC (6 AM Brazil) for free. No Bluesky auth needed!

## Setting Up a Daily Schedule (Windows)

1. Open Task Scheduler
2. Create a new task
3. Under the "Triggers" tab, create a new trigger
   - Set to "Daily" and choose your preferred time
4. Under the "Actions" tab, create a new action
   - Action: "Start a program"
   - Program/script: `python`
   - Add arguments: `"C:\path\to\bluesky_daily_post.py"` (use the actual path to the script)
   - Start in: `C:\path\to\script\directory`

## Setting Up a Daily Schedule (Linux/macOS)

Add the following line to your crontab (run `crontab -e`):
```
0 9 * * * cd /path/to/script && /usr/bin/python3 /path/to/bluesky_daily_post_resend.py >> /path/to/script/log.txt 2>&1
```
This will run the script every day at 9 AM and log the output to a file.

## 🔒 Security Best Practices

- ✅ **Never commit** your `.env` file to version control (already in `.gitignore`)
- ✅ **Use provider API keys** (store as GitHub Secrets in CI)
- ✅ **No Bluesky authentication required** - uses public API to read posts
- ✅ **Rotate API keys** regularly and restrict scope in your provider dashboard

## 🔄 Smart Deduplication

The script tracks the last sent post to avoid duplicate emails:
- Stores post text in `last_sent_post.json`
- Only sends email if post content has changed
- Works automatically in both local and GitHub Actions
- Checks the "A agenda esportiva desta..." text pattern

## ⏰ Optimal Schedule

Based on analysis of 44 posts, the account typically posts around:
- **21:00 UTC** (6 PM Brazil time)
- The script runs at **22:00 UTC** (7 PM Brazil time)
- This gives 1 hour buffer to catch the latest post
