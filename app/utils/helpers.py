"""
共通ヘルパー関数
アプリケーション全体で使用される汎用的な関数群
"""
import os
import re
import time
from functools import wraps
from flask import current_app, flash, redirect, url_for
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename
from PIL import Image


def admin_required(f):
    """管理者認証デコレータ"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('ログインが必要です', 'info')
            return redirect(url_for('login'))
        if current_user.role != 'admin':
            flash('管理者権限が必要です', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return login_required(decorated_function)


def allowed_file(filename):
    """ファイル拡張子チェック"""
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in current_app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'gif'})


def get_safe_count(query_or_model):
    """安全にカウントを取得（デバッグ情報付き）"""
    try:
        if hasattr(query_or_model, 'count'):
            # クエリオブジェクトの場合
            count = query_or_model.count()
            current_app.logger.info(f"Query count: {count}")
            return count
        else:
            # モデルクラスの場合
            count = query_or_model.query.count()
            current_app.logger.info(f"Model {query_or_model.__name__} count: {count}")
            return count
    except Exception as e:
        current_app.logger.error(f"Count query failed for {query_or_model}: {e}")
        return 0


def generate_slug_from_name(name):
    """名前からスラッグを自動生成"""
    if not name:
        return None
    slug = re.sub(r'[^\w\s-]', '', name.lower())
    slug = re.sub(r'[\s_-]+', '-', slug)
    return slug.strip('-')


def process_featured_image(image_file, article_id=None):
    """記事のアイキャッチ画像を処理（アップロード、リサイズ）"""
    if not image_file:
        return None
    
    try:
        timestamp = int(time.time())
        file_ext = os.path.splitext(secure_filename(image_file.filename))[1]
        filename = f"featured_{article_id or 'new'}_{timestamp}{file_ext}"
        
        upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'articles')
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        
        image_path = os.path.join(upload_folder, filename)
        temp_path = os.path.join(upload_folder, f"temp_{filename}")
        
        # 一時保存
        image_file.save(temp_path)
        
        # 画像処理
        with Image.open(temp_path) as img:
            # リサイズ（アイキャッチ画像の標準サイズ）
            resized_img = img.resize((1200, 675), Image.Resampling.LANCZOS)
            resized_img.save(image_path, format='JPEG', quality=85)
        
        # 一時ファイル削除
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        # 相対パスを返す
        return os.path.relpath(image_path, current_app.static_folder)
    
    except Exception as e:
        current_app.logger.error(f"Featured image processing error: {e}")
        return None


def process_ogp_image(image_file, category_id=None):
    """OGP画像の処理（アップロード、クロップ、リサイズ）"""
    if not image_file:
        return None
    
    try:
        timestamp = int(time.time())
        file_ext = os.path.splitext(secure_filename(image_file.filename))[1]
        filename = f"category_ogp_{category_id or 'new'}_{timestamp}{file_ext}"
        
        upload_folder = current_app.config.get('CATEGORY_OGP_UPLOAD_FOLDER', 'static/uploads/categories')
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        
        image_path = os.path.join(upload_folder, filename)
        temp_path = os.path.join(upload_folder, f"temp_{filename}")
        
        # 一時保存
        image_file.save(temp_path)
        
        # 画像処理
        with Image.open(temp_path) as img:
            # リサイズ（OGP画像の標準サイズ）
            resized_img = img.resize((1200, 630), Image.Resampling.LANCZOS)
            resized_img.save(image_path, format='JPEG', quality=85)
        
        # 一時ファイル削除
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        # 相対パスを返す
        return os.path.relpath(image_path, current_app.static_folder)
    
    except Exception as e:
        current_app.logger.error(f"OGP image processing error: {e}")
        return None


def delete_old_image(image_path):
    """古い画像ファイルを削除"""
    if image_path and os.path.exists(image_path):
        try:
            os.remove(image_path)
            current_app.logger.info(f"Deleted old image: {image_path}")
        except OSError as e:
            current_app.logger.error(f"Error deleting image {image_path}: {e}")


def sanitize_html(content):
    """HTMLコンテンツをサニタイズ"""
    import bleach
    allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li', 'a', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']
    allowed_attributes = {'a': ['href', 'title']}
    return bleach.clean(content, tags=allowed_tags, attributes=allowed_attributes, strip=True)