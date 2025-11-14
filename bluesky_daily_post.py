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

def get_thread_posts(feed_item):
    """
    Extract the main post and all corrections from a thread.
    Returns: dict with 'main_post' (the one with images and agenda text) and 'corrections' (list of correction posts)
    """
    result = {
        'main_post': None,
        'corrections': [],
        'subject_text': None
    }
    
    post = feed_item.get('post', {})
    record = post.get('record', {})
    reply_info = feed_item.get('reply', {})
    
    # Check if this is a reply/correction
    if record.get('reply') and reply_info:
        # This is a correction post
        root_post = reply_info.get('root', {})
        parent_post = reply_info.get('parent', {})
        
        # Get the root post (the main agenda post)
        root_record = root_post.get('record', {})
        root_text = root_record.get('text', '')
        
        # Check if root has the agenda text
        if 'A agenda esportiva desta' in root_text:
            result['main_post'] = root_post
            result['subject_text'] = root_text
            
            # Add current post as a correction
            author = post.get('author', {})
            post_uri = post.get('uri', '')
            post_id = post_uri.split('/')[-1] if post_uri else ''
            
            result['corrections'].append({
                'text': record.get('text', ''),
                'created_at': record.get('createdAt', ''),
                'url': f"https://bsky.app/profile/{author.get('handle')}/post/{post_id}"
            })
    else:
        # This is a main post (not a reply)
        text = record.get('text', '')
        if 'A agenda esportiva desta' in text:
            result['main_post'] = post
            result['subject_text'] = text
    
    return result

def fetch_thread_corrections(root_uri):
    """
    Fetch all posts in the thread to find additional corrections.
    Returns a list of correction posts.
    """
    corrections = []
    
    try:
        # Get recent posts to find other replies in the thread
        url = f"{BLUESKY_API_BASE}/xrpc/app.bsky.feed.getAuthorFeed"
        params = {
            'actor': BLUESKY_HANDLE,
            'limit': 20  # Check recent posts for corrections
        }
        
        logger.debug(f"Fetching thread corrections for root URI: {root_uri}")
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        
        data = response.json()
        feed = data.get('feed', [])
        
        for feed_item in feed:
            post = feed_item.get('post', {})
            record = post.get('record', {})
            reply_data = record.get('reply', {})
            
            # Check if this post is a reply to our root post
            if reply_data and reply_data.get('root', {}).get('uri') == root_uri:
                author = post.get('author', {})
                post_uri = post.get('uri', '')
                post_id = post_uri.split('/')[-1] if post_uri else ''
                
                corrections.append({
                    'text': record.get('text', ''),
                    'created_at': record.get('createdAt', ''),
                    'url': f"https://bsky.app/profile/{author.get('handle')}/post/{post_id}"
                })
        
        if corrections:
            logger.info(f"Found {len(corrections)} correction(s) in thread")
        
    except Exception as e:
        logger.error(f"Error fetching thread corrections: {e}")
    
    return corrections

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
        
        # Parse the thread structure to detect corrections
        logger.debug("Analyzing thread structure...")
        thread_data = get_thread_posts(feed[0])
        
        # Determine which post to use as main (the one with agenda and images)
        main_post = thread_data['main_post']
        if not main_post:
            # Fallback to the latest post if no agenda post found
            logger.debug("No agenda post detected in thread, using latest post")
            main_post = feed[0].get('post', {})
        else:
            logger.info("Detected agenda post in thread structure")
        
        # Parse the main post data
        record = main_post.get('record', {})
        author = main_post.get('author', {})
        post_uri = main_post.get('uri', '')
        post_id = post_uri.split('/')[-1] if post_uri else ''
        embed = record.get('embed')
        
        post_data = {
            'text': record.get('text', ''),
            'created_at': record.get('createdAt', ''),
            'url': f"https://bsky.app/profile/{author.get('handle')}/post/{post_id}",
            'author': f"@{author.get('handle')}",
            'images': [],
            'corrections': thread_data['corrections'],
            'subject_text': thread_data.get('subject_text')
        }
        
        # Look for images in the main post
        if embed and embed.get('$type') == 'app.bsky.embed.images':
            images_data = embed.get('images', [])
            logger.info(f"Found post with {len(images_data)} image(s)")
            
            did = author.get('did')
            
            # Download and convert images to base64
            for idx, image_data in enumerate(images_data):
                image_ref = image_data.get('image', {})
                
                if image_ref.get('$type') == 'blob' and image_ref.get('ref'):
                    cid = image_ref['ref']['$link']
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
        
        # Check for additional corrections in the thread
        if main_post.get('uri'):
            logger.debug("Searching for additional corrections in thread...")
            additional_corrections = fetch_thread_corrections(main_post.get('uri'))
            
            # Merge and deduplicate corrections
            existing_urls = {corr['url'] for corr in post_data['corrections']}
            for corr in additional_corrections:
                if corr['url'] not in existing_urls:
                    post_data['corrections'].append(corr)
                    existing_urls.add(corr['url'])
            
            # Sort corrections by creation time
            post_data['corrections'].sort(key=lambda x: x['created_at'])
            
            if post_data['corrections']:
                logger.info(f"Total corrections found: {len(post_data['corrections'])}")
        
        logger.info(f"Post from {post_data['author']} at {post_data['created_at']}")
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
        
        # Build corrections section if present
        corrections_html = ""
        if post_data.get('corrections'):
            logger.info(f"Adding {len(post_data['corrections'])} correction(s) to email")
            corrections_html = '''
            <div style="background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 15px 0; border-radius: 5px;">
                <h3 style="margin-top: 0; color: #856404;">⚠️ Correções / Updates:</h3>
            '''
            for idx, correction in enumerate(post_data['corrections'], 1):
                corr_text = correction['text'].replace('\n', '<br>')
                corr_time = correction['created_at']
                corr_url = correction['url']
                corrections_html += f'''
                <div style="margin-bottom: 10px; padding: 10px; background-color: #fff; border-radius: 3px;">
                    <p style="margin: 0;"><strong>Correção {idx}:</strong> <em>{corr_time}</em></p>
                    <p style="margin: 5px 0;">{corr_text}</p>
                    <p style="margin: 0;"><a href="{corr_url}" style="font-size: 0.9em; color: #0066cc;">Ver no Bluesky</a></p>
                </div>
                '''
            corrections_html += '</div>'
        
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
            {corrections_html}
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
        
        # Use the subject text from the main post (agenda text) if available
        subject_text = post_data.get('subject_text', post_data.get('text', ''))
        if 'A agenda esportiva desta' in subject_text:
            # Extract just the agenda line for the subject
            subject_line = subject_text.split('\n')[0] if '\n' in subject_text else subject_text
            email_subject = f"📰 {subject_line}"
            logger.info(f"Using custom subject from agenda: {subject_line[:50]}...")
        else:
            email_subject = f"📰 Daily Update from {BLUESKY_HANDLE} - {datetime.now().strftime('%Y-%m-%d')}"
        
        payload = {
            "from": email_from,
            "to": [email_to],
            "subject": email_subject,
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
    logger.info(f"  Images: {len(post.get('images', []))}")
    logger.info(f"  Corrections: {len(post.get('corrections', []))}")
    
    if post.get('corrections'):
        logger.info("  Corrections found:")
        for idx, corr in enumerate(post['corrections'], 1):
            logger.info(f"    {idx}. {corr['text'][:60]}...")
    
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