import os
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv

# Configuration
BLUESKY_HANDLE = 'esportesnatv.bsky.social'
BLUESKY_API_BASE = 'https://public.api.bsky.app'

# Load environment variables
load_dotenv()

def get_latest_post():
    """Fetch the latest post from the specified Bluesky account."""
    
    try:
        # Use the public API to get author feed
        url = f"{BLUESKY_API_BASE}/xrpc/app.bsky.feed.getAuthorFeed"
        params = {
            'actor': BLUESKY_HANDLE,
            'limit': 1
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        feed = data.get('feed', [])
        
        if not feed:
            return None
            
        post = feed[0].get('post', {})
        record = post.get('record', {})
        author = post.get('author', {})
        post_uri = post.get('uri', '')
        post_id = post_uri.split('/')[-1] if post_uri else ''
        
        return {
            'text': record.get('text', ''),
            'created_at': record.get('createdAt', ''),
            'url': f"https://bsky.app/profile/{author.get('handle')}/post/{post_id}",
            'author': f"@{author.get('handle')}"
        }
    except Exception as e:
        print(f"Error fetching post: {e}")
        return None

def send_email(post_data):
    """Send an email with the latest post."""
    # Get email configuration from environment
    email_from = os.getenv('EMAIL_FROM')
    email_to = os.getenv('EMAIL_TO')
    email_password = os.getenv('EMAIL_PASSWORD')
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    
    if not all([email_from, email_password, email_to]):
        print("Email configuration is incomplete. Please check your configuration.")
        return False
    
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = email_from
            msg['To'] = email_to
            msg['Subject'] = f"📰 Daily Update from {BLUESKY_HANDLE} - {datetime.now().strftime('%Y-%m-%d')}"
            
            # Format the post text for HTML (replace newlines with <br>)
            formatted_text = post_data['text'].replace('\n', '<br>')
            
            # Format the email body
            body = f"""
            <h2>Latest Post from {post_data['author']}</h2>
            <p><strong>Posted at:</strong> {post_data['created_at']}</p>
            <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 15px 0;">
                {formatted_text}
            </div>
            <p><a href="{post_data['url']}">View on Bluesky</a></p>
            """
            
            msg.attach(MIMEText(body, 'html'))
        
        # Connect to SMTP server and send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(email_from, email_password)
            server.send_message(msg)
            
        print(f"Email sent successfully to {email_to}")
        return True
        
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def main():
    print(f"Fetching latest post from @{BLUESKY_HANDLE}...")
    post = get_latest_post()
    
    if post:
        print(f"Found post from {post['created_at']}")
        send_email(post)
    else:
        print("No posts found or error occurred while fetching post.")

if __name__ == "__main__":
    main()
