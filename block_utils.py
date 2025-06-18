"""
ブロック型エディタ用ユーティリティ関数
画像処理、SNS埋込、OGP取得などの機能
"""
import os
import re
import json
import time
import requests
from PIL import Image
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup
from werkzeug.utils import secure_filename
from flask import current_app
import logging

logger = logging.getLogger(__name__)

# SNSプラットフォーム検出パターン
SNS_PATTERNS = {
    'twitter': [r'twitter\.com', r'x\.com'],
    'facebook': [r'facebook\.com', r'fb\.com'],
    'instagram': [r'instagram\.com'],
    'threads': [r'threads\.net'],
    'youtube': [r'youtube\.com', r'youtu\.be']
}

def detect_sns_platform(url):
    """URLからSNSプラットフォームを自動検出"""
    if not url:
        return None
    
    url_lower = url.lower()
    for platform, patterns in SNS_PATTERNS.items():
        if any(re.search(pattern, url_lower) for pattern in patterns):
            return platform
    return None

def extract_sns_id(url, platform):
    """プラットフォーム固有のIDを抽出"""
    if not url or not platform:
        return None
    
    try:
        if platform == 'twitter':
            # Twitter/X投稿ID抽出: https://twitter.com/user/status/1234567890
            match = re.search(r'/status/(\d+)', url)
            return match.group(1) if match else None
            
        elif platform == 'youtube':
            # YouTube動画ID抽出
            if 'youtu.be' in url:
                # https://youtu.be/VIDEO_ID
                return url.split('/')[-1].split('?')[0]
            else:
                # https://www.youtube.com/watch?v=VIDEO_ID
                parsed = urlparse(url)
                return parse_qs(parsed.query).get('v', [None])[0]
                
        elif platform == 'instagram':
            # Instagram投稿ID抽出: https://www.instagram.com/p/POST_ID/
            match = re.search(r'/p/([^/]+)/', url)
            return match.group(1) if match else None
            
        elif platform == 'facebook':
            # Facebook投稿ID抽出（複数パターン対応）
            patterns = [
                r'/posts/(\d+)',
                r'/permalink/(\d+)',
                r'story_fbid=(\d+)'
            ]
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    return match.group(1)
            return None
            
        elif platform == 'threads':
            # Threads投稿ID抽出: https://www.threads.net/@user/post/POST_ID
            match = re.search(r'/post/([^/]+)', url)
            return match.group(1) if match else None
            
    except Exception as e:
        logger.error(f"SNS ID extraction error for {url}: {e}")
        return None
    
    return None

def generate_sns_embed_html(url, platform, sns_id):
    """SNS埋込HTML生成（oEmbedやプラットフォーム固有のembed形式）"""
    try:
        if platform == 'twitter':
            return f'''
            <blockquote class="twitter-tweet">
                <a href="{url}"></a>
            </blockquote>
            <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>
            '''
        
        elif platform == 'youtube':
            return f'''
            <div class="youtube-embed">
                <iframe width="560" height="315" 
                        src="https://www.youtube.com/embed/{sns_id}" 
                        title="YouTube video player" 
                        frameborder="0" 
                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                        allowfullscreen>
                </iframe>
            </div>
            '''
        
        elif platform == 'instagram':
            return f'''
            <blockquote class="instagram-media" data-instgrm-permalink="{url}">
                <a href="{url}"></a>
            </blockquote>
            <script async src="//www.instagram.com/embed.js"></script>
            '''
        
        elif platform == 'facebook':
            return f'''
            <div class="fb-post" data-href="{url}"></div>
            <div id="fb-root"></div>
            <script async defer crossorigin="anonymous" 
                    src="https://connect.facebook.net/ja_JP/sdk.js#xfbml=1&version=v18.0">
            </script>
            '''
        
        elif platform == 'threads':
            # Threadsは現在埋込機能が限定的
            return f'''
            <div class="threads-embed">
                <a href="{url}" target="_blank" rel="noopener">
                    Threadsで見る
                </a>
            </div>
            '''
        
    except Exception as e:
        logger.error(f"SNS embed HTML generation error: {e}")
    
    # フォールバック: シンプルなリンク
    return f'<a href="{url}" target="_blank" rel="noopener">{url}</a>'

def fetch_ogp_data(url):
    """URLからOGP情報を取得"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        ogp_data = {
            'title': None,
            'description': None,
            'image': None,
            'site_name': None,
            'url': url
        }
        
        # OGPタグ取得
        og_tags = soup.find_all('meta', property=lambda x: x and x.startswith('og:'))
        for tag in og_tags:
            property_name = tag.get('property', '').replace('og:', '')
            content = tag.get('content', '')
            if property_name in ogp_data and content:
                ogp_data[property_name] = content
        
        # フォールバック: title、description
        if not ogp_data['title']:
            title_tag = soup.find('title')
            if title_tag:
                ogp_data['title'] = title_tag.get_text().strip()
        
        if not ogp_data['description']:
            desc_tag = soup.find('meta', attrs={'name': 'description'})
            if desc_tag:
                ogp_data['description'] = desc_tag.get('content', '').strip()
        
        return ogp_data
        
    except Exception as e:
        logger.error(f"OGP fetch error for {url}: {e}")
        return None

def process_block_image(image_file, block_type, block_id=None):
    """ブロック用画像の処理（アップロード、リサイズ、トリミング）"""
    if not image_file:
        return None
    
    try:
        # ファイル名生成
        timestamp = int(time.time())
        file_ext = os.path.splitext(secure_filename(image_file.filename))[1]
        filename = f"block_{block_type}_{block_id or 'new'}_{timestamp}{file_ext}"
        
        # アップロードフォルダ設定
        upload_folder = current_app.config.get('BLOCK_IMAGE_UPLOAD_FOLDER', 'static/uploads/blocks')
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        
        image_path = os.path.join(upload_folder, filename)
        temp_path = os.path.join(upload_folder, f"temp_{filename}")
        
        # 一時保存
        image_file.save(temp_path)
        
        # 画像処理
        with Image.open(temp_path) as img:
            # RGBA→RGBの変換
            if img.mode in ('RGBA', 'LA', 'P'):
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = rgb_img
            
            # ブロックタイプ別リサイズ
            if block_type == 'image':
                # 1:1比率、700px
                target_size = (700, 700)
            elif block_type == 'featured_image':
                # 16:9比率、800px幅
                target_size = (800, 450)
            else:
                # デフォルト
                target_size = (600, 400)
            
            # リサイズ
            resized_img = img.resize(target_size, Image.Resampling.LANCZOS)
            resized_img.save(image_path, format='JPEG', quality=85)
        
        # 一時ファイル削除
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        # 相対パスを返す
        return os.path.relpath(image_path, current_app.static_folder)
        
    except Exception as e:
        logger.error(f"Block image processing error: {e}")
        return None

def process_block_image_with_crop(image_file, block_type, crop_data, block_id=None):
    """トリミング情報を使用した画像処理"""
    if not image_file or not crop_data:
        return process_block_image(image_file, block_type, block_id)
    
    try:
        # クロップデータ解析
        if isinstance(crop_data, str):
            crop_data = json.loads(crop_data)
        
        crop_x = int(float(crop_data.get('x', 0)))
        crop_y = int(float(crop_data.get('y', 0)))
        crop_width = int(float(crop_data.get('width', 0)))
        crop_height = int(float(crop_data.get('height', 0)))
        
        if crop_width <= 0 or crop_height <= 0:
            return process_block_image(image_file, block_type, block_id)
        
        # ファイル名生成
        timestamp = int(time.time())
        file_ext = os.path.splitext(secure_filename(image_file.filename))[1]
        filename = f"block_{block_type}_{block_id or 'new'}_{timestamp}{file_ext}"
        
        upload_folder = current_app.config.get('BLOCK_IMAGE_UPLOAD_FOLDER', 'static/uploads/blocks')
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        
        image_path = os.path.join(upload_folder, filename)
        temp_path = os.path.join(upload_folder, f"temp_{filename}")
        
        # 一時保存
        image_file.save(temp_path)
        
        # 画像処理
        with Image.open(temp_path) as img:
            # RGBA→RGB変換
            if img.mode in ('RGBA', 'LA', 'P'):
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = rgb_img
            
            # クロップの境界チェック
            img_width, img_height = img.size
            crop_x = max(0, min(crop_x, img_width - 1))
            crop_y = max(0, min(crop_y, img_height - 1))
            crop_width = min(crop_width, img_width - crop_x)
            crop_height = min(crop_height, img_height - crop_y)
            
            # クロップ実行
            crop_box = (crop_x, crop_y, crop_x + crop_width, crop_y + crop_height)
            cropped_img = img.crop(crop_box)
            
            # ブロックタイプ別の最適化処理
            if block_type == 'image':
                # 1:1比率、700px（正方形）
                final_size = (700, 700)
                # クロップ済み画像をアスペクト比を保ちながら正方形に収める
                cropped_img.thumbnail((700, 700), Image.Resampling.LANCZOS)
                
                # 正方形の背景を作成（白背景）
                background = Image.new('RGB', final_size, (255, 255, 255))
                
                # 中央に配置
                paste_x = (final_size[0] - cropped_img.width) // 2
                paste_y = (final_size[1] - cropped_img.height) // 2
                background.paste(cropped_img, (paste_x, paste_y))
                resized_img = background
                
            elif block_type == 'featured_image':
                # 16:9比率、800px幅
                final_size = (800, 450)
                resized_img = cropped_img.resize(final_size, Image.Resampling.LANCZOS)
                
            else:
                # デフォルト
                final_size = (600, 400)
                resized_img = cropped_img.resize(final_size, Image.Resampling.LANCZOS)
            resized_img.save(image_path, format='JPEG', quality=85)
        
        # 一時ファイル削除
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        return os.path.relpath(image_path, current_app.static_folder)
        
    except Exception as e:
        logger.error(f"Block image crop processing error: {e}")
        return process_block_image(image_file, block_type, block_id)

def delete_block_image(image_path):
    """ブロック画像ファイルの削除"""
    if not image_path:
        return
    
    try:
        full_path = os.path.join(current_app.static_folder, image_path)
        if os.path.exists(full_path):
            os.remove(full_path)
            logger.info(f"Deleted block image: {full_path}")
    except Exception as e:
        logger.error(f"Error deleting block image {image_path}: {e}")

def render_block_content(block):
    """ブロックの内容をHTMLでレンダリング"""
    from flask import render_template
    
    try:
        if not block or not block.block_type:
            return ''
        
        template_name = block.block_type.template_name
        if not template_name:
            template_name = f'blocks/{block.block_type.type_name}_block.html'
        
        return render_template(template_name, block=block)
        
    except Exception as e:
        logger.error(f"Block rendering error: {e}")
        return f'<div class="block-error">ブロックの表示でエラーが発生しました</div>'