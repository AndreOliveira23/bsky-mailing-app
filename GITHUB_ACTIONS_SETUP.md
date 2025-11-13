# GitHub Actions Setup Guide

Deploy your Bluesky emailer to run automatically every day using GitHub Actions - **completely free!**

> **✨ No Bluesky Authentication Required!**  
> This setup uses the **public Bluesky API** to read posts - you only need your email credentials.

## ⏱️ Time Required: ~5 minutes

---

## 📋 Prerequisites

- GitHub account (free)
- Your email credentials ready

---

## 🚀 Step-by-Step Setup

### Step 1: Create GitHub Repository

1. Go to [github.com](https://github.com)
2. Click the **"+"** icon → **"New repository"**
3. Name it (e.g., `bluesky-emailer`)
4. Choose **Private** (to keep your code private)
5. Click **"Create repository"**

### Step 2: Push Your Code to GitHub

Open terminal in your project folder and run:

```bash
# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit: Bluesky emailer with GitHub Actions"

# Add remote (replace with your repository URL)
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git

# Push to GitHub
git branch -M main
git push -u origin main
```

### Step 3: Add Secrets to GitHub

This is the most important step - it keeps your credentials secure!

1. Go to your repository on GitHub
2. Click **Settings** (top navigation)
3. In left sidebar: **Secrets and variables** → **Actions**
4. Click **"New repository secret"**

Add each of these secrets one by one:

#### Required Secrets (5 total):

| Secret Name | Example Value | Where to Get It |
|-------------|---------------|-----------------||
| `EMAIL_FROM` | `your@gmail.com` | Your Gmail address |
| `EMAIL_PASSWORD` | `abcd efgh ijkl mnop` | [Gmail App Password](#how-to-get-gmail-app-password) |
| `EMAIL_TO` | `recipient@example.com` | Where to send the emails |
| `SMTP_SERVER` | `smtp.gmail.com` | Gmail SMTP server |
| `SMTP_PORT` | `587` | Gmail SMTP port |

**Note:** No Bluesky credentials needed! The script uses the public Bluesky API to read posts.

### Step 4: Verify Setup

1. Go to **Actions** tab in your repository
2. You should see the workflow: **"Daily Bluesky Post Email"**
3. Click on the workflow name
4. You'll see:
   - Scheduled run time (next execution)
   - Past runs (if any)

### Step 5: Test Manually (Recommended)

Before waiting for the scheduled run:

1. Go to **Actions** tab
2. Click on **"Daily Bluesky Post Email"** workflow
3. Click **"Run workflow"** button (on the right)
4. Select branch: `main`
5. Click **"Run workflow"**

Wait ~1 minute and you should see:
- ✅ Green checkmark = Success! Email was sent
- ❌ Red X = Failed (click to see error logs)

---

## 🕐 Schedule Configuration

The workflow is set to run **daily at 9:00 UTC (6 AM Brazil time)**.

### Want a Different Time?

Edit `.github/workflows/daily-post.yml`:

```yaml
schedule:
  - cron: '0 9 * * *'  # Change this line
```

#### Common Schedules:

| Time (UTC) | Brazil Time | Cron Expression | Description |
|------------|-------------|----------------|-------------|
| 9:00 UTC | 6 AM | `0 9 * * *` | **Default - Morning** |
| 12:00 UTC | 9 AM | `0 12 * * *` | Mid-morning (Brazil) |
| 15:00 UTC | 12 PM | `0 15 * * *` | Noon (Brazil) |
| 21:00 UTC | 6 PM | `0 21 * * *` | Evening |
| 22:00 UTC | 7 PM | `0 22 * * *` | Late evening |

**Need help with cron?** Use [crontab.guru](https://crontab.guru/)

---

## 📊 Monitoring

### View Workflow Runs

1. Go to **Actions** tab
2. Click on **"Daily Bluesky Post Email"**
3. See all past runs with status

### Check Logs

Click on any run → Click on job → Expand steps to see detailed logs

### Get Notified on Failures

GitHub will email you if a workflow fails (check your GitHub notification settings).

---

## 🔧 Troubleshooting

### Workflow Not Running

**Problem:** No runs showing up in Actions tab

**Solutions:**
- Verify workflow file is in `.github/workflows/`
- Check Actions are enabled: Settings → Actions → General → Allow all actions
- Wait up to 1 hour for first scheduled run

### Authentication Failed

**Problem:** `Login failed` or `Invalid credentials`

**Solutions:**
- **Gmail:** Use an **App Password**, not your main password
  - [See guide below](#how-to-get-gmail-app-password)
- Double-check secret names match exactly (case-sensitive)
- Ensure 2FA is enabled on your Gmail account

### Email Not Sending

**Problem:** Script runs but no email received

**Solutions:**
- Check spam folder
- Verify `EMAIL_TO` is correct
- Check Gmail App Password is valid
- Ensure 2FA is enabled on Gmail account
- Check workflow logs for error messages

### Rate Limiting

**Problem:** GitHub Actions says rate limited

**Solutions:**
- This is rare on free tier
- You have 2,000 minutes/month for private repos
- Daily 2-minute run = ~60 minutes/month (well within limit)

---

## 🔄 How It Works

The workflow fetches posts using the **public Bluesky API**:
- No authentication required - reads public posts directly
- Fetches the latest post from the specified account
- Sends formatted email with post content and link
- Simple and reliable

---

## 📧 How to Get Gmail App Password

1. **Enable 2-Factor Authentication** (if not already)
   - Go to [myaccount.google.com/security](https://myaccount.google.com/security)
   - Turn on "2-Step Verification"

2. **Create App Password**
   - Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
   - Select "Mail" and your device
   - Click "Generate"
   - Copy the 16-character password (e.g., `abcd efgh ijkl mnop`)

3. **Add to GitHub Secrets**
   - Use this password for `EMAIL_PASSWORD` secret
   - **Not your regular Gmail password!**

---

## 💰 Cost & Limits

### Free Tier Includes:

- ✅ 2,000 minutes/month (private repos)
- ✅ Unlimited minutes (public repos)
- ✅ Unlimited workflows
- ✅ Unlimited scheduled jobs

### Your Usage:

- Daily run: ~2 minutes
- Monthly: ~60 minutes
- **Well within free tier!** ✅

---

## 🔐 Security Best Practices

- ✅ Use **Private repository** for your code
- ✅ Always use **App Passwords**, never main passwords
- ✅ Store all credentials as **GitHub Secrets**
- ✅ Never commit `.env` file (it's in `.gitignore`)
- ✅ Regularly rotate passwords and tokens
- ✅ Enable GitHub's **Dependabot** for security updates

---

## 🎯 Quick Commands Reference

```bash
# Clone your repo (on new machine)
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git

# Pull latest changes
git pull

# Make changes and push
git add .
git commit -m "Updated schedule"
git push

# View workflow logs (local)
# Not available - must check on GitHub Actions tab
```

---

## 📱 Mobile Access

You can monitor your workflow from GitHub mobile app:
- Download GitHub app (iOS/Android)
- Go to your repository → Actions
- See runs and status on the go

---

## 🎓 Advanced: Multiple Schedules

Want to run different scripts at different times?

Create separate workflow files:

```
.github/workflows/
  ├── daily-post.yml         # Morning email
  ├── evening-post.yml       # Evening email
  └── weekly-summary.yml     # Weekly summary
```

Each with different schedules and scripts.

---

## ✅ Success Checklist

- [ ] Repository created on GitHub
- [ ] Code pushed to GitHub
- [ ] All secrets added to repository settings
- [ ] Workflow file exists in `.github/workflows/`
- [ ] Manual test run successful
- [ ] Email received successfully
- [ ] Schedule time configured correctly
- [ ] Notifications enabled for failures

---

## 🆘 Still Having Issues?

Common issues:

1. **Secrets not working** → Check spelling and case sensitivity (only email secrets needed)
2. **Workflow not in Actions tab** → File must be in `.github/workflows/`
3. **Schedule not running** → Enable schedule in `daily-post.yml` (uncomment the schedule section)
4. **Gmail blocking** → Use App Password with 2FA enabled, not regular password

---

## 🎉 You're Done!

Your Bluesky emailer is now running in the cloud, completely free!

- ✅ Automatic daily emails
- ✅ No server to maintain
- ✅ Secure credentials storage
- ✅ Easy to monitor and debug

**Next Steps:**
- Star your repository ⭐
- Set up branch protection
- Add a README badge showing workflow status
- Consider adding error notifications

Enjoy your automated Bluesky updates! 📧✨
