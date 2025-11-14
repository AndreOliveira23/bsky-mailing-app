import os
import smtplib
import requests
import base64

try:
    import msal
except Exception:
    msal = None
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv

# Configuration
BLUESKY_HANDLE = 'esportesnatv.bsky.social'
BLUESKY_API_BASE = 'https://public.api.bsky.app'

# Load environment variables
load_dotenv()

def get_post_thread_data(feed_data):
    """
    Analyze the feed to find the main post with 'A agenda esportiva desta' 
    and collect all correction posts (replies in thread).
    
    Returns: dict with main_post, corrections list, and images
    """
    corrections = []
    main_post = None
    
    for feed_item in feed_data:
        post = feed_item.get('post', {})
        record = post.get('record', {})
        text = record.get('text', '')
        author = post.get('author', {})
        post_uri = post.get('uri', '')
        post_id = post_uri.split('/')[-1] if post_uri else ''
        
        # Check if this is the main agenda post
        if 'A agenda esportiva desta' in text:
            embed = record.get('embed')
            images = []
            
            # Extract images if available
            if embed and embed.get('$type') == 'app.bsky.embed.images':
                images_data = embed.get('images', [])
                did = author.get('did')
                
                for idx, image_data in enumerate(images_data):
                    image_ref = image_data.get('image', {})
                    if image_ref.get('$type') == 'blob' and image_ref.get('ref'):
                        cid = image_ref['ref']['$link']
                        image_url = f"https://cdn.bsky.app/img/feed_fullsize/plain/{did}/{cid}@jpeg"
                        images.append({
                            'url': image_url,
                            'alt': image_data.get('alt', '')
                        })
            
            main_post = {
                'text': text,
                'created_at': record.get('createdAt', ''),
                'url': f"https://bsky.app/profile/{author.get('handle')}/post/{post_id}",
                'author': f"@{author.get('handle')}",
                'uri': post_uri,
                'images': images
            }
        # Check if this is a correction post (starts with "Correção:")
        elif text.startswith('Correção:'):
            corrections.append({
                'text': text,
                'created_at': record.get('createdAt', ''),
                'url': f"https://bsky.app/profile/{author.get('handle')}/post/{post_id}"
            })
            
            # If this is a reply, check if parent is in the reply data
            reply_data = feed_item.get('reply', {})
            if reply_data and not main_post:
                # Try to get parent from the reply field
                root_post = reply_data.get('root', {})
                parent_post = reply_data.get('parent', {})
                
                # Check root first, then parent
                for candidate in [root_post, parent_post]:
                    if candidate:
                        candidate_record = candidate.get('record', {})
                        candidate_text = candidate_record.get('text', '')
                        
                        if 'A agenda esportiva desta' in candidate_text:
                            candidate_author = candidate.get('author', {})
                            candidate_uri = candidate.get('uri', '')
                            candidate_id = candidate_uri.split('/')[-1] if candidate_uri else ''
                            
                            # Extract images from parent
                            images = []
                            candidate_embed = candidate_record.get('embed')
                            if candidate_embed and candidate_embed.get('$type') == 'app.bsky.embed.images':
                                images_data = candidate_embed.get('images', [])
                                did = candidate_author.get('did')
                                
                                for idx, image_data in enumerate(images_data):
                                    image_ref = image_data.get('image', {})
                                    if image_ref.get('$type') == 'blob' and image_ref.get('ref'):
                                        cid = image_ref['ref']['$link']
                                        image_url = f"https://cdn.bsky.app/img/feed_fullsize/plain/{did}/{cid}@jpeg"
                                        images.append({
                                            'url': image_url,
                                            'alt': image_data.get('alt', '')
                                        })
                            
                            # Also check embed view for images
                            if not images:
                                candidate_embed_view = candidate.get('embed')
                                if candidate_embed_view and candidate_embed_view.get('$type') == 'app.bsky.embed.images#view':
                                    images_view = candidate_embed_view.get('images', [])
                                    for img_view in images_view:
                                        fullsize_url = img_view.get('fullsize')
                                        if fullsize_url:
                                            images.append({
                                                'url': fullsize_url,
                                                'alt': img_view.get('alt', '')
                                            })
                            
                            main_post = {
                                'text': candidate_text,
                                'created_at': candidate_record.get('createdAt', ''),
                                'url': f"https://bsky.app/profile/{candidate_author.get('handle')}/post/{candidate_id}",
                                'author': f"@{candidate_author.get('handle')}",
                                'uri': candidate_uri,
                                'images': images
                            }
                            break
    
    return {
        'main_post': main_post,
        'corrections': corrections
    }

def get_latest_post():
    """Fetch the latest post from the specified Bluesky account, handling threads."""
    
    try:
        # Use the public API to get author feed with more posts to catch corrections
        url = f"{BLUESKY_API_BASE}/xrpc/app.bsky.feed.getAuthorFeed"
        params = {
            'actor': BLUESKY_HANDLE,
            'limit': 10  # Get more posts to capture corrections in thread
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        feed = data.get('feed', [])
        
        if not feed:
            return None
        
        # Get thread data (main post + corrections)
        thread_data = get_post_thread_data(feed)
        
        if not thread_data['main_post']:
            # Fallback to just the latest post if no agenda post found
            post = feed[0].get('post', {})
            record = post.get('record', {})
            author = post.get('author', {})
            post_uri = post.get('uri', '')
            post_id = post_uri.split('/')[-1] if post_uri else ''
            
            return {
                'text': record.get('text', ''),
                'created_at': record.get('createdAt', ''),
                'url': f"https://bsky.app/profile/{author.get('handle')}/post/{post_id}",
                'author': f"@{author.get('handle')}",
                'corrections': [],
                'images': []
            }
        
        # Return main post with corrections
        result = thread_data['main_post']
        result['corrections'] = thread_data['corrections']
        return result
        
    except Exception as e:
        print(f"Error fetching post: {e}")
        return None

def download_image_to_memory(image_url):
    """Download an image from URL and return the binary content."""
    try:
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        return response.content
    except Exception as e:
        print(f"Error downloading image {image_url}: {e}")
        return None

def send_email(post_data):
    """Send an email with the latest post, including images as attachments."""
    from email.mime.image import MIMEImage
    
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
        
        # Use the post text as subject (extract date portion)
        subject_text = post_data.get('text', '')
        if 'A agenda esportiva desta' in subject_text:
            # Extract just the relevant part for subject line
            msg['Subject'] = f"📰 {subject_text}"
        else:
            msg['Subject'] = f"📰 Daily Update from {BLUESKY_HANDLE} - {datetime.now().strftime('%Y-%m-%d')}"

        # Format the post text for HTML (replace newlines with <br>)
        formatted_text = post_data.get('text', '').replace('\n', '<br>')

        # Format the email body
        body = f"""
        <h2>Latest Post from {post_data.get('author')}</h2>
        <p><strong>Posted at:</strong> {post_data.get('created_at')}</p>
        <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 15px 0;">
            {formatted_text}
        </div>
        """
        
        # Add corrections if any
        corrections = post_data.get('corrections', [])
        if corrections:
            body += """
            <h3 style="color: #d9534f; margin-top: 20px;">⚠️ Correções:</h3>
            """
            for correction in corrections:
                correction_text = correction.get('text', '').replace('\n', '<br>')
                body += f"""
                <div style="background-color: #fff3cd; padding: 10px; border-left: 4px solid #ffc107; margin: 10px 0;">
                    {correction_text}
                    <p style="font-size: 0.9em; color: #666; margin-top: 5px;">
                        <a href="{correction.get('url')}">Ver correção no Bluesky</a>
                    </p>
                </div>
                """
        
        # Add link to original post
        body += f"""
        <p style="margin-top: 20px;"><a href="{post_data.get('url')}">View on Bluesky</a></p>
        """
        
        # Add note about attachments if images are present
        images = post_data.get('images', [])
        if images:
            body += f"""
            <p style="font-style: italic; color: #666;">📎 {len(images)} imagem(ns) anexada(s)</p>
            """

        msg.attach(MIMEText(body, 'html'))
        
        # Attach images
        for idx, image_info in enumerate(images):
            image_url = image_info.get('url')
            image_data = download_image_to_memory(image_url)
            if image_data:
                image_attachment = MIMEImage(image_data)
                image_attachment.add_header('Content-Disposition', 'attachment', filename=f'agenda_image_{idx + 1}.jpg')
                msg.attach(image_attachment)
                print(f"Attached image {idx + 1}/{len(images)}")

        # Connect to SMTP server and send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()

            # Prefer OAuth2 if configured
            smtp_oauth2 = os.getenv('SMTP_OAUTH2', 'false').lower() == 'true'
            azure_client_id = os.getenv('AZURE_CLIENT_ID')
            azure_client_secret = os.getenv('AZURE_CLIENT_SECRET')
            azure_tenant_id = os.getenv('AZURE_TENANT_ID')

            token = None
            if smtp_oauth2 or (azure_client_id and azure_client_secret and azure_tenant_id):
                if not msal:
                    raise RuntimeError('msal package is not available. Install requirements.')

                authority = f"https://login.microsoftonline.com/{azure_tenant_id}"
                app = msal.ConfidentialClientApplication(
                    azure_client_id,
                    authority=authority,
                    client_credential=azure_client_secret,
                )

                # Use the Outlook resource scope for SMTP
                result = app.acquire_token_for_client(scopes=["https://outlook.office.com/.default"])
                token = result.get('access_token')

            if token:
                # Build XOAUTH2 auth string and authenticate
                auth_string = f"user={email_from}\x01auth=Bearer {token}\x01\x01"
                auth_b64 = base64.b64encode(auth_string.encode()).decode()
                code, resp = server.docmd("AUTH", "XOAUTH2 " + auth_b64)
                if code != 235:
                    raise RuntimeError(f"XOAUTH2 authentication failed: {code} {resp}")
            else:
                # Fallback to basic auth using password
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
