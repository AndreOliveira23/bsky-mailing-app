import os
import requests
import json
import logging
import time
import base64
from datetime import datetime
from dotenv import load_dotenv
from io import BytesIO

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Configuration
BLUESKY_HANDLE = 'esportesnatv.bsky.social'
BLUESKY_API_BASE = 'https://public.api.bsky.app'
LAST_SENT_FILE = 'last_sent_post.json'
REQUEST_TIMEOUT = 30  # seconds

# Load environment variables
load_dotenv()

def load_last_sent():
    """Load the last sent post information."""
    logger.info(f"Checking for last sent post file: {LAST_SENT_FILE}")
    if os.path.exists(LAST_SENT_FILE):
        try:
            with open(LAST_SENT_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"Loaded last sent post from {data.get('sent_at', 'unknown time')}")
                return data
        except Exception as e:
            logger.warning(f"Failed to load last sent file: {e}")
            return None
    logger.info("No last sent post file found")
    return None

def save_last_sent(post_text, timestamp):
    """Save the last sent post information."""
    logger.info("Saving last sent post information")
    with open(LAST_SENT_FILE, 'w', encoding='utf-8') as f:
        json.dump({
            'text': post_text,
            'timestamp': timestamp,
            'sent_at': datetime.now().isoformat()
        }, f, indent=2)
    logger.info(f"Saved to {LAST_SENT_FILE}")

def download_image_to_base64(url):
    """Download an image and convert to base64 for embedding."""
    try:
        logger.debug(f"Downloading image from: {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Convert to base64
        image_data = base64.b64encode(response.content).decode('utf-8')
        logger.debug(f"Image converted to base64 ({len(image_data)} chars)")
        return image_data
    except Exception as e:
        logger.error(f"Failed to download image: {e}")
        return None

def get_latest_post():
    """Fetch the latest post from the specified Bluesky account with images."""
    
    try:
        # Use the public API to get author feed
        url = f"{BLUESKY_API_BASE}/xrpc/app.bsky.feed.getAuthorFeed"
        params = {
            'actor': BLUESKY_HANDLE,
            'limit': 10  # Get more posts to find one with images
        }
        
        logger.info(f"Fetching latest post from {BLUESKY_HANDLE}")
        logger.debug(f"Request URL: {url}")
        logger.debug(f"Request params: {params}")
        
        start_time = time.time()
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        elapsed = time.time() - start_time
        logger.info(f"API request completed in {elapsed:.2f}s (status: {response.status_code})")
        
        response.raise_for_status()
        
        data = response.json()
        feed = data.get('feed', [])
        logger.info(f"Retrieved {len(feed)} post(s) from feed")
        
        if not feed:
            logger.warning("Feed is empty, no posts found")
            return None
        
        # Look for the latest post (preferably with images)
        for feed_item in feed:
            post = feed_item.get('post', {})
            record = post.get('record', {})
            author = post.get('author', {})
            post_uri = post.get('uri', '')
            post_id = post_uri.split('/')[-1] if post_uri else ''
            embed = record.get('embed')
            
            post_data = {
                'text': record.get('text', ''),
                'created_at': record.get('createdAt', ''),
                'url': f"https://bsky.app/profile/{author.get('handle')}/post/{post_id}",
                'author': f"@{author.get('handle')}",
                'images': []
            }
            
            # Check if post has images
            if embed and embed.get('$type') == 'app.bsky.embed.images':
                images_data = embed.get('images', [])
                logger.info(f"Found post with {len(images_data)} image(s)")
                
                # Download and convert images to base64
                for idx, image_data in enumerate(images_data):
                    image_ref = image_data.get('image', {})
                    
                    if image_ref.get('$type') == 'blob' and image_ref.get('ref'):
                        cid = image_ref['ref']['$link']
                        did = author.get('did')
                        image_url = f"https://cdn.bsky.app/img/feed_fullsize/plain/{did}/{cid}@jpeg"
                        
                        logger.info(f"Downloading image {idx + 1}/{len(images_data)}...")
                        base64_image = download_image_to_base64(image_url)
                        
                        if base64_image:
                            post_data['images'].append({
                                'base64': base64_image,
                                'alt': image_data.get('alt', ''),
                                'filename': f'image_{idx + 1}.jpg'
                            })
                
                if post_data['images']:
                    logger.info(f"Successfully downloaded {len(post_data['images'])} image(s)")
                    logger.info(f"Post from {post_data['author']} at {post_data['created_at']}")
                    return post_data
            
            # If we're looking at the first post (latest), return it even without images
            if feed_item == feed[0]:
                logger.info(f"Latest post has no images, but returning it anyway")
                logger.info(f"Post from {post_data['author']} at {post_data['created_at']}")
                return post_data
        
        # Return first post if nothing found with images
        post = feed[0].get('post', {})
        record = post.get('record', {})
        author = post.get('author', {})
        post_uri = post.get('uri', '')
        post_id = post_uri.split('/')[-1] if post_uri else ''
        
        post_data = {
            'text': record.get('text', ''),
            'created_at': record.get('createdAt', ''),
            'url': f"https://bsky.app/profile/{author.get('handle')}/post/{post_id}",
            'author': f"@{author.get('handle')}",
            'images': []
        }
        logger.info(f"Successfully parsed post from {post_data['author']} at {post_data['created_at']}")
        return post_data
        
    except requests.Timeout:
        logger.error(f"Timeout after {REQUEST_TIMEOUT}s while fetching post from Bluesky API")
        return None
    except requests.RequestException as e:
        logger.error(f"Network error fetching post: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching post: {e}", exc_info=True)
        return None

def send_email_resend(post_data):
    """Send an email using Resend API."""
    logger.info("Starting email send process (Resend API)")
    
    # Get configuration from environment
    resend_api_key = os.getenv('RESEND_API_KEY')
    email_from = os.getenv('EMAIL_FROM')  # Must be verified domain or use onboarding@resend.dev for testing
    email_to = os.getenv('EMAIL_TO')
    
    logger.debug(f"Email Config: from={email_from}, to={email_to}")
    
    if not all([resend_api_key, email_from, email_to]):
        logger.error("Email configuration is incomplete")
        logger.error(f"  RESEND_API_KEY: {'✓' if resend_api_key else '✗ Missing'}")
        logger.error(f"  EMAIL_FROM: {'✓' if email_from else '✗ Missing'}")
        logger.error(f"  EMAIL_TO: {'✓' if email_to else '✗ Missing'}")
        return False
    
    try:
        logger.info("Composing email message")
        start_time = time.time()
        
        # Format the post text for HTML (replace newlines with <br>)
        formatted_text = post_data.get('text', '').replace('\n', '<br>')
        
        # Format the email body (images will be sent as attachments)
        images = post_data.get('images', [])
        images_info = ""
        if images:
            logger.info(f"Preparing {len(images)} image(s) as attachments")
            images_info = f'<p style="color: #666;"><em>📎 {len(images)} image(s) attached</em></p>'
        
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #333;">Latest Post from {post_data.get('author')}</h2>
            <p style="color: #666;"><strong>Posted at:</strong> {post_data.get('created_at')}</p>
            <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 15px 0;">
                {formatted_text}
            </div>
            {images_info}
            <p><a href="{post_data.get('url')}" style="color: #0066cc;">View on Bluesky</a></p>
        </div>
        """
        
        # Prepare attachments array for Resend API
        attachments = []
        for img in images:
            attachments.append({
                'content': img.get('base64', ''),
                'filename': img.get('filename', 'image.jpg')
            })
        
        # Send via Resend API
        logger.info("Sending email via Resend API...")
        
        url = "https://api.resend.com/emails"
        headers = {
            "Authorization": f"Bearer {resend_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "from": email_from,
            "to": [email_to],
            "subject": f"📰 Daily Update from {BLUESKY_HANDLE} - {datetime.now().strftime('%Y-%m-%d')}",
            "html": html_body
        }
        
        # Add attachments if present
        if attachments:
            payload['attachments'] = attachments
            logger.info(f"Adding {len(attachments)} attachment(s) to email")
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            elapsed = time.time() - start_time
            logger.info(f"✓ Email sent successfully to {email_to} in {elapsed:.2f}s")
            return True
        else:
            logger.error(f"✗ Failed to send email: HTTP {response.status_code}")
            logger.error(f"  Response: {response.text}")
            return False
            
    except requests.RequestException as e:
        logger.error(f"✗ Network error sending email: {e}")
        return False
    except Exception as e:
        logger.error(f"✗ Error sending email: {e}", exc_info=True)
        return False

def main():
    logger.info("="*60)
    logger.info("Starting Bluesky Daily Post Script (Resend)")
    logger.info("="*60)
    start_time = time.time()
    
    logger.info(f"Fetching latest post from @{BLUESKY_HANDLE}...")
    post = get_latest_post()
    
    if not post:
        logger.error("✗ No posts found or error occurred while fetching post.")
        logger.info(f"Total execution time: {time.time() - start_time:.2f}s")
        return
    
    # Check for duplication
    #last_sent = load_last_sent()
    #if last_sent and last_sent.get('text') == post['text']:
    #    logger.info(f"✓ Post already sent: {post['text'][:60]}...")
    #    logger.info("  Skipping to avoid duplicate email.")
    #    logger.info(f"Total execution time: {time.time() - start_time:.2f}s")
    #    return
    
    logger.info(f"✓ New post found from {post['created_at']}")
    logger.info(f"  Content preview: {post['text'][:60]}...")
    
    if send_email_resend(post):
        # Save to prevent duplicates
        save_last_sent(post['text'], post['created_at'])
        logger.info(f"✓ Saved post tracking to {LAST_SENT_FILE}")
    else:
        logger.error("✗ Email not sent, not saving tracking info")
    
    total_time = time.time() - start_time
    logger.info("="*60)
    logger.info(f"Script completed in {total_time:.2f}s")
    logger.info("="*60)

if __name__ == "__main__":
    main()
