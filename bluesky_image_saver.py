import os
import requests
import logging
import time
from datetime import datetime
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Configuration
BLUESKY_HANDLE = 'esportesnatv.bsky.social'
BLUESKY_API_BASE = 'https://public.api.bsky.app'
IMAGES_FOLDER = 'post_images'
REQUEST_TIMEOUT = 30  # seconds
IMAGE_DOWNLOAD_TIMEOUT = 60  # seconds for image downloads

def ensure_images_folder():
    """Create the images folder if it doesn't exist."""
    if not os.path.exists(IMAGES_FOLDER):
        os.makedirs(IMAGES_FOLDER)
        logger.info(f"Created folder: {IMAGES_FOLDER}")
    else:
        logger.debug(f"Images folder already exists: {IMAGES_FOLDER}")

def download_image(url, filename):
    """Download an image from a URL and save it locally."""
    logger.info(f"Downloading image: {filename}")
    logger.debug(f"Image URL: {url}")
    
    try:
        start_time = time.time()
        response = requests.get(url, stream=True, timeout=IMAGE_DOWNLOAD_TIMEOUT)
        logger.debug(f"Image request completed in {time.time() - start_time:.2f}s (status: {response.status_code})")
        
        response.raise_for_status()
        
        filepath = os.path.join(IMAGES_FOLDER, filename)
        bytes_written = 0
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                bytes_written += len(chunk)
        
        elapsed = time.time() - start_time
        size_mb = bytes_written / (1024 * 1024)
        logger.info(f"✓ Downloaded: {filename} ({size_mb:.2f} MB in {elapsed:.2f}s)")
        return filepath
        
    except requests.Timeout:
        logger.error(f"Timeout after {IMAGE_DOWNLOAD_TIMEOUT}s downloading image {filename}")
        return None
    except requests.RequestException as e:
        logger.error(f"Network error downloading image {url}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error downloading image {url}: {e}", exc_info=True)
        return None

def get_latest_post_with_images(search_text=None):
    """Fetch the latest post from the specified Bluesky account and download images."""
    
    try:
        # Use the public API to get author feed
        url = f"{BLUESKY_API_BASE}/xrpc/app.bsky.feed.getAuthorFeed"
        params = {
            'actor': BLUESKY_HANDLE,
            'limit': 50  # Increase limit to search through more posts
        }
        
        logger.info(f"Fetching feed from: {url}")
        logger.debug(f"Request params: {params}")
        
        start_time = time.time()
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        elapsed = time.time() - start_time
        logger.info(f"API request completed in {elapsed:.2f}s (status: {response.status_code})")
        
        response.raise_for_status()
        
        data = response.json()
        feed = data.get('feed', [])
        
        if not feed:
            logger.warning("No posts found in feed.")
            return None
        
        logger.info(f"Found {len(feed)} posts in feed")
        
        # Find the first post with images (optionally matching search text)
        logger.info(f"Searching through {len(feed)} posts...")
        
        for idx, feed_item in enumerate(feed):
            post = feed_item.get('post', {})
            record = post.get('record', {})
            post_text = record.get('text', '')
            embed = record.get('embed')
            
            logger.debug(f"Checking post #{idx + 1}")
            
            # If search_text is provided, check if it matches
            if search_text and search_text not in post_text:
                continue
            
            if search_text and search_text in post_text:
                logger.info(f"✓ Found matching text in post #{idx + 1}")
            
            # Check if post has embedded images
            if embed and embed.get('$type') == 'app.bsky.embed.images':
                images_data = embed.get('images', [])
                
                if images_data:
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
                    
                    logger.info(f"Found post with {len(images_data)} image(s)")
                    logger.debug(f"Post created at: {record.get('createdAt', 'unknown')}")
                    
                    # Process each image
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    download_start = time.time()
                    logger.info(f"Starting download of {len(images_data)} image(s)...")
                    
                    for idx, image_data in enumerate(images_data):
                        # Get the image URL (fullsize)
                        image_ref = image_data.get('image', {})
                        
                        # Construct the CDN URL for the image
                        # The ref contains the CID (content identifier) that we need
                        if image_ref.get('$type') == 'blob' and image_ref.get('ref'):
                            cid = image_ref['ref']['$link']
                            did = author.get('did')
                            image_url = f"https://cdn.bsky.app/img/feed_fullsize/plain/{did}/{cid}@jpeg"
                            
                            logger.debug(f"Processing image {idx + 1}/{len(images_data)}")
                            
                            # Create filename
                            handle_short = BLUESKY_HANDLE.split('.')[0]
                            filename = f"{handle_short}_{timestamp}_image_{idx + 1}.jpg"
                            
                            # Download the image
                            filepath = download_image(image_url, filename)
                            if filepath:
                                post_data['images'].append({
                                    'filepath': filepath,
                                    'alt_text': image_data.get('alt', '')
                                })
                    
                    download_elapsed = time.time() - download_start
                    logger.info(f"All images downloaded in {download_elapsed:.2f}s")
                    return post_data
        
        logger.warning("No posts with images found in the recent feed.")
        return None
        
    except requests.Timeout:
        logger.error(f"Timeout after {REQUEST_TIMEOUT}s while fetching post from Bluesky API")
        return None
    except requests.RequestException as e:
        logger.error(f"Network error fetching post: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching post: {e}", exc_info=True)
        return None

def save_post_info(post_data):
    """Save post information to a text file."""
    logger.info("Saving post information to file")
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    info_filename = os.path.join(IMAGES_FOLDER, f"{BLUESKY_HANDLE}_{timestamp}_info.txt")
    
    with open(info_filename, 'w', encoding='utf-8') as f:
        f.write(f"Post from: {post_data['author']}\n")
        f.write(f"Posted at: {post_data['created_at']}\n")
        f.write(f"URL: {post_data['url']}\n")
        f.write(f"\nPost text:\n{post_data['text']}\n")
        f.write(f"\nImages downloaded: {len(post_data['images'])}\n")
        for idx, img in enumerate(post_data['images'], 1):
            f.write(f"\nImage {idx}:\n")
            f.write(f"  File: {img['filepath']}\n")
            if img['alt_text']:
                f.write(f"  Alt text: {img['alt_text']}\n")
    
    logger.info(f"✓ Post info saved to: {info_filename}")

def main():
    logger.info("="*60)
    logger.info("Starting Bluesky Image Saver Script")
    logger.info("="*60)
    start_time = time.time()
    
    # Search for a specific post
    search_text = "A agenda esportiva deste DOMINGO (09/11/2025)"
    
    logger.info(f"Searching for post containing: '{search_text}'")
    logger.info(f"From account: @{BLUESKY_HANDLE}")
    
    # Ensure the images folder exists
    ensure_images_folder()
    
    # Get the post with images matching the search text
    post = get_latest_post_with_images(search_text=search_text)
    
    if post and post['images']:
        logger.info(f"\n✓ Found matching post from {post['created_at']}")
        logger.info(f"✓ Post text: {post['text'][:150]}...")
        logger.info(f"✓ Downloaded {len(post['images'])} image(s)")
        
        # Save post information
        save_post_info(post)
        
        logger.info(f"\n✓ All files saved to '{IMAGES_FOLDER}' folder")
    else:
        logger.error("✗ No matching posts with images found or error occurred while fetching post.")
    
    total_time = time.time() - start_time
    logger.info("="*60)
    logger.info(f"Script completed in {total_time:.2f}s")
    logger.info("="*60)

if __name__ == "__main__":
    main()
