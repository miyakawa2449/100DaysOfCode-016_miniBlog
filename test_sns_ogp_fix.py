#!/usr/bin/env python3
"""
Test script to verify SNS OGP functionality improvements
"""
import sys
from app import app
from models import db, ArticleBlock
from block_utils import detect_sns_platform, fetch_sns_ogp_data

def test_sns_platform_detection():
    """Test SNS platform detection for various URLs"""
    test_urls = [
        'https://x.com/miyakawa2449/status/1938166417775567042',
        'https://youtu.be/__lLkYY34NA?si=q-VC8AMmLcRKMJ0l',
        'https://www.instagram.com/p/DLYgyzAz7SG/?utm_source=ig_web_copy_link',
        'https://fb.watch/AtJ6-H7uor/',
        'https://www.threads.com/@hideo_kojima/post/DLYTl87zVO4?xmt=AQF0HleuJozBG1Y1Gsy4-EVZi4KQsfBdYPpZ5Swfx5XA3w'
    ]
    
    print("=== SNS Platform Detection Test ===")
    for url in test_urls:
        platform = detect_sns_platform(url)
        print(f"URL: {url}")
        print(f"Detected Platform: {platform}")
        print()

def test_sns_ogp_fetching():
    """Test SNS OGP data fetching"""
    test_cases = [
        ('https://x.com/miyakawa2449/status/1938166417775567042', 'twitter'),
        ('https://youtu.be/__lLkYY34NA?si=q-VC8AMmLcRKMJ0l', 'youtube'),
        ('https://www.instagram.com/p/DLYgyzAz7SG/?utm_source=ig_web_copy_link', 'instagram'),
        ('https://fb.watch/AtJ6-H7uor/', 'facebook'),
        ('https://www.threads.com/@hideo_kojima/post/DLYTl87zVO4?xmt=AQF0HleuJozBG1Y1Gsy4-EVZi4KQsfBdYPpZ5Swfx5XA3w', 'threads')
    ]
    
    print("=== SNS OGP Fetching Test ===")
    for url, platform in test_cases:
        print(f"Testing {platform.upper()}: {url[:50]}...")
        try:
            ogp_data = fetch_sns_ogp_data(url, platform)
            if ogp_data:
                print(f"  ✓ Success!")
                print(f"    Title: {ogp_data.get('title', 'N/A')}")
                print(f"    Description: {ogp_data.get('description', 'N/A')[:60]}...")
                print(f"    Site Name: {ogp_data.get('site_name', 'N/A')}")
                print(f"    Image: {'Yes' if ogp_data.get('image') else 'No'}")
            else:
                print(f"  ✗ Failed to fetch OGP data")
        except Exception as e:
            print(f"  ✗ Error: {e}")
        print()

def update_existing_sns_blocks():
    """Update existing SNS blocks with OGP data"""
    print("=== Updating Existing SNS Blocks ===")
    
    with app.app_context():
        # Get all SNS blocks without OGP data - use simpler query
        from models import BlockType
        sns_block_type = BlockType.query.filter_by(type_name='sns_embed').first()
        if not sns_block_type:
            print("SNS embed block type not found!")
            return
        
        sns_blocks = ArticleBlock.query.filter(
            ArticleBlock.block_type_id == sns_block_type.id,
            ArticleBlock.embed_url.isnot(None),
            db.or_(
                ArticleBlock.ogp_title.is_(None),
                ArticleBlock.ogp_title == ''
            )
        ).all()
        
        print(f"Found {len(sns_blocks)} SNS blocks without OGP data")
        
        for block in sns_blocks:
            print(f"Processing block {block.id}: {block.embed_url}")
            
            try:
                platform = detect_sns_platform(block.embed_url)
                if platform:
                    print(f"  Detected platform: {platform}")
                    ogp_data = fetch_sns_ogp_data(block.embed_url, platform)
                    
                    if ogp_data:
                        print(f"  ✓ OGP data fetched successfully")
                        
                        # Update the block
                        block.embed_platform = platform
                        block.ogp_title = ogp_data.get('title', '')
                        block.ogp_description = ogp_data.get('description', '')
                        block.ogp_site_name = ogp_data.get('site_name', '')
                        block.ogp_image = ogp_data.get('image', '')
                        block.ogp_url = block.embed_url
                        
                        # Set to OGP card mode if no display mode is set
                        current_settings = block.get_settings_json()
                        if not current_settings.get('display_mode'):
                            current_settings['display_mode'] = 'ogp_card'
                            block.set_settings_json(current_settings)
                        
                        print(f"    Title: {block.ogp_title}")
                        print(f"    Site: {block.ogp_site_name}")
                        
                        db.session.commit()
                    else:
                        print(f"  ✗ Failed to fetch OGP data")
                else:
                    print(f"  ✗ Platform not detected")
            
            except Exception as e:
                print(f"  ✗ Error: {e}")
                db.session.rollback()
            
            print()

def main():
    """Main test function"""
    print("Testing SNS OGP functionality improvements\n")
    
    # Test platform detection
    test_sns_platform_detection()
    
    # Test OGP fetching
    test_sns_ogp_fetching()
    
    # Update existing blocks
    if len(sys.argv) > 1 and sys.argv[1] == '--update':
        update_existing_sns_blocks()
    else:
        print("To update existing SNS blocks, run: python test_sns_ogp_fix.py --update")

if __name__ == '__main__':
    main()