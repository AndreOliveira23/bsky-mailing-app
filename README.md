# Bluesky Post Emailer

This script fetches the latest post from the 'esportesNaTv' account on Bluesky and sends it via email on a daily basis.

## Setup

1. **Install Python** (3.7 or higher) if you haven't already.

2. **Install the required packages**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure your environment variables**:
   - Rename `.env.example` to `.env`
   - Update the `.env` file with your credentials:
     - `BLUESKY_HANDLE`: Your Bluesky handle (e.g., `yourhandle.bsky.social`)
     - `BLUESKY_PASSWORD`: Your Bluesky app password (not your main password)
     - `EMAIL_FROM`: Your Gmail address
     - `EMAIL_PASSWORD`: Your Gmail app password (not your main password)
     - `EMAIL_TO`: The recipient email address

   > **Note**: For Gmail, you'll need to generate an "App Password" if you have 2FA enabled.

## Usage

To run the script manually:
```bash
python bluesky_emailer.py
```

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

## Security Note

- Never commit your `.env` file to version control
- Use app-specific passwords instead of your main account passwords
- Consider using environment variables directly on your server instead of the `.env` file in production
