import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from dotenv import load_dotenv
from atproto import Client, models

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
        with smtplib.SMTP(os.getenv('SMTP_SERVER'), int(os.getenv('SMTP_PORT'))) as server:
            server.starttls()
            server.login(os.getenv('EMAIL_FROM'), os.getenv('EMAIL_PASSWORD'))
            server.send_message(msg)
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

def main():
    # Load environment variables
    load_dotenv()
    
    print("Fetching latest post from 'esportesNaTv'...")
    post = get_latest_post()
    
    if post:
        # Format the email content
        subject = f"Latest Post from esportesNaTv - {datetime.now().strftime('%Y-%m-%d')}"
        body = f"""Latest post from esportesNaTv:
        
        {post['text']}
        
        Posted at: {post['timestamp']}
        View on Bluesky: {post['url']}
        """
        
        print("Sending email...")
        send_email(subject, body)
    else:
        print("No posts found from 'esportesNaTv'")

if __name__ == "__main__":
    main()
