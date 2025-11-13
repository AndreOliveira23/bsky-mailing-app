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
- **[Compare All Hosting Options](HOSTING_OPTIONS.md)** - See all free platforms

## Setup

1. **Install Python** (3.7 or higher) if you haven't already.

2. **Install the required packages**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure your environment variables**:
   - Copy `.env.example` to `.env`
   - Update the `.env` file with your credentials:
     - `BLUESKY_HANDLE`: Your Bluesky handle (e.g., `yourhandle.bsky.social`)
     - `BLUESKY_PASSWORD`: Your Bluesky app password (not your main password)
     - `EMAIL_FROM`: Your Gmail address
     - `EMAIL_PASSWORD`: Your Gmail app password (not your main password)
     - `EMAIL_TO`: The recipient email address
     - `SMTP_SERVER`: `smtp.gmail.com` (default)
     - `SMTP_PORT`: `587` (default)

   > **Note**: For Gmail, you'll need to generate an "App Password" if you have 2FA enabled.

## Usage

### Run Manually (Local)
```bash
python bluesky_emailer.py
```

### Deploy to Cloud (Scheduled/Automated)

Want to run this automatically every day without self-hosting?
- 🚀 **[GitHub Actions Setup](GITHUB_ACTIONS_SETUP.md)** - Quick 10-min setup (⭐ Recommended)
- 📘 **[All Hosting Options](HOSTING_OPTIONS.md)** - Compare 5+ free platforms

**TL;DR:** Push to GitHub, add 7 secrets, done! Runs daily at 22:00 UTC (7 PM Brazil) for free.

## Setting Up a Daily Schedule (Windows)

1. Open Task Scheduler
2. Create a new task
3. Under the "Triggers" tab, create a new trigger
   - Set to "Daily" and choose your preferred time
4. Under the "Actions" tab, create a new action
   - Action: "Start a program"
   - Program/script: `python`
   - Add arguments: `"C:\path\to\bluesky_emailer.py"` (use the actual path to the script)
   - Start in: `C:\path\to\script\directory`

## Setting Up a Daily Schedule (Linux/macOS)

Add the following line to your crontab (run `crontab -e`):
```
0 9 * * * cd /path/to/script && /usr/bin/python3 /path/to/bluesky_emailer.py >> /path/to/script/log.txt 2>&1
```
This will run the script every day at 9 AM and log the output to a file.

## 🔒 Security Best Practices

- ✅ **Never commit** your `.env` file to version control (already in `.gitignore`)
- ✅ **Use app-specific passwords** instead of your main account passwords
  - Bluesky: Settings → App Passwords
  - Gmail: [Generate App Password](https://myaccount.google.com/apppasswords)
- ✅ **For production**: Use GitHub Secrets (encrypted at rest)
- ✅ **Rotate secrets** regularly for security

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
