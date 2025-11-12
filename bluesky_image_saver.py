import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration
BLUESKY_HANDLE = 'esportesnatv.bsky.social'
BLUESKY_API_BASE = 'https://public.api.bsky.app'
IMAGES_FOLDER = 'post_images'

def ensure_images_folder():
    """Create the images folder if it doesn't exist."""
    if not os.path.exists(IMAGES_FOLDER):
        os.makedirs(IMAGES_FOLDER)
        print(f"Created folder: {IMAGES_FOLDER}")

def download_image(url, filename):
    """Download an image from a URL and save it locally."""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        filepath = os.path.join(IMAGES_FOLDER, filename)
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"Downloaded: {filename}")
        return filepath
    except Exception as e:
        print(f"Error downloading image {url}: {e}")
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
        
        print(f"Fetching feed from: {url}")
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        feed = data.get('feed', [])
        
        if not feed:
            print("No posts found.")
            return None
        
        print(f"Found {len(feed)} posts in feed")
        
        # Find the first post with images (optionally matching search text)
        for idx, feed_item in enumerate(feed):
            post = feed_item.get('post', {})
            record = post.get('record', {})
            post_text = record.get('text', '')
            embed = record.get('embed')
            
            # If search_text is provided, check if it matches
            if search_text and search_text not in post_text:
                continue
            
            if search_text and search_text in post_text:
                print(f"✓ Found matching text in post #{idx + 1}")
            
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
                    
                    print(f"Found post with {len(images_data)} image(s)")
                    
                    # Process each image
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    for idx, image_data in enumerate(images_data):
                        # Get the image URL (fullsize)
                        image_ref = image_data.get('image', {})
                        
                        # Construct the CDN URL for the image
                        # The ref contains the CID (content identifier) that we need
                        if image_ref.get('$type') == 'blob' and image_ref.get('ref'):
                            cid = image_ref['ref']['$link']
                            did = author.get('did')
                            image_url = f"https://cdn.bsky.app/img/feed_fullsize/plain/{did}/{cid}@jpeg"
                            
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
                    
                    return post_data
        
        print("No posts with images found in the recent feed.")
        return None
        
    except Exception as e:
        print(f"Error fetching post: {e}")
        import traceback
        traceback.print_exc()
        return None

def save_post_info(post_data):
    """Save post information to a text file."""
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
    
    print(f"Post info saved to: {info_filename}")

def main():
    # Search for a specific post
    search_text = "A agenda esportiva deste DOMINGO (09/11/2025)"
    
    print(f"Searching for post containing: '{search_text}'")
    print(f"From account: @{BLUESKY_HANDLE}...")
    
    # Ensure the images folder exists
    ensure_images_folder()
    
    # Get the post with images matching the search text
    post = get_latest_post_with_images(search_text=search_text)
    
    if post and post['images']:
        print(f"\n✓ Found matching post from {post['created_at']}")
        print(f"✓ Post text: {post['text'][:150]}...")
        print(f"✓ Downloaded {len(post['images'])} image(s)")
        
        # Save post information
        save_post_info(post)
        
        print(f"\n✓ All files saved to '{IMAGES_FOLDER}' folder")
    else:
        print("✗ No matching posts with images found or error occurred while fetching post.")

if __name__ == "__main__":
    main()
