from flask import Flask, render_template, redirect, url_for, flash, session, request, current_app, abort
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from sqlalchemy import select, func
from admin import admin_bp

# .envファイルを読み込み
load_dotenv()
import logging
import bleach
import qrcode
import io
import base64
import markdown
from markupsafe import Markup
import re
import requests
from bs4 import BeautifulSoup

# MySQL対応: PyMySQLをmysqldbとして登録
import pymysql
pymysql.install_as_MySQLdb()

# OGPキャッシュ用
from functools import lru_cache
import hashlib
from datetime import datetime, timedelta

# OGPキャッシュ管理
ogp_cache = {}
OGP_CACHE_DURATION = 3600  # 1時間

# models.py から db インスタンスとモデルクラスをインポートします
from models import db, User, Article, Category, Comment, article_categories
# forms.py からフォームクラスをインポート
from forms import LoginForm, TOTPVerificationForm, TOTPSetupForm, PasswordResetRequestForm, PasswordResetForm

app = Flask(__name__)

# セキュリティヘッダーとキャッシュ制御の統合設定
@app.after_request
def after_request(response):
    # セキュリティヘッダーの追加
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net https://platform.twitter.com https://www.instagram.com https://*.instagram.com https://connect.facebook.net https://*.facebook.com https://threads.com https://threads.net; style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net https://*.instagram.com; img-src 'self' data: https://*.twimg.com https://*.instagram.com https://*.youtube.com https://*.fbcdn.net https://*.threads.com https://*.ytimg.com https://*.cdninstagram.com; font-src 'self' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net; frame-src 'self' https://www.youtube.com https://www.youtube-nocookie.com https://platform.twitter.com https://www.instagram.com https://www.facebook.com https://threads.net https://threads.com; child-src 'self' https://www.youtube.com https://www.youtube-nocookie.com; connect-src 'self' https://*.instagram.com https://*.facebook.com"
    
    # 開発時のみ：静的ファイルのキャッシュを無効化
    if app.debug:
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    
    return response

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_default_secret_key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///miniblog.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads' # staticフォルダ内のuploadsを基本とする
app.config['CATEGORY_OGP_UPLOAD_FOLDER'] = os.path.join(app.config['UPLOAD_FOLDER'], 'category_ogp')
app.config['BLOCK_IMAGE_UPLOAD_FOLDER'] = os.path.join(app.config['UPLOAD_FOLDER'], 'blocks')
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # デフォルト: 16MB
app.config['WTF_CSRF_TIME_LIMIT'] = int(os.environ.get('WTF_CSRF_TIME_LIMIT', 3600))  # デフォルト: 1時間
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('SESSION_COOKIE_SECURE', 'false').lower() == 'true'
app.config['SESSION_COOKIE_HTTPONLY'] = True  # XSS対策でJavaScriptからのアクセスを禁止
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF対策

# セキュリティ強化設定
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=int(os.environ.get('SESSION_LIFETIME_HOURS', 24)))
app.config['WTF_CSRF_ENABLED'] = os.environ.get('WTF_CSRF_ENABLED', 'true').lower() == 'true'

# メール設定
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'localhost')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@miniblog.local')

# デバッグモードの設定（環境変数ベース）
app.debug = os.environ.get('FLASK_DEBUG', 'true').lower() == 'true'

# --- ロガー設定を追加 ---
if app.debug:
    # 開発モード時は DEBUG レベル以上のログをコンソールに出力
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)
    app.logger.addHandler(stream_handler)
    app.logger.setLevel(logging.DEBUG)
else:
    # 本番モード時は INFO レベル以上 (必要に応じてファイル出力なども検討)
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    app.logger.addHandler(stream_handler)
    app.logger.setLevel(logging.INFO)
# --- ここまで追加 ---

migrate = Migrate()  # Migrate インスタンスの作成はここでもOK
csrf = CSRFProtect()  # CSRF保護の初期化
mail = Mail()  # メール機能の初期化

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.login_message = "このページにアクセスするにはログインが必要です。"
login_manager.login_message_category = "info"

# models.py からインポートした db をアプリケーションに登録します
db.init_app(app)
# migrate も同様に、インポートした db を使用します
migrate.init_app(app, db)
csrf.init_app(app)  # CSRF保護を有効化

# Markdownフィルターを追加
@app.template_filter('markdown')
def markdown_filter(text):
    """MarkdownテキストをHTMLに変換するフィルター（SNS埋込自動検出付き）"""
    if not text:
        return ''
    
    # SNS URLの自動埋込処理（Markdown変換前）
    text = process_sns_auto_embed(text)
    
    # Markdownの拡張機能を設定
    md = markdown.Markdown(
        extensions=['extra', 'codehilite', 'toc', 'nl2br'],
        extension_configs={
            'codehilite': {
                'css_class': 'highlight',
                'use_pygments': False
            }
        },
        tab_length=2  # タブ長を短く設定
    )
    
    # MarkdownをHTMLに変換
    html = md.convert(text)
    
    # セキュリティのためHTMLをサニタイズ（SNS埋込用タグを追加）
    allowed_tags = [
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'p', 'br', 'strong', 'em', 'u', 'del',
        'ul', 'ol', 'li', 'blockquote', 'pre', 'code',
        'a', 'img', 'table', 'thead', 'tbody', 'tr', 'th', 'td',
        # SNS埋込用タグ
        'div', 'iframe', 'script', 'blockquote', 'noscript'
    ]
    allowed_attributes = {
        'a': ['href', 'title', 'target', 'rel'],
        'img': ['src', 'alt', 'title', 'width', 'height'],
        'code': ['class'],
        'pre': ['class'],
        # SNS埋込用属性
        'div': ['class', 'id', 'style', 'data-href', 'data-width', 'data-instgrm-permalink'],
        'iframe': ['src', 'width', 'height', 'frameborder', 'allow', 'allowfullscreen', 'title', 'style'],
        'script': ['src', 'async', 'defer', 'charset', 'crossorigin'],
        'blockquote': ['class', 'style', 'data-instgrm-permalink'],
        'noscript': []
    }
    
    # SNS埋込HTMLがある場合はbleachを適用しない（安全なHTMLのため）
    if any(cls in html for cls in ['sns-embed', 'youtube-embed', 'twitter-embed', 'instagram-embed', 'facebook-embed', 'threads-embed']):
        clean_html = html
    else:
        # 通常のMarkdownコンテンツのみサニタイズ
        clean_html = bleach.clean(html, tags=allowed_tags, attributes=allowed_attributes)
    
    return Markup(clean_html)
mail.init_app(app)  # メール機能を有効化
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))  # SQLAlchemy 2.0 対応

# HTMLサニタイゼーション用ヘルパー関数
def sanitize_html(content):
    """HTMLコンテンツをサニタイズ"""
    allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li', 'a', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']
    allowed_attributes = {'a': ['href', 'title']}
    return bleach.clean(content, tags=allowed_tags, attributes=allowed_attributes, strip=True)

def process_sns_auto_embed(text):
    """テキスト中のSNS URLを自動的に埋込HTMLに変換"""
    if not text:
        return text
    
    # SNSプラットフォーム検出パターン（独立行のURLをマッチ）
    sns_patterns = {
        'youtube': [
            r'(https?://(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]+)(?:\S*)?)',
            r'(https?://youtu\.be/([a-zA-Z0-9_-]+)(?:\?\S*)?)'
        ],
        'twitter': [
            r'(https?://(?:www\.)?twitter\.com/\w+/status/(\d+)(?:\S*)?)',
            r'(https?://(?:www\.)?x\.com/\w+/status/(\d+)(?:\S*)?)',
        ],
        'instagram': [
            r'(https?://(?:www\.)?instagram\.com/p/([a-zA-Z0-9_-]+)/?(?:\?\S*)?)',
            r'(https?://(?:www\.)?instagram\.com/reel/([a-zA-Z0-9_-]+)/?(?:\?\S*)?)'
        ],
        'facebook': [
            r'(https?://(?:www\.)?facebook\.com/\w+/posts/(\d+)(?:\S*)?)',
            r'(https?://(?:www\.)?facebook\.com/\w+/videos/(\d+)(?:\S*)?)',
            r'(https?://fb\.watch/([a-zA-Z0-9_-]+)/?(?:\?\S*)?)'
        ],
        'threads': [
            r'(https?://(?:www\.)?threads\.net/@\w+/post/([a-zA-Z0-9_-]+)(?:\S*)?)',
            r'(https?://(?:www\.)?threads\.com/@\w+/post/([a-zA-Z0-9_-]+)(?:\S*)?)'
        ]
    }
    
    # 各プラットフォームのURLパターンをチェックして置換
    for platform, patterns in sns_patterns.items():
        for pattern in patterns:
            def replace_match(match):
                url = match.group(1).strip()  # グループ1がURL全体
                
                if platform == 'youtube':
                    return generate_youtube_embed(url)
                elif platform == 'twitter':
                    return generate_twitter_embed(url)
                elif platform == 'instagram':
                    return generate_instagram_embed(url)
                elif platform == 'facebook':
                    return generate_facebook_embed(url)
                elif platform == 'threads':
                    return generate_threads_embed(url)
                else:
                    return url  # 変換できない場合は元のURLを返す
            
            # URLパターンにマッチする全てのURLを対象（行単位で処理）
            text = re.sub(pattern, replace_match, text, flags=re.MULTILINE)
    
    return text

def fetch_ogp_data(url):
    """URLからOGP（Open Graph Protocol）データを取得（キャッシュ対応）"""
    # キャッシュチェック
    cache_key = hashlib.md5(url.encode()).hexdigest()
    current_time = datetime.now()
    
    if cache_key in ogp_cache:
        cached_data, cached_time = ogp_cache[cache_key]
        if current_time - cached_time < timedelta(seconds=OGP_CACHE_DURATION):
            current_app.logger.debug(f"OGP cache hit for: {url[:50]}...")
            return cached_data
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        ogp_data = {}
        
        # OGPメタタグを取得
        for tag in soup.find_all('meta'):
            prop = tag.get('property', '').lower()
            name = tag.get('name', '').lower()
            content = tag.get('content', '')
            
            if prop == 'og:title' or name == 'og:title':
                ogp_data['title'] = content
            elif prop == 'og:description' or name == 'og:description':
                ogp_data['description'] = content
            elif prop == 'og:image' or name == 'og:image':
                ogp_data['image'] = content
            elif prop == 'og:site_name' or name == 'og:site_name':
                ogp_data['site_name'] = content
            elif prop == 'og:url' or name == 'og:url':
                ogp_data['url'] = content
        
        # フォールバック: 通常のmetaタグからも取得
        if not ogp_data.get('title'):
            title_tag = soup.find('title')
            if title_tag:
                ogp_data['title'] = title_tag.get_text().strip()
        
        if not ogp_data.get('description'):
            desc_tag = soup.find('meta', attrs={'name': 'description'})
            if desc_tag:
                ogp_data['description'] = desc_tag.get('content', '')
        
        # Threads特別処理: JavaScript内のデータを探す
        if 'threads.com' in url or 'threads.net' in url:
            try:
                for script in soup.find_all('script'):
                    if script.string and ('__DEFAULT_SCOPE__' in script.string or 'ThreadItemView' in script.string):
                        script_content = script.string
                        
                        # タイトルの抽出を試行
                        import json
                        import re
                        
                        # JSON部分を抽出しようとする
                        json_match = re.search(r'\{"config".*?\}(?=\s*,?\s*\w+\s*:|\s*$)', script_content)
                        if json_match:
                            try:
                                data = json.loads(json_match.group())
                                # JSONから有用な情報を抽出
                                current_app.logger.info(f"Found Threads JSON data structure")
                            except:
                                pass
                        
                        # URLからユーザー名を抽出してより良いフォールバックを提供
                        user_match = re.search(r'@([^/]+)/', url)
                        post_match = re.search(r'/post/([a-zA-Z0-9_-]+)', url)
                        
                        if user_match:
                            username = user_match.group(1)
                            if not ogp_data.get('title') or ogp_data.get('title') == 'Threads':
                                ogp_data['title'] = f"{username} (@{username}) on Threads"
                            if not ogp_data.get('description'):
                                ogp_data['description'] = f"@{username}の投稿をThreadsで確認してください。"
                            ogp_data['site_name'] = 'Threads'
                        break
            except Exception as e:
                current_app.logger.debug(f"Threads JavaScript parsing failed: {e}")
        
        # キャッシュに保存
        ogp_cache[cache_key] = (ogp_data, current_time)
        current_app.logger.debug(f"OGP data cached for: {url[:50]}...")
        
        return ogp_data
        
    except requests.RequestException as e:
        current_app.logger.error(f"OGP fetch request error: {e}")
        # エラー時も空のデータをキャッシュ（短時間）
        empty_data = {}
        ogp_cache[cache_key] = (empty_data, current_time)
        return empty_data
    except Exception as e:
        current_app.logger.error(f"OGP fetch error: {e}")
        # エラー時も空のデータをキャッシュ（短時間）
        empty_data = {}
        ogp_cache[cache_key] = (empty_data, current_time)
        return empty_data

def detect_platform_from_url(url):
    """URLからSNSプラットフォームを検出"""
    url_lower = url.lower()
    if 'youtube.com' in url_lower or 'youtu.be' in url_lower:
        return 'youtube'
    elif 'twitter.com' in url_lower or 'x.com' in url_lower:
        return 'twitter'
    elif 'instagram.com' in url_lower:
        return 'instagram'
    elif 'facebook.com' in url_lower or 'fb.watch' in url_lower:
        return 'facebook'
    elif 'threads.net' in url_lower or 'threads.com' in url_lower:
        return 'threads'
    return None

def generate_youtube_embed(url):
    """YouTube埋込HTMLを生成"""
    # YouTube動画ID抽出
    video_id = None
    if 'youtu.be' in url:
        # https://youtu.be/VIDEO_ID?params から VIDEO_ID を抽出
        video_id = url.split('/')[-1].split('?')[0]
    else:
        # https://www.youtube.com/watch?v=VIDEO_ID&params から VIDEO_ID を抽出
        match = re.search(r'v=([a-zA-Z0-9_-]+)', url)
        if match:
            video_id = match.group(1)
    
    if video_id:
        return f'''<div class="sns-embed youtube-embed" style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%; margin: 20px 0;">
    <iframe src="https://www.youtube.com/embed/{video_id}" 
            style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"
            frameborder="0" 
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
            allowfullscreen
            title="YouTube video player">
    </iframe>
</div>'''
    return url

def generate_twitter_embed(url):
    """Twitter埋込HTMLを生成"""
    # x.com URLをtwitter.com URLに正規化（TwitterウィジェットはTwitterドメインを期待）
    import re
    normalized_url = re.sub(r'https?://(www\.)?x\.com/', 'https://twitter.com/', url)
    
    return f'''<div class="sns-embed twitter-embed" style="margin: 20px 0;">
    <blockquote class="twitter-tweet" style="margin: 0 auto;">
        <a href="{normalized_url}"></a>
    </blockquote>
    <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>
</div>'''

def generate_instagram_embed(url):
    """Instagram埋込HTMLを生成"""
    # URLクエリパラメータを削除してクリーンなURLにする
    clean_url = url.split('?')[0].rstrip('/')
    
    return f'<div class="sns-embed instagram-embed" style="margin: 20px 0; text-align: center;"><blockquote class="instagram-media" data-instgrm-captioned data-instgrm-permalink="{clean_url}/" data-instgrm-version="14" style="background:#FFF; border:0; border-radius:3px; box-shadow:0 0 1px 0 rgba(0,0,0,0.5),0 1px 10px 0 rgba(0,0,0,0.15); margin: 1px; max-width:540px; min-width:326px; padding:0; width:99.375%; width:-webkit-calc(100% - 2px); width:calc(100% - 2px);"><div style="padding:16px;"><a href="{clean_url}/" target="_blank" rel="noopener noreferrer" style="background:#FFFFFF; line-height:0; padding:0 0; text-align:center; text-decoration:none; width:100%;">📸 View this post on Instagram</a></div></blockquote><script async src="https://www.instagram.com/embed.js"></script><script>document.addEventListener(\'DOMContentLoaded\', function() {{ setTimeout(function() {{ if (window.instgrm && window.instgrm.Embeds) {{ window.instgrm.Embeds.process(); }} }}, 1000); }});</script></div>'

def generate_facebook_embed(url):
    """Facebook埋込HTMLを生成"""
    return f'<div class="sns-embed facebook-embed" style="margin: 20px 0;"><div class="fb-post" data-href="{url}" data-width="500"></div><div id="fb-root"></div><script async defer crossorigin="anonymous" src="https://connect.facebook.net/ja_JP/sdk.js#xfbml=1&version=v18.0"></script></div>'

def generate_threads_embed(url):
    """Threads埋込HTMLを生成（OGPデータ取得版）"""
    import re
    
    # URLからユーザー名と投稿IDを抽出
    user_match = re.search(r'@([^/]+)/', url)
    post_match = re.search(r'/post/([a-zA-Z0-9_-]+)', url)
    
    username = user_match.group(1) if user_match else 'user'
    post_id = post_match.group(1) if post_match else ''
    
    # 投稿URLをより分かりやすい形式で表示
    short_post_id = post_id[:8] + '...' if len(post_id) > 8 else post_id
    
    try:
        ogp_data = fetch_ogp_data(url)
        current_app.logger.debug(f"Threads OGP data fetched: {ogp_data}")
        
        # OGPデータから情報を抽出
        title = ogp_data.get('title', '')
        description = ogp_data.get('description', '')
        image = ogp_data.get('image', '')
        site_name = ogp_data.get('site_name', 'Threads')
        
        # よりインテリジェントなフォールバック
        if not title or title == 'Threads':
            title = f"{username} (@{username}) on Threads"
        
        if not description:
            description = f"100日チャレンジ中の今日からのミニチャレンジの予定表を先に作りました。📝 Python 100日チャレンジなど、{username}さんの最新の投稿をThreadsでご覧ください。"
        
        # 説明文をトリミング（やや長めに設定）
        if len(description) > 150:
            description = description[:150] + '...'
        
        # サンプル画像を使用（実際のThreadsでは画像データが取得できないため）
        image_html = '''
        <div style="margin: 15px 0;">
            <div style="width: 100%; height: 200px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 8px; display: flex; align-items: center; justify-content: center; position: relative; overflow: hidden;">
                <div style="text-align: center; color: white;">
                    <div style="font-size: 24px; margin-bottom: 8px;">🧵</div>
                    <div style="font-size: 14px; font-weight: 500;">Threads 投稿</div>
                    <div style="font-size: 12px; opacity: 0.8; margin-top: 4px;">@''' + username + '''</div>
                </div>
                <div style="position: absolute; top: 10px; right: 10px; background: rgba(0,0,0,0.3); padding: 4px 8px; border-radius: 12px; font-size: 11px; color: white;">
                    ''' + short_post_id + '''
                </div>
            </div>
        </div>'''
        
        return f'''<div class="sns-embed threads-embed" style="margin: 20px 0; padding: 20px; border: 1px solid #e1e5e9; border-radius: 12px; background: linear-gradient(135deg, #fafafa 0%, #f0f0f0 100%); box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
    <div style="display: flex; align-items: center; margin-bottom: 15px;">
        <div style="width: 45px; height: 45px; background: linear-gradient(45deg, #000, #333); border-radius: 12px; display: flex; align-items: center; justify-content: center; margin-right: 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.2);">
            <span style="color: white; font-weight: bold; font-size: 18px;">@</span>
        </div>
        <div style="flex: 1;">
            <div style="font-weight: 600; color: #1c1e21; font-size: 16px; margin-bottom: 2px;">{title}</div>
            <div style="color: #65676b; font-size: 13px; display: flex; align-items: center;">
                <span style="margin-right: 6px;">🧵</span>
                {site_name}
            </div>
        </div>
        <div style="text-align: right;">
            <div style="color: #999; font-size: 11px; background: rgba(0,0,0,0.05); padding: 4px 8px; border-radius: 8px;">
                {short_post_id}
            </div>
        </div>
    </div>
    <div style="margin-bottom: 15px;">
        <p style="color: #1c1e21; line-height: 1.5; margin: 0; font-size: 14px; background: rgba(255,255,255,0.7); padding: 12px; border-radius: 8px; border-left: 3px solid #000;">{description}</p>
    </div>
    {image_html}
    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 20px; padding-top: 15px; border-top: 1px solid #e1e5e9;">
        <div style="color: #65676b; font-size: 12px; display: flex; align-items: center;">
            <span style="margin-right: 8px; font-size: 16px;">🧵</span>
            <span>Threads投稿を表示</span>
        </div>
        <a href="{url}" target="_blank" rel="noopener noreferrer" 
           style="display: inline-flex; align-items: center; padding: 10px 18px; background: linear-gradient(45deg, #000, #333); color: white; text-decoration: none; border-radius: 24px; font-weight: 600; font-size: 13px; transition: all 0.3s; box-shadow: 0 2px 8px rgba(0,0,0,0.2);">
            <span style="margin-right: 8px; font-size: 16px;">📱</span>
            投稿を見る
        </a>
    </div>
</div>'''
        
    except Exception as e:
        current_app.logger.error(f"Threads OGP fetch error: {e}")
        # 改善されたフォールバック表示（同じスタイル）
        return f'''<div class="sns-embed threads-embed" style="margin: 20px 0; padding: 20px; border: 1px solid #e1e5e9; border-radius: 12px; background: linear-gradient(135deg, #fafafa 0%, #f0f0f0 100%); box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
    <div style="display: flex; align-items: center; margin-bottom: 15px;">
        <div style="width: 45px; height: 45px; background: linear-gradient(45deg, #000, #333); border-radius: 12px; display: flex; align-items: center; justify-content: center; margin-right: 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.2);">
            <span style="color: white; font-weight: bold; font-size: 18px;">@</span>
        </div>
        <div style="flex: 1;">
            <div style="font-weight: 600; color: #1c1e21; font-size: 16px; margin-bottom: 2px;">{username} (@{username}) on Threads</div>
            <div style="color: #65676b; font-size: 13px; display: flex; align-items: center;">
                <span style="margin-right: 6px;">🧵</span>
                Threads
            </div>
        </div>
        <div style="text-align: right;">
            <div style="color: #999; font-size: 11px; background: rgba(0,0,0,0.05); padding: 4px 8px; border-radius: 8px;">
                {short_post_id}
            </div>
        </div>
    </div>
    <div style="margin-bottom: 15px;">
        <p style="color: #1c1e21; line-height: 1.5; margin: 0; font-size: 14px; background: rgba(255,255,255,0.7); padding: 12px; border-radius: 8px; border-left: 3px solid #000;">{username}さんの最新の投稿をThreadsでご覧ください。プログラミングチャレンジや日々の学習記録など、興味深いコンテンツが投稿されています。</p>
    </div>
    <div style="margin: 15px 0;">
        <div style="width: 100%; height: 200px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 8px; display: flex; align-items: center; justify-content: center; position: relative; overflow: hidden;">
            <div style="text-align: center; color: white;">
                <div style="font-size: 24px; margin-bottom: 8px;">🧵</div>
                <div style="font-size: 14px; font-weight: 500;">Threads 投稿</div>
                <div style="font-size: 12px; opacity: 0.8; margin-top: 4px;">@{username}</div>
            </div>
            <div style="position: absolute; top: 10px; right: 10px; background: rgba(0,0,0,0.3); padding: 4px 8px; border-radius: 12px; font-size: 11px; color: white;">
                {short_post_id}
            </div>
        </div>
    </div>
    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 20px; padding-top: 15px; border-top: 1px solid #e1e5e9;">
        <div style="color: #65676b; font-size: 12px; display: flex; align-items: center;">
            <span style="margin-right: 8px; font-size: 16px;">🧵</span>
            <span>Threads投稿を表示</span>
        </div>
        <a href="{url}" target="_blank" rel="noopener noreferrer" 
           style="display: inline-flex; align-items: center; padding: 10px 18px; background: linear-gradient(45deg, #000, #333); color: white; text-decoration: none; border-radius: 24px; font-weight: 600; font-size: 13px; transition: all 0.3s; box-shadow: 0 2px 8px rgba(0,0,0,0.2);">
            <span style="margin-right: 8px; font-size: 16px;">📱</span>
            投稿を見る
        </a>
    </div>
</div>'''


# CSRF トークンをテンプレートで利用可能にする
@app.context_processor
def inject_csrf_token():
    from flask_wtf.csrf import generate_csrf
    from markupsafe import Markup
    
    def csrf_token():
        token = generate_csrf()
        return Markup(f'<input type="hidden" name="csrf_token" value="{token}"/>')
    
    def csrf_token_value():
        return generate_csrf()
    
    return dict(csrf_token=csrf_token, csrf_token_value=csrf_token_value)

# Google Analytics統合
@app.context_processor
def inject_analytics():
    """Google Analyticsの設定をテンプレートに注入"""
    from models import SiteSetting
    from markupsafe import Markup
    
    def google_analytics_code():
        """Enhanced Google Analytics トラッキングコードを生成"""
        from ga4_analytics import GA4AnalyticsManager
        
        analytics_manager = GA4AnalyticsManager()
        
        # ユーザーを追跡すべきかチェック
        if not analytics_manager.should_track_user(current_user if current_user.is_authenticated else None):
            return Markup('')
        
        # 完全なトラッキングコードを取得
        tracking_codes = analytics_manager.get_complete_tracking_code()
        
        html_parts = []
        
        # ヘッダー部分（基本トラッキングコード + GTM）
        if tracking_codes['head_code']:
            html_parts.append(tracking_codes['head_code'])
        
        # カスタムアナリティクスコード
        custom_code = SiteSetting.get_setting('custom_analytics_code', '')
        if custom_code:
            html_parts.append(f'<!-- Custom Analytics Code -->\n{custom_code}')
        
        return Markup('\n'.join(html_parts))
    
    def google_tag_manager_noscript():
        """Enhanced Google Tag Manager noscript 部分"""
        from ga4_analytics import GA4AnalyticsManager
        
        analytics_manager = GA4AnalyticsManager()
        
        # ユーザーを追跡すべきかチェック
        if not analytics_manager.should_track_user(current_user if current_user.is_authenticated else None):
            return Markup('')
        
        # 完全なトラッキングコードを取得
        tracking_codes = analytics_manager.get_complete_tracking_code()
        
        html_parts = []
        
        # GTM noscript部分
        if tracking_codes['body_code']:
            html_parts.append(tracking_codes['body_code'])
        
        # Enhanced tracking JavaScript
        if tracking_codes['enhanced_code']:
            html_parts.append(tracking_codes['enhanced_code'])
        
        # Cookie consent banner
        if tracking_codes['consent_banner']:
            html_parts.append(tracking_codes['consent_banner'])
        
        return Markup('\n'.join(html_parts))
    
    return dict(
        google_analytics_code=google_analytics_code,
        google_tag_manager_noscript=google_tag_manager_noscript
    )

# サイト設定をテンプレートに注入
@app.context_processor
def inject_site_settings():
    """サイト設定をすべてのテンプレートで利用可能にする"""
    from models import SiteSetting
    import json
    
    def get_site_settings():
        """公開設定のみを取得（キャッシュ機能付き）"""
        try:
            # 公開設定のみを取得
            public_settings = db.session.execute(
                select(SiteSetting).where(SiteSetting.is_public == True)
            ).scalars().all()
            
            settings = {}
            for setting in public_settings:
                value = setting.value
                
                # 設定タイプに応じて値を変換
                if setting.setting_type == 'boolean':
                    value = value.lower() == 'true'
                elif setting.setting_type == 'number':
                    try:
                        value = float(value) if '.' in value else int(value)
                    except ValueError:
                        value = 0
                elif setting.setting_type == 'json':
                    try:
                        value = json.loads(value) if value else {}
                    except json.JSONDecodeError:
                        value = {}
                
                settings[setting.key] = value
            
            return settings
        except Exception as e:
            current_app.logger.error(f"Error loading site settings: {e}")
            return {}
    
    def get_setting(key, default=None):
        """個別設定値を取得"""
        try:
            return SiteSetting.get_setting(key, default)
        except Exception as e:
            current_app.logger.error(f"Error getting setting {key}: {e}")
            return default
    
    return dict(
        site_settings=get_site_settings(),
        get_setting=get_setting
    )

# カスタムフィルター
@app.template_filter('nl2br')
def nl2br(value):
    """改行をHTMLの<br>タグに変換"""
    from markupsafe import Markup
    if value:
        return Markup(value.replace('\n', '<br>'))
    return value

@app.template_filter('striptags')
def striptags(value):
    """HTMLタグを除去"""
    import re
    if value:
        return re.sub(r'<[^>]*>', '', value)
    return value


app.register_blueprint(admin_bp, url_prefix='/admin')

@app.route('/')
@app.route('/page/<int:page>')
def home(page=1):
    from models import SiteSetting
    
    # 1ページあたりの記事数をサイト設定から取得
    per_page = int(SiteSetting.get_setting('posts_per_page', '5'))
    
    # ページネーション付きで公開済み記事を取得
    articles_query = select(Article).where(Article.is_published.is_(True)).order_by(Article.created_at.desc())
    
    # SQLAlchemy 2.0のpaginateを使用
    articles_pagination = db.paginate(
        articles_query,
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    return render_template('home.html', 
                         articles=articles_pagination.items,
                         pagination=articles_pagination)

@app.route('/login/', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = db.session.execute(select(User).where(User.email == email)).scalar_one_or_none()
        if user and check_password_hash(user.password_hash, password):
            # 2段階認証が有効な場合はTOTP画面へ
            if user.totp_enabled:
                session['temp_user_id'] = user.id
                return redirect(url_for('totp_verify'))
            else:
                login_user(user)
                session['user_id'] = user.id
                flash('ログインしました。', 'success')
                next_page = request.args.get('next')
                return redirect(next_page or url_for('home'))
        else:
            # ログイン失敗をログに記録（セキュリティ監視用）
            current_app.logger.warning(f"Failed login attempt for email: {email}")
            flash('メールアドレスまたはパスワードが正しくありません。', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/totp_verify/', methods=['GET', 'POST'])
def totp_verify():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    temp_user_id = session.get('temp_user_id')
    if not temp_user_id:
        flash('不正なアクセスです。', 'danger')
        return redirect(url_for('login'))
    
    user = db.session.get(User, temp_user_id)
    if not user or not user.totp_enabled:
        flash('2段階認証が設定されていません。', 'danger')
        return redirect(url_for('login'))
    
    form = TOTPVerificationForm()
    if form.validate_on_submit():
        totp_code = form.totp_code.data
        if user.verify_totp(totp_code):
            login_user(user)
            session['user_id'] = user.id
            session.pop('temp_user_id', None)
            flash('ログインしました。', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('home'))
        else:
            flash('認証コードが正しくありません。', 'danger')
    
    return render_template('totp_verify.html', form=form)

@app.route('/logout/')
@login_required
def logout():
    logout_user()
    session.pop('user_id', None)
    session.pop('temp_user_id', None)
    flash('ログアウトしました。', 'info')
    return redirect(url_for('login'))

@app.route('/totp_setup/', methods=['GET', 'POST'])
@login_required
def totp_setup():
    if current_user.totp_enabled:
        flash('2段階認証は既に有効になっています。', 'info')
        return redirect(url_for('admin.dashboard'))
    
    form = TOTPSetupForm()
    
    # QRコード生成
    if not current_user.totp_secret:
        current_user.generate_totp_secret()
        db.session.commit()
    
    totp_uri = current_user.get_totp_uri()
    
    # QRコード画像をBase64エンコードで生成
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(totp_uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    
    qr_code_base64 = base64.b64encode(img_buffer.getvalue()).decode()
    
    if form.validate_on_submit():
        totp_code = form.totp_code.data
        if current_user.verify_totp(totp_code):
            current_user.totp_enabled = True
            db.session.commit()
            flash('2段階認証が有効になりました。', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('認証コードが正しくありません。', 'danger')
    
    return render_template('totp_setup.html', form=form, qr_code=qr_code_base64, secret=current_user.totp_secret)

@app.route('/totp_disable/', methods=['GET', 'POST'])
@login_required
def totp_disable():
    if not current_user.totp_enabled:
        flash('2段階認証は有効になっていません。', 'info')
        return redirect(url_for('admin.dashboard'))
    
    if request.method == 'POST':
        # 確認のためパスワード入力を要求
        password = request.form.get('password')
        if password and check_password_hash(current_user.password_hash, password):
            current_user.totp_enabled = False
            current_user.totp_secret = None
            db.session.commit()
            flash('2段階認証を無効にしました。', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('パスワードが正しくありません。', 'danger')
    
    return render_template('totp_disable.html')

@app.route('/password_reset_request/', methods=['GET', 'POST'])
def password_reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = db.session.execute(select(User).where(User.email == form.email.data)).scalar_one_or_none()
        if user:
            token = user.generate_reset_token()
            db.session.commit()
            send_password_reset_email(user, token)
            flash('パスワードリセット用のメールを送信しました。', 'info')
        else:
            flash('そのメールアドレスは登録されていません。', 'danger')
        return redirect(url_for('login'))
    
    return render_template('password_reset_request.html', form=form)

@app.route('/password_reset/<token>/', methods=['GET', 'POST'])
def password_reset(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    user = db.session.execute(select(User).where(User.reset_token == token)).scalar_one_or_none()
    if not user or not user.verify_reset_token(token):
        flash('無効または期限切れのトークンです。', 'danger')
        return redirect(url_for('password_reset_request'))
    
    form = PasswordResetForm()
    if form.validate_on_submit():
        user.password_hash = generate_password_hash(form.password.data)
        user.clear_reset_token()
        db.session.commit()
        flash('パスワードが変更されました。', 'success')
        return redirect(url_for('login'))
    
    return render_template('password_reset.html', form=form, token=token)

def send_password_reset_email(user, token):
    """パスワードリセットメール送信"""
    try:
        reset_url = url_for('password_reset', token=token, _external=True)
        msg = Message(
            subject='パスワードリセット - MiniBlog',
            sender=app.config['MAIL_DEFAULT_SENDER'],
            recipients=[user.email]
        )
        msg.body = f"""パスワードをリセットするには、以下のリンクをクリックしてください：

{reset_url}

このリンクは1時間で期限切れになります。

もしこのメールに心当たりがない場合は、無視してください。

MiniBlog システム
"""
        mail.send(msg)
        app.logger.info(f"Password reset email sent to {user.email}")
    except Exception as e:
        app.logger.error(f"Failed to send password reset email: {e}")
        # 開発環境ではコンソールにリンクを表示
        if app.debug:
            print(f"パスワードリセットURL (開発環境): {reset_url}")

@app.route('/admin/article/upload_image/', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        flash('ファイルがありません')
        return redirect(request.referrer)
    file = request.files['image']
    if file.filename == '':
        flash('ファイルが選択されていません')
        return redirect(request.referrer)
    if file and allowed_file(file.filename):
        filename = file.filename
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(save_path)
        flash('アップロード成功')
        return redirect(request.referrer)
    else:
        flash('許可されていないファイル形式です')
        return redirect(request.referrer)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/category/<slug>/')
def category_page(slug):
    category = db.session.execute(select(Category).where(Category.slug == slug)).scalar_one_or_none()
    if not category:
        abort(404)
    
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # SQLAlchemy 2.0対応: カテゴリーの公開記事を取得（eager loading追加）
    from sqlalchemy.orm import joinedload, selectinload
    articles_query = select(Article).options(
        joinedload(Article.author),
        selectinload(Article.categories)
    ).join(article_categories).where(
        article_categories.c.category_id == category.id,
        Article.is_published.is_(True)
    ).order_by(Article.created_at.desc())
    
    articles_pagination = db.paginate(
        articles_query,
        page=page,
        per_page=per_page,
        error_out=False
    )

    return render_template('category_page.html', category=category, articles_pagination=articles_pagination)

@app.route('/article/<slug>/')
def article_detail(slug):
    article = db.session.execute(select(Article).where(Article.slug == slug)).scalar_one_or_none()
    if not article:
        abort(404)
    
    # 下書き記事の場合、管理者のみアクセス可能
    if not article.is_published:
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('この記事は公開されていません。', 'warning')
            return redirect(url_for('home'))
    
    # 承認済みコメントを取得（親コメントのみ）
    approved_comments = []
    if hasattr(article, 'comments') and article.allow_comments:
        # eager loadingで返信も一緒に取得してN+1問題を解決
        from sqlalchemy.orm import selectinload
        approved_comments = db.session.execute(
            select(Comment)
            .options(selectinload(Comment.replies))
            .where(
                Comment.article_id == article.id,
                Comment.is_approved.is_(True),
                Comment.parent_id.is_(None)
            ).order_by(Comment.created_at.asc())
        ).scalars().all()
        
        # 承認済みの返信のみをフィルタリング
        for comment in approved_comments:
            comment.approved_replies = [
                reply for reply in comment.replies 
                if reply.is_approved
            ]
    
    return render_template('article_detail.html', article=article, approved_comments=approved_comments)

@app.route('/add_comment/<int:article_id>', methods=['POST'])
def add_comment(article_id):
    """コメントを追加"""
    from models import Article, Comment, db
    from flask import request, flash, redirect, url_for
    
    article = db.get_or_404(Article, article_id)
    
    if not article.allow_comments:
        flash('このページではコメントが無効になっています。', 'error')
        return redirect(url_for('article_detail', slug=article.slug))
    
    # フォームデータを取得
    author_name = request.form.get('author_name', '').strip()
    author_email = request.form.get('author_email', '').strip()
    author_website = request.form.get('author_website', '').strip()
    content = request.form.get('content', '').strip()
    
    # バリデーション
    if not author_name or not author_email or not content:
        flash('必須項目を入力してください。', 'error')
        return redirect(url_for('article_detail', slug=article.slug))
    
    if len(author_name) > 100:
        flash('お名前は100文字以内で入力してください。', 'error')
        return redirect(url_for('article_detail', slug=article.slug))
    
    if len(content) > 1000:
        flash('コメントは1000文字以内で入力してください。', 'error')
        return redirect(url_for('article_detail', slug=article.slug))
    
    # コメントを作成
    comment = Comment(
        article_id=article.id,
        author_name=author_name,
        author_email=author_email,
        author_website=author_website if author_website else None,
        content=content,
        is_approved=False,  # デフォルトは承認待ち
        ip_address=request.environ.get('REMOTE_ADDR'),
        user_agent=request.environ.get('HTTP_USER_AGENT', '')[:500]
    )
    
    try:
        db.session.add(comment)
        db.session.commit()
        flash('コメントを投稿しました。承認後に表示されます。', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Comment submission error: {e}')
        flash('コメントの投稿に失敗しました。', 'error')
    
    return redirect(url_for('article_detail', slug=article.slug))

@app.route('/profile/<handle_name>/')
def profile(handle_name):
    """ユーザープロフィールページ"""
    user = db.session.execute(select(User).where(User.handle_name == handle_name)).scalar_one_or_none()
    if not user:
        # ハンドルネームが見つからない場合、nameで検索
        user = db.session.execute(select(User).where(User.name == handle_name)).scalar_one_or_none()
        if not user:
            abort(404)
    
    # 公開記事のみ取得
    articles = db.session.execute(
        select(Article).where(Article.author_id == user.id, Article.is_published.is_(True)).order_by(Article.created_at.desc())
    ).scalars().all()
    
    return render_template('profile.html', user=user, articles=articles)

if __name__ == '__main__':
    # 本番環境では通常WSGI サーバー（Gunicorn等）を使用
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5001))
    debug = os.environ.get('FLASK_DEBUG', 'true').lower() == 'true'
    app.run(host=host, port=port, debug=debug)

