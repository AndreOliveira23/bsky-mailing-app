import os
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv
from atproto import Client, models

# File to track last sent post
LAST_SENT_FILE = 'last_sent_post.json'

def load_last_sent():
    """Load the last sent post information."""
    if os.path.exists(LAST_SENT_FILE):
        try:
            with open(LAST_SENT_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return None
    return None

def save_last_sent(post_text, timestamp):
    """Save the last sent post information."""
    with open(LAST_SENT_FILE, 'w', encoding='utf-8') as f:
        json.dump({
            'text': post_text,
            'timestamp': timestamp,
            'sent_at': datetime.now().isoformat()
        }, f, indent=2)

def get_latest_post():
    # Initialize the client
    client = Client()
    
    # Login to Bluesky (using app password is recommended)
    client.login(
        os.getenv('BLUESKY_HANDLE'),
        os.getenv('BLUESKY_PASSWORD')
    )
    
    # Get the profile of 'esportesNaTv'
    profile = client.bsky.actor.get_profile({'actor': 'esportesNaTv'})
    
    # Get the user's feed (most recent posts)
    feed = client.bsky.feed.get_author_feed({
        'actor': 'esportesNaTv',
        'limit': 1  # Only get the most recent post
    })
    
    if not feed.feed:
        return None
    
    # Get the most recent post
    latest_post = feed.feed[0].post
    
    # Format the post content
    post_text = latest_post.record.text
    post_url = f"https://bsky.app/profile/{profile.did}/post/{latest_post.uri.split('/')[-1]}"
    
    return {
        'text': post_text,
        'url': post_url,
        'timestamp': latest_post.record.created_at
    }

def send_email(subject, body):
    # Create message
    msg = MIMEMultipart()
    msg['From'] = os.getenv('EMAIL_FROM')
    msg['To'] = os.getenv('EMAIL_TO')
    msg['Subject'] = subject
    
    # Attach the body
    msg.attach(MIMEText(body, 'plain'))
    
    # Connect to SMTP server and send email
    try:
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        email_from = os.getenv('EMAIL_FROM')
        email_password = os.getenv('EMAIL_PASSWORD')
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(email_from, email_password)
            server.send_message(msg)
        print("✓ Email sent successfully!")
        return True
    except Exception as e:
        print(f"✗ Failed to send email: {e}")
        return False

def main():
    # Load environment variables
    load_dotenv()
    
    # Validate required secrets
    required_vars = ['BLUESKY_HANDLE', 'BLUESKY_PASSWORD', 'EMAIL_FROM', 'EMAIL_PASSWORD', 'EMAIL_TO']
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        print(f"✗ Error: Missing required environment variables: {', '.join(missing)}")
        return
    
    print("Fetching latest post from 'esportesNaTv'...")
    post = get_latest_post()
    
    if not post:
        print("✗ No posts found from 'esportesNaTv'")
        return
    
    # Check for duplication
    last_sent = load_last_sent()
    if last_sent and last_sent.get('text') == post['text']:
        print(f"✓ Post already sent: {post['text'][:60]}...")
        print("  Skipping to avoid duplicate email.")
        return
    
    print(f"✓ New post found: {post['text'][:60]}...")
    
    # Format the email content
    subject = f"Latest Post from esportesNaTv - {datetime.now().strftime('%Y-%m-%d')}"
    body = f"""Latest post from esportesNaTv:

{post['text']}

Posted at: {post['timestamp']}
View on Bluesky: {post['url']}
"""
    
    print("Sending email...")
    if send_email(subject, body):
        # Save to prevent duplicates
        save_last_sent(post['text'], post['timestamp'])
        print(f"✓ Saved post tracking to {LAST_SENT_FILE}")
    else:
        print("✗ Email not sent, not saving tracking info")

if __name__ == "__main__":
    main()
