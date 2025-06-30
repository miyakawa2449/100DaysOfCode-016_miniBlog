from flask import Blueprint, render_template, redirect, url_for, request, flash, session, current_app, jsonify
from flask_login import login_required, current_user
from models import db, User, Article, Category, Comment, SiteSetting, UploadedImage
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from sqlalchemy import func
import os
from PIL import Image
import time
import re
import json
from forms import CategoryForm, ArticleForm, WordPressImportForm, GoogleAnalyticsForm
try:
    from block_forms import BlockEditorForm, create_block_form
    from block_utils import process_block_image, process_block_image_with_crop, fetch_ogp_data, detect_sns_platform, extract_sns_id, generate_sns_embed_html
    from models import BlockType, ArticleBlock
    BLOCK_EDITOR_AVAILABLE = True
except ImportError as e:
    print(f"Block editor modules not available: {e}")
    BLOCK_EDITOR_AVAILABLE = False

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# ユーティリティ関数
def admin_required(f):
    """管理者認証デコレータ"""
    from functools import wraps
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
        current_app.logger.error(f"OGP画像処理エラー: {e}")
        return None

def delete_old_image(image_path):
    """古い画像ファイルを削除"""
    if image_path:
        try:
            full_path = os.path.join(current_app.static_folder, image_path)
            if os.path.exists(full_path):
                os.remove(full_path)
                return True
        except Exception as e:
            current_app.logger.error(f"画像削除エラー: {e}")
    return False

def process_featured_image(image_file, article_id=None):
    """アイキャッチ画像の処理（アップロード、リサイズ）"""
    if not image_file or not image_file.filename:
        current_app.logger.info("No image file provided")
        return None
    
    try:
        current_app.logger.info(f"Processing image: {image_file.filename}")
        
        timestamp = int(time.time())
        file_ext = os.path.splitext(secure_filename(image_file.filename))[1]
        if not file_ext:
            file_ext = '.jpg'
        
        filename = f"featured_{article_id or 'new'}_{timestamp}{file_ext}"
        
        upload_folder = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'static/uploads'), 'articles')
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder, exist_ok=True)
            current_app.logger.info(f"Created upload directory: {upload_folder}")
        
        image_path = os.path.join(upload_folder, filename)
        temp_path = os.path.join(upload_folder, f"temp_{filename}")
        
        current_app.logger.info(f"Saving image to: {image_path}")
        
        # 一時保存
        image_file.save(temp_path)
        current_app.logger.info(f"Saved temp file: {temp_path}")
        
        # 画像処理
        with Image.open(temp_path) as img:
            # RGB変換（JPEG保存のため）
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # アイキャッチ画像のリサイズ（16:9比率、最大1200x675）
            resized_img = img.resize((1200, 675), Image.Resampling.LANCZOS)
            resized_img.save(image_path, format='JPEG', quality=85)
            current_app.logger.info(f"Processed and saved image: {image_path}")
        
        # 一時ファイル削除
        if os.path.exists(temp_path):
            os.remove(temp_path)
            current_app.logger.info(f"Removed temp file: {temp_path}")
        
        # 相対パスを返す
        relative_path = os.path.relpath(image_path, current_app.static_folder)
        current_app.logger.info(f"Returning relative path: {relative_path}")
        return relative_path
    
    except Exception as e:
        current_app.logger.error(f"アイキャッチ画像処理エラー: {e}")
        import traceback
        current_app.logger.error(f"Traceback: {traceback.format_exc()}")
        # 一時ファイルをクリーンアップ
        if 'temp_path' in locals() and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass
        return None

def process_cropped_image(cropped_data, article_id=None):
    """トリミング後の画像データの処理"""
    import base64
    import io
    
    try:
        current_app.logger.info(f"Processing cropped image data for article ID: {article_id}")
        
        # Data URLからbase64データを抽出
        if cropped_data.startswith('data:image'):
            header, base64_data = cropped_data.split(',', 1)
        else:
            base64_data = cropped_data
        
        # base64デコード
        image_data = base64.b64decode(base64_data)
        
        # PILで画像を開く
        img = Image.open(io.BytesIO(image_data))
        
        # RGB変換（JPEG保存のため）
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        
        # ファイル名生成
        timestamp = int(time.time())
        filename = f"featured_cropped_{article_id or 'new'}_{timestamp}.jpg"
        
        # 保存先ディレクトリ
        upload_folder = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'static/uploads'), 'articles')
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder, exist_ok=True)
            current_app.logger.info(f"Created upload directory: {upload_folder}")
        
        image_path = os.path.join(upload_folder, filename)
        
        # 画像保存
        img.save(image_path, format='JPEG', quality=85)
        current_app.logger.info(f"Cropped image saved: {image_path}")
        
        # 相対パスを返す
        relative_path = os.path.relpath(image_path, current_app.static_folder)
        current_app.logger.info(f"Returning relative path: {relative_path}")
        return relative_path
        
    except Exception as e:
        current_app.logger.error(f"Cropped image processing error: {e}")
        import traceback
        current_app.logger.error(f"Traceback: {traceback.format_exc()}")
        return None

def process_uploaded_image(image_file, alt_text="", caption="", description=""):
    """記事本文用の画像アップロード処理"""
    import mimetypes
    
    if not image_file or not image_file.filename:
        return None, "画像ファイルが選択されていません。"
    
    try:
        # ファイル名の安全化
        original_filename = secure_filename(image_file.filename)
        if not original_filename:
            return None, "無効なファイル名です。"
        
        # 拡張子チェック
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
        file_ext = os.path.splitext(original_filename)[1].lower()
        if file_ext not in allowed_extensions:
            return None, f"サポートされていないファイル形式です。対応形式: {', '.join(allowed_extensions)}"
        
        # MIMEタイプ検証
        mime_type, _ = mimetypes.guess_type(original_filename)
        if not mime_type or not mime_type.startswith('image/'):
            return None, "画像ファイルではありません。"
        
        # ファイルサイズチェック（10MB制限 - トリミング画像対応）
        image_file.seek(0, 2)  # ファイル末尾に移動
        file_size = image_file.tell()
        image_file.seek(0)  # ファイル先頭に戻る
        
        max_size = 10 * 1024 * 1024  # 10MB
        if file_size > max_size:
            return None, f"ファイルサイズが大きすぎます（最大{max_size // (1024*1024)}MB）。"
        
        # ユニークなファイル名生成
        timestamp = int(time.time())
        filename = f"content_{current_user.id}_{timestamp}{file_ext}"
        
        # 保存先ディレクトリ
        upload_folder = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'static/uploads'), 'content')
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder, exist_ok=True)
        
        # 一時保存
        temp_path = os.path.join(upload_folder, f"temp_{filename}")
        image_file.save(temp_path)
        
        # 画像処理とメタデータ取得
        final_path = os.path.join(upload_folder, filename)
        width, height = None, None
        
        with Image.open(temp_path) as img:
            width, height = img.size
            
            # RGB変換（JPEG保存のため）
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # 大きすぎる画像はリサイズ（最大2000px）
            max_dimension = 2000
            if max(width, height) > max_dimension:
                ratio = max_dimension / max(width, height)
                new_width = int(width * ratio)
                new_height = int(height * ratio)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                width, height = new_width, new_height
            
            # 最終保存
            img.save(final_path, format='JPEG' if file_ext in ['.jpg', '.jpeg'] else 'PNG', 
                    quality=85 if file_ext in ['.jpg', '.jpeg'] else None)
        
        # 一時ファイル削除
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        # データベースに保存
        relative_path = os.path.relpath(final_path, current_app.static_folder)
        
        uploaded_image = UploadedImage(
            filename=filename,
            original_filename=original_filename,
            file_path=relative_path,
            file_size=os.path.getsize(final_path),
            mime_type=mime_type,
            width=width,
            height=height,
            alt_text=alt_text,
            caption=caption,
            description=description,
            uploader_id=current_user.id
        )
        
        db.session.add(uploaded_image)
        db.session.commit()
        
        current_app.logger.info(f"Image uploaded successfully: {filename}")
        return uploaded_image, None
        
    except Exception as e:
        current_app.logger.error(f"Image upload error: {e}")
        import traceback
        current_app.logger.error(f"Traceback: {traceback.format_exc()}")
        
        # クリーンアップ
        for cleanup_path in [locals().get('temp_path'), locals().get('final_path')]:
            if cleanup_path and os.path.exists(cleanup_path):
                try:
                    os.remove(cleanup_path)
                except:
                    pass
        
        return None, "画像のアップロードに失敗しました。"

# デバッグ用のテスト関数（簡易版）
@admin_bp.route('/debug/simple')
def debug_simple():
    """認証なしでデータベース接続をテスト"""
    from flask import current_app
    try:
        with current_app.app_context():
            user_count = db.session.query(User).count()
            article_count = db.session.query(Article).count()
            category_count = db.session.query(Category).count()
            
            return f"""
            <h2>簡単なデータベーステスト</h2>
            <p>ユーザー数: {user_count}</p>
            <p>記事数: {article_count}</p>  
            <p>カテゴリ数: {category_count}</p>
            """
    except Exception as e:
        import traceback
        return f"<h2>エラー</h2><pre>{str(e)}\n\n{traceback.format_exc()}</pre>"

# デバッグ用のテンプレートテスト
@admin_bp.route('/debug/template')
@admin_required
def debug_template():
    """テンプレート描画テスト"""
    try:
        stats = {
            'user_count': 1,
            'article_count': 6,
            'category_count': 2,
            'comment_count': 0
        }
        
        monthly_stats = {
            'articles_this_month': 6,
            'users_this_month': 1,
            'comments_this_month': 0
        }
        
        recent_data = {
            'recent_articles': [],
            'pending_comments': 0
        }
        
        return render_template('admin/dashboard.html', 
                             stats=stats,
                             monthly_stats=monthly_stats,
                             recent_data=recent_data,
                             chart_data=[])
    except Exception as e:
        import traceback
        return f"<h2>テンプレートエラー</h2><pre>{str(e)}\n\n{traceback.format_exc()}</pre>"

@admin_bp.route('/debug/stats')
@admin_required
def debug_stats():
    """統計データのデバッグ"""
    debug_info = {}
    
    try:
        # 直接クエリでテスト
        debug_info['user_count_direct'] = db.session.query(User).count()
        debug_info['article_count_direct'] = db.session.query(Article).count()
        debug_info['category_count_direct'] = db.session.query(Category).count()
        
        # モデル経由でテスト
        debug_info['user_count_model'] = User.query.count()
        debug_info['article_count_model'] = Article.query.count()
        debug_info['category_count_model'] = Category.query.count()
        
        # 実際のデータ一覧
        debug_info['users'] = [{'id': u.id, 'name': u.name, 'email': u.email} for u in User.query.all()]
        debug_info['articles'] = [{'id': a.id, 'title': a.title, 'author_id': a.author_id} for a in Article.query.all()]
        debug_info['categories'] = [{'id': c.id, 'name': c.name, 'slug': c.slug} for c in Category.query.all()]
        
        # 記事の状態チェック（エラー回避のため簡略化）
        articles = Article.query.all()
        debug_info['article_details'] = []
        for article in articles:
            article_info = {
                'id': article.id,
                'title': article.title,
                'created_at': str(article.created_at) if article.created_at else None
            }
            
            # hasattr の使用を避けて try/except で代替
            try:
                article_info['is_published'] = article.is_published
                article_info['has_is_published'] = True
            except AttributeError:
                article_info['has_is_published'] = False
                
            try:
                article_info['published_at'] = str(article.published_at) if article.published_at else None
                article_info['has_published_at'] = True
            except AttributeError:
                article_info['has_published_at'] = False
            
            debug_info['article_details'].append(article_info)
        
        import json
        return f"<pre>{json.dumps(debug_info, indent=2, ensure_ascii=False)}</pre>"
        
    except Exception as e:
        import traceback
        return f"<pre>Debug error: {str(e)}\n\nTraceback:\n{traceback.format_exc()}</pre>"

# ダッシュボード
@admin_bp.route('/')
@admin_required
def dashboard():
    """管理者ダッシュボード（シンプル版）"""
    # 基本的な統計のみ
    stats = {
        'user_count': User.query.count(),
        'article_count': Article.query.count(),
        'category_count': Category.query.count(),
        'comment_count': 0
    }
    
    # 今月の統計を計算
    import calendar
    
    current_date = datetime.now()
    current_year = current_date.year
    current_month = current_date.month
    
    # 今月の開始日と終了日を計算
    first_day = datetime(current_year, current_month, 1)
    last_day = datetime(current_year, current_month, calendar.monthrange(current_year, current_month)[1], 23, 59, 59)
    
    # 今月作成された記事数
    articles_this_month = Article.query.filter(
        Article.created_at >= first_day,
        Article.created_at <= last_day
    ).count()
    
    # 今月作成されたユーザー数（created_atフィールドがある場合）
    users_this_month = 0
    if hasattr(User, 'created_at'):
        users_this_month = User.query.filter(
            User.created_at >= first_day,
            User.created_at <= last_day
        ).count()
    
    current_app.logger.info(f"Monthly stats calculation: articles_this_month={articles_this_month}, period={first_day} to {last_day}")
    
    monthly_stats = {
        'articles_this_month': articles_this_month,
        'users_this_month': users_this_month,
        'comments_this_month': 0  # コメント機能が実装されたら修正
    }
    
    # 最近の記事
    recent_articles = Article.query.order_by(Article.created_at.desc()).limit(5).all()
    recent_data = {
        'recent_articles': recent_articles,
        'pending_comments': 0
    }
    
    return render_template('admin/dashboard.html', 
                         stats=stats,
                         monthly_stats=monthly_stats,
                         recent_data=recent_data,
                         chart_data=[])

# ユーザー管理
@admin_bp.route('/users/')
@admin_required
def users():
    """ユーザー一覧"""
    try:
        users = User.query.all()
        return render_template('admin/users.html', users=users)
    except Exception as e:
        current_app.logger.error(f"Users page error: {e}")
        flash('ユーザーデータの取得中にエラーが発生しました。', 'danger')
        return render_template('admin/users.html', users=[])

@admin_bp.route('/user/create/', methods=['GET', 'POST'])
@admin_required
def create_user():
    """ユーザー作成"""
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        password = request.form.get('password')
        role = request.form.get('role', 'author')
        
        # バリデーション
        if not all([email, name, password]):
            flash('必須項目を入力してください。', 'danger')
            return render_template('admin/create_user.html')
        
        if len(password) < 8:
            flash('パスワードは8文字以上である必要があります。', 'danger')
            return render_template('admin/create_user.html')
        
        if User.query.filter_by(email=email).first():
            flash('このメールアドレスは既に使用されています。', 'danger')
            return render_template('admin/create_user.html')
        
        try:
            new_user = User(
                email=email,
                name=name,
                password_hash=generate_password_hash(password),
                role=role,
                handle_name=request.form.get('handle_name', ''),
                introduction=request.form.get('introduction', ''),
                created_at=datetime.utcnow()
            )
            db.session.add(new_user)
            db.session.commit()
            flash(f'ユーザー「{name}」を作成しました。', 'success')
            return redirect(url_for('admin.users'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"User creation error: {e}")
            flash('ユーザーの作成に失敗しました。', 'danger')
    
    return render_template('admin/create_user.html')

@admin_bp.route('/user/edit/<int:user_id>/', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    """ユーザー編集"""
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        # 自分自身の管理者権限削除チェック
        if user.id == current_user.id and request.form.get('role') != 'admin':
            flash('自分自身の管理者権限は削除できません。', 'danger')
            return render_template('admin/edit_user.html', user=user)
        
        try:
            # パスワード確認チェック
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            if new_password and new_password != confirm_password:
                flash('パスワードが一致しません。', 'danger')
                return render_template('admin/edit_user.html', user=user)
            
            # 基本データ更新
            user.name = request.form.get('name', user.name)
            user.handle_name = request.form.get('handle_name', user.handle_name or '')
            if user.id != current_user.id:  # 自分以外の場合のみ権限変更可能
                user.role = request.form.get('role', user.role)
            
            # プロフィール情報更新
            user.introduction = request.form.get('introduction', user.introduction or '')
            user.birthplace = request.form.get('birthplace', user.birthplace or '')
            
            # 誕生日の処理
            birthday_str = request.form.get('birthday')
            if birthday_str:
                from datetime import datetime
                user.birthday = datetime.strptime(birthday_str, '%Y-%m-%d').date()
            else:
                user.birthday = None
            
            # SNSアカウント更新
            user.sns_x = request.form.get('sns_x', user.sns_x or '')
            user.sns_facebook = request.form.get('sns_facebook', user.sns_facebook or '')
            user.sns_instagram = request.form.get('sns_instagram', user.sns_instagram or '')
            user.sns_threads = request.form.get('sns_threads', user.sns_threads or '')
            user.sns_youtube = request.form.get('sns_youtube', user.sns_youtube or '')
            
            # パスワード変更
            if new_password:
                if len(new_password) < 8:
                    flash('パスワードは8文字以上である必要があります。', 'danger')
                    return render_template('admin/edit_user.html', user=user)
                user.password_hash = generate_password_hash(new_password)
            
            # 通知設定
            user.notify_on_publish = 'notify_on_publish' in request.form
            user.notify_on_comment = 'notify_on_comment' in request.form
            
            db.session.commit()
            flash('ユーザー情報を更新しました。', 'success')
            return redirect(url_for('admin.users'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"User update error: {e}")
            flash('ユーザー情報の更新に失敗しました。', 'danger')
    
    return render_template('admin/edit_user.html', user=user)

@admin_bp.route('/user/delete/<int:user_id>/', methods=['POST'])
@admin_required
def delete_user(user_id):
    """ユーザー削除"""
    user = User.query.get_or_404(user_id)
    
    # 削除制限チェック
    if user.id == current_user.id:
        flash('自分自身を削除することはできません。', 'danger')
        return redirect(url_for('admin.users'))
    
    admin_count = User.query.filter_by(role='admin').count()
    if user.role == 'admin' and admin_count <= 1:
        flash('最後の管理者を削除することはできません。', 'danger')
        return redirect(url_for('admin.users'))
    
    try:
        # 関連記事の処理
        user_articles = Article.query.filter_by(author_id=user.id).all()
        if user_articles:
            action = request.form.get('article_action', 'keep')
            if action == 'delete':
                for article in user_articles:
                    db.session.delete(article)
            elif action == 'transfer':
                transfer_to_id = request.form.get('transfer_to_user')
                if transfer_to_id:
                    for article in user_articles:
                        article.author_id = int(transfer_to_id)
        
        db.session.delete(user)
        db.session.commit()
        flash(f'ユーザー「{user.name}」を削除しました。', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"User deletion error: {e}")
        flash('ユーザーの削除に失敗しました。', 'danger')
    
    return redirect(url_for('admin.users'))

# 記事管理
@admin_bp.route('/articles/')
@admin_required
def articles():
    """記事一覧（シンプル版）"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # ページネーション
    articles_pagination = Article.query.order_by(Article.created_at.desc()).paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    # 基本統計
    total_articles = Article.query.count()
    published_articles = Article.query.filter_by(is_published=True).count()
    draft_articles = Article.query.filter_by(is_published=False).count()
    
    # 今月の記事数
    from datetime import datetime
    current_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    this_month_articles = Article.query.filter(Article.created_at >= current_month).count()
    
    return render_template('admin/articles.html', 
                         articles_list=articles_pagination,
                         total_articles=total_articles,
                         published_articles=published_articles,
                         draft_articles=draft_articles,
                         this_month_articles=this_month_articles)

@admin_bp.route('/article/create/', methods=['GET', 'POST'])
@admin_required
def create_article():
    """記事作成"""
    form = ArticleForm()
    all_categories = Category.query.order_by(Category.name).all()
    
    # カテゴリの選択肢を設定
    form.category_id.choices = [(0, 'カテゴリを選択してください')] + [(cat.id, cat.name) for cat in all_categories]
    
    if form.validate_on_submit():
        # デバッグ: ファイルが送信されているかチェック
        current_app.logger.info(f"Featured image data: {form.featured_image.data}")
        current_app.logger.info(f"Featured image filename: {form.featured_image.data.filename if form.featured_image.data else 'No file'}")
        
        # スラッグ重複チェック
        if Article.query.filter_by(slug=form.slug.data).first():
            flash('そのスラッグは既に使用されています。', 'danger')
        else:
            try:
                new_article = Article(
                    title=form.title.data,
                    slug=form.slug.data,
                    summary=form.summary.data,
                    body=form.body.data,
                    meta_title=form.meta_title.data,
                    meta_description=form.meta_description.data,
                    meta_keywords=form.meta_keywords.data,
                    canonical_url=form.canonical_url.data,
                    is_published=form.is_published.data,
                    allow_comments=form.allow_comments.data,
                    author_id=current_user.id,
                    created_at=datetime.utcnow()
                )
                
                # 公開日時の設定
                if form.is_published.data:
                    new_article.published_at = datetime.utcnow()
                
                # カテゴリ関連付け
                if form.category_id.data and form.category_id.data != 0:
                    category = Category.query.get(form.category_id.data)
                    if category:
                        new_article.categories.append(category)
                
                db.session.add(new_article)
                db.session.flush()  # IDを取得するためにflush
                
                # アイキャッチ画像の処理（IDが確定した後）
                cropped_image_data = request.form.get('cropped_image_data')
                
                if cropped_image_data:
                    # トリミング後の画像データがある場合
                    try:
                        current_app.logger.info(f"Processing cropped image data for new article ID: {new_article.id}")
                        featured_image = process_cropped_image(cropped_image_data, new_article.id)
                        if featured_image:
                            new_article.featured_image = featured_image
                            current_app.logger.info(f"New cropped featured image saved: {featured_image}")
                        else:
                            current_app.logger.error("Failed to process cropped featured image")
                    except Exception as img_error:
                        current_app.logger.error(f"Cropped image processing error: {img_error}")
                        flash('トリミング画像の処理中にエラーが発生しましたが、記事は作成されました。', 'warning')
                        
                elif form.featured_image.data and form.featured_image.data.filename:
                    # 通常の画像アップロード
                    try:
                        current_app.logger.info(f"Processing featured image for article ID: {new_article.id}")
                        featured_image = process_featured_image(form.featured_image.data, new_article.id)
                        if featured_image:
                            new_article.featured_image = featured_image
                            current_app.logger.info(f"Featured image saved: {featured_image}")
                        else:
                            current_app.logger.warning("Featured image processing failed, but continuing with article creation")
                    except Exception as img_error:
                        current_app.logger.error(f"Featured image processing error: {img_error}")
                        flash('画像の処理中にエラーが発生しましたが、記事は作成されました。', 'warning')
                
                db.session.commit()
                current_app.logger.info(f"Article created with featured_image: {new_article.featured_image}")
                flash('記事が作成されました。', 'success')
                return redirect(url_for('admin.articles'))
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Article creation error: {e}")
                flash(f'記事の作成に失敗しました: {str(e)}', 'danger')
    else:
        # バリデーションエラーがある場合
        if form.errors:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'{field}: {error}', 'danger')
    
    return render_template('admin/create_article.html', form=form, all_categories=all_categories)

@admin_bp.route('/article/edit/<int:article_id>/', methods=['GET', 'POST'])
@admin_required
def edit_article(article_id):
    """記事編集（従来型エディタ）"""
    article = Article.query.get_or_404(article_id)
    
    # ブロック型記事の場合はブロック型エディタにリダイレクト
    if article.use_block_editor:
        flash('この記事はブロック型エディタで作成されています。ブロック型エディタで編集してください。', 'info')
        return redirect(url_for('admin.edit_article_block_editor', article_id=article_id))
    form = ArticleForm(obj=article)
    all_categories = Category.query.order_by(Category.name).all()
    
    # カテゴリの選択肢を設定
    form.category_id.choices = [(0, 'カテゴリを選択してください')] + [(cat.id, cat.name) for cat in all_categories]
    
    # 現在のカテゴリを設定
    current_category = article.categories.first()
    if current_category:
        form.category_id.data = current_category.id
    
    if form.validate_on_submit():
        # スラッグ重複チェック（自分以外）
        existing = Article.query.filter(Article.id != article_id, Article.slug == form.slug.data).first()
        if existing:
            flash('そのスラッグは既に使用されています。', 'danger')
        else:
            try:
                # 基本フィールドの更新
                article.title = form.title.data
                article.slug = form.slug.data
                article.summary = form.summary.data
                article.body = form.body.data
                article.meta_title = form.meta_title.data
                article.meta_description = form.meta_description.data
                article.meta_keywords = form.meta_keywords.data
                article.canonical_url = form.canonical_url.data
                article.allow_comments = form.allow_comments.data
                article.updated_at = datetime.utcnow()
                
                # 公開状態の更新
                was_published = article.is_published
                article.is_published = form.is_published.data
                if form.is_published.data and not was_published:
                    article.published_at = datetime.utcnow()
                
                # アイキャッチ画像の処理
                cropped_image_data = request.form.get('cropped_image_data')
                
                if cropped_image_data:
                    # トリミング後の画像データがある場合
                    current_app.logger.info(f"Processing cropped image data for article ID: {article.id}")
                    # 古い画像削除
                    if article.featured_image:
                        current_app.logger.info(f"Deleting old image: {article.featured_image}")
                        delete_old_image(article.featured_image)
                    
                    featured_image = process_cropped_image(cropped_image_data, article.id)
                    if featured_image:
                        article.featured_image = featured_image
                        current_app.logger.info(f"New cropped featured image saved: {featured_image}")
                    else:
                        current_app.logger.error("Failed to process cropped featured image")
                        
                elif form.featured_image.data and form.featured_image.data.filename:
                    # 通常の画像アップロード
                    current_app.logger.info(f"Processing new featured image for article ID: {article.id}")
                    # 古い画像削除
                    if article.featured_image:
                        current_app.logger.info(f"Deleting old image: {article.featured_image}")
                        delete_old_image(article.featured_image)
                    
                    featured_image = process_featured_image(form.featured_image.data, article.id)
                    if featured_image:
                        article.featured_image = featured_image
                        current_app.logger.info(f"New featured image saved: {featured_image}")
                    else:
                        current_app.logger.error("Failed to process new featured image")
                
                # カテゴリ更新
                # dynamic relationshipの場合は直接clearできないため、手動で削除
                current_category_ids = [cat.id for cat in article.categories.all()]
                for cat_id in current_category_ids:
                    category_to_remove = Category.query.get(cat_id)
                    if category_to_remove:
                        article.categories.remove(category_to_remove)
                        
                if form.category_id.data and form.category_id.data != 0:
                    category = Category.query.get(form.category_id.data)
                    if category:
                        article.categories.append(category)
                
                db.session.commit()
                flash('記事が更新されました。', 'success')
                return redirect(url_for('admin.articles'))
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Article update error: {e}")
                flash('記事の更新に失敗しました。', 'danger')
    
    return render_template('admin/edit_article.html', form=form, article=article, all_categories=all_categories)


@admin_bp.route('/article/toggle_status/<int:article_id>/', methods=['POST'])
@admin_required
def toggle_article_status(article_id):
    """記事ステータスの切り替え"""
    from flask import jsonify
    from flask_wtf.csrf import validate_csrf
    from werkzeug.exceptions import BadRequest
    
    article = Article.query.get_or_404(article_id)
    
    try:
        # フォームデータから状態を取得
        new_status = request.form.get('is_published', 'false').lower() == 'true'
        was_published = article.is_published
        
        # ステータス更新
        article.is_published = new_status
        if new_status and not was_published:
            article.published_at = datetime.utcnow()
        
        db.session.commit()
        
        status_text = '公開' if new_status else '下書き'
        current_app.logger.info(f'Article {article.id} status changed to {status_text}')
        flash(f'記事ステータスを{status_text}に変更しました', 'success')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Status toggle error: {e}")
        flash(f'ステータス変更に失敗しました: {str(e)}', 'danger')
    
    return redirect(url_for('admin.articles'))

@admin_bp.route('/article/delete/<int:article_id>/', methods=['POST'])
@admin_required
def delete_article(article_id):
    """記事削除"""
    article = Article.query.get_or_404(article_id)
    article_title = article.title  # 削除前にタイトルを保存
    
    try:
        # SQLAlchemyのCASCADE設定により関連ブロックも自動削除される
        db.session.delete(article)
        db.session.commit()
        flash(f'記事「{article_title}」を削除しました。', 'success')
        current_app.logger.info(f"Article deleted successfully: {article_id}")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Article deletion error: {e}")
        print(f"Article deletion error: {e}")  # デバッグ用
        flash('記事の削除に失敗しました。', 'danger')
    
    return redirect(url_for('admin.articles'))

# カテゴリ管理
@admin_bp.route('/categories/')
@admin_required
def categories():
    """カテゴリ一覧"""
    page = request.args.get('page', 1, type=int)
    categories_list = Category.query.order_by(Category.name).paginate(
        page=page, per_page=10, error_out=False
    )
    
    # 統計情報を計算
    total_categories = Category.query.count()
    
    # 現在ページのカテゴリに関連する記事数
    current_page_articles = 0
    for category in categories_list.items:
        current_page_articles += category.articles.count() if category.articles else 0
    
    # 全カテゴリの記事数
    total_articles_in_categories = 0
    all_categories = Category.query.all()
    for category in all_categories:
        total_articles_in_categories += category.articles.count() if category.articles else 0
    
    # 記事が割り当てられていないカテゴリ数
    empty_categories = 0
    for category in all_categories:
        if not category.articles or category.articles.count() == 0:
            empty_categories += 1
    
    stats = {
        'total_categories': total_categories,
        'current_page_articles': current_page_articles,
        'total_articles_in_categories': total_articles_in_categories,
        'empty_categories': empty_categories
    }
    
    return render_template('admin/categories.html', 
                         categories_list=categories_list,
                         stats=stats)

@admin_bp.route('/category/create/', methods=['GET', 'POST'])
@admin_required
def create_category():
    """カテゴリ作成"""
    form = CategoryForm()
    
    if form.validate_on_submit():
        # スラッグ自動生成
        slug = form.slug.data or generate_slug_from_name(form.name.data)
        if not slug:
            flash('有効なスラッグを生成できませんでした。', 'danger')
            return render_template('admin/create_category.html', form=form)
        
        # 重複チェック
        if Category.query.filter_by(slug=slug).first():
            flash('そのスラッグは既に使用されています。', 'danger')
            return render_template('admin/create_category.html', form=form)
        
        if Category.query.filter_by(name=form.name.data).first():
            flash('そのカテゴリ名は既に使用されています。', 'danger')
            return render_template('admin/create_category.html', form=form)
        
        try:
            # カテゴリ作成
            new_category = Category(
                name=form.name.data,
                slug=slug,
                description=form.description.data,
                created_at=datetime.utcnow()
            )
            
            db.session.add(new_category)
            db.session.flush()  # IDを取得するためにflushを実行
            
            # OGP画像の処理
            if form.ogp_image.data:
                import sys
                sys.path.append(os.path.join(os.path.dirname(__file__), 'app', 'utils'))
                from helpers import process_ogp_image
                
                # クロップデータの取得
                crop_data = None
                if all([form.ogp_crop_x.data, form.ogp_crop_y.data, form.ogp_crop_width.data, form.ogp_crop_height.data]):
                    crop_data = {
                        'x': form.ogp_crop_x.data,
                        'y': form.ogp_crop_y.data,
                        'width': form.ogp_crop_width.data,
                        'height': form.ogp_crop_height.data
                    }
                    current_app.logger.info(f"Crop data: {crop_data}")
                
                ogp_image_path = process_ogp_image(form.ogp_image.data, new_category.id, crop_data)
                if ogp_image_path:
                    new_category.ogp_image = ogp_image_path
                    current_app.logger.info(f"OGP image saved: {ogp_image_path}")
                else:
                    flash('画像の処理中にエラーが発生しました。', 'warning')
            
            db.session.commit()
            flash('カテゴリが作成されました。', 'success')
            return redirect(url_for('admin.categories'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Category creation error: {e}")
            flash(f'カテゴリの作成中にエラーが発生しました: {str(e)}', 'danger')
    
    return render_template('admin/create_category.html', form=form)

@admin_bp.route('/category/edit/<int:category_id>/', methods=['GET', 'POST'])
@admin_required
def edit_category(category_id):
    """カテゴリ編集"""
    category = Category.query.get_or_404(category_id)
    form = CategoryForm(obj=category)
    
    if form.validate_on_submit():
        try:
            # データ更新
            category.name = form.name.data
            category.slug = form.slug.data
            category.description = form.description.data
            
            # OGP画像の処理
            if form.ogp_image.data:
                import sys
                sys.path.append(os.path.join(os.path.dirname(__file__), 'app', 'utils'))
                from helpers import process_ogp_image, delete_old_image
                
                # 古い画像を削除
                if category.ogp_image:
                    old_image_path = os.path.join(current_app.static_folder, category.ogp_image)
                    delete_old_image(old_image_path)
                
                # クロップデータの取得
                crop_data = None
                if all([form.ogp_crop_x.data, form.ogp_crop_y.data, form.ogp_crop_width.data, form.ogp_crop_height.data]):
                    crop_data = {
                        'x': form.ogp_crop_x.data,
                        'y': form.ogp_crop_y.data,
                        'width': form.ogp_crop_width.data,
                        'height': form.ogp_crop_height.data
                    }
                    current_app.logger.info(f"Crop data: {crop_data}")
                
                # 新しい画像を処理
                ogp_image_path = process_ogp_image(form.ogp_image.data, category.id, crop_data)
                if ogp_image_path:
                    category.ogp_image = ogp_image_path
                    current_app.logger.info(f"OGP image updated: {ogp_image_path}")
                else:
                    flash('画像の処理中にエラーが発生しました。', 'warning')
            
            db.session.commit()
            flash('カテゴリが正常に更新されました。', 'success')
            return redirect(url_for('admin.categories'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Category update error: {e}")
            flash('カテゴリの更新中にエラーが発生しました。', 'danger')
    
    return render_template('admin/edit_category.html', form=form, category=category)

@admin_bp.route('/category/delete/<int:category_id>/', methods=['POST'])
@admin_required
def delete_category(category_id):
    """カテゴリ削除"""
    category = Category.query.get_or_404(category_id)
    
    try:
        # 関連記事のカテゴリ関連付けを削除
        for article in category.articles:
            article.categories.remove(category)
        
        db.session.delete(category)
        db.session.commit()
        flash(f'カテゴリ「{category.name}」を削除しました。', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Category deletion error: {e}")
        flash('カテゴリの削除中にエラーが発生しました。', 'danger')
    
    return redirect(url_for('admin.categories'))

@admin_bp.route('/categories/bulk-delete', methods=['POST'])
@admin_required
def bulk_delete_categories():
    """カテゴリ一括削除"""
    category_ids = request.form.getlist('category_ids')
    
    if not category_ids:
        flash('削除するカテゴリが選択されていません。', 'warning')
        return redirect(url_for('admin.categories'))
    
    try:
        deleted_count = 0
        for category_id in category_ids:
            category = Category.query.get(category_id)
            if category:
                # 関連記事のカテゴリ関連付けを削除
                for article in category.articles:
                    article.categories.remove(category)
                
                db.session.delete(category)
                deleted_count += 1
        
        db.session.commit()
        flash(f'{deleted_count}個のカテゴリを削除しました。', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Bulk category deletion error: {e}")
        flash('カテゴリの削除中にエラーが発生しました。', 'danger')
    
    return redirect(url_for('admin.categories'))

# サイト設定
# Removed duplicate site_settings function

# コメント管理（admin.py の最後に追加）
@admin_bp.route('/comments/')
@admin_required
def comments():
    """コメント管理"""
    try:
        page = request.args.get('page', 1, type=int)
        status_filter = request.args.get('status', 'all')
        
        # Commentモデルが存在するかチェック
        if not hasattr(Comment, 'query'):
            flash('コメント機能は実装されていません。', 'info')
            return render_template('admin/comments.html',
                                 comments_list=None,
                                 status_filter=status_filter,
                                 total=0,
                                 approved=0,
                                 pending=0)
        
        query = Comment.query
        if status_filter == 'approved':
            if hasattr(Comment, 'is_approved'):
                query = query.filter(Comment.is_approved == True)
        elif status_filter == 'pending':
            if hasattr(Comment, 'is_approved'):
                query = query.filter(Comment.is_approved == False)
        
        comments_pagination = query.order_by(Comment.created_at.desc()).paginate(
            page=page, per_page=20, error_out=False
        )
        
        # 統計
        stats = {
            'total': get_safe_count(Comment),
            'approved': get_safe_count(Comment.query.filter(Comment.is_approved == True)) if hasattr(Comment, 'is_approved') else 0,
            'pending': get_safe_count(Comment.query.filter(Comment.is_approved == False)) if hasattr(Comment, 'is_approved') else 0
        }
        
        return render_template('admin/comments.html',
                             comments_list=comments_pagination,
                             status_filter=status_filter,
                             **stats)
                             
    except Exception as e:
        current_app.logger.error(f"Comments page error: {e}")
        
        # エラー時の空のページネーション
        class EmptyPagination:
            def __init__(self):
                self.items = []
                self.total = 0
                self.page = 1
                self.pages = 0
                self.per_page = 20
                self.has_prev = False
                self.has_next = False
                self.prev_num = None
                self.next_num = None
            
            def iter_pages(self, **kwargs):
                return []
        
        empty_pagination = EmptyPagination()
        stats = {
            'total': 0,
            'approved': 0,
            'pending': 0
        }
        
        flash('コメントデータの取得中にエラーが発生しました。', 'warning')
        return render_template('admin/comments.html',
                             comments_list=empty_pagination,
                             status_filter='all',
                             **stats)

@admin_bp.route('/comment/approve/<int:comment_id>/', methods=['POST'])
@admin_required
def approve_comment(comment_id):
    """コメント承認"""
    try:
        comment = Comment.query.get_or_404(comment_id)
        if hasattr(comment, 'is_approved'):
            comment.is_approved = True
            db.session.commit()
            flash('コメントを承認しました。', 'success')
        else:
            flash('承認機能は実装されていません。', 'warning')
    except Exception as e:
        current_app.logger.error(f"Comment approval error: {e}")
        flash('コメントの承認に失敗しました。', 'danger')
    
    return redirect(url_for('admin.comments'))

@admin_bp.route('/comment/reject/<int:comment_id>/', methods=['POST'])
@admin_required
def reject_comment(comment_id):
    """コメント拒否"""
    try:
        comment = Comment.query.get_or_404(comment_id)
        if hasattr(comment, 'is_approved'):
            comment.is_approved = False
            db.session.commit()
            flash('コメントを拒否しました。', 'info')
        else:
            flash('拒否機能は実装されていません。', 'warning')
    except Exception as e:
        current_app.logger.error(f"Comment rejection error: {e}")
        flash('コメントの拒否に失敗しました。', 'danger')
    
    return redirect(url_for('admin.comments'))

@admin_bp.route('/comment/delete/<int:comment_id>/', methods=['POST'])
@admin_required
def delete_comment(comment_id):
    """コメント削除"""
    try:
        comment = Comment.query.get_or_404(comment_id)
        db.session.delete(comment)
        db.session.commit()
        flash('コメントを削除しました。', 'success')
    except Exception as e:
        current_app.logger.error(f"Comment deletion error: {e}")
        flash('コメントの削除に失敗しました。', 'danger')
    
    return redirect(url_for('admin.comments'))

@admin_bp.route('/comments/bulk-action/', methods=['POST'])
@admin_required
def bulk_comment_action():
    """コメント一括操作"""
    action = request.form.get('action')
    comment_ids = request.form.getlist('comment_ids')
    
    if not comment_ids:
        flash('コメントが選択されていません。', 'warning')
        return redirect(url_for('admin.comments'))
    
    try:
        comments = Comment.query.filter(Comment.id.in_(comment_ids)).all()
        
        if action == 'approve' and hasattr(Comment, 'is_approved'):
            for comment in comments:
                comment.is_approved = True
            flash(f'{len(comments)}件のコメントを承認しました。', 'success')
        elif action == 'reject' and hasattr(Comment, 'is_approved'):
            for comment in comments:
                comment.is_approved = False
            flash(f'{len(comments)}件のコメントを拒否しました。', 'info')
        elif action == 'delete':
            for comment in comments:
                db.session.delete(comment)
            flash(f'{len(comments)}件のコメントを削除しました。', 'success')
        else:
            flash('無効な操作です。', 'warning')
            return redirect(url_for('admin.comments'))
        
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Bulk comment action error: {e}")
        flash('一括操作に失敗しました。', 'danger')
    
    return redirect(url_for('admin.comments'))

# ===== ブロック型エディタ機能 =====

@admin_bp.route('/article/block-editor/create/', methods=['GET', 'POST'])
@admin_required
def create_article_block_editor():
    """ブロック型エディタで記事作成"""
    if not BLOCK_EDITOR_AVAILABLE:
        flash('ブロックエディタが利用できません。', 'warning')
        return redirect(url_for('admin.create_article'))
    
    form = BlockEditorForm()
    all_categories = Category.query.order_by(Category.name).all()
    
    # カテゴリの選択肢を設定
    form.category_id.choices = [(0, 'カテゴリを選択してください')] + [(cat.id, cat.name) for cat in all_categories]
    
    if form.validate_on_submit():
        # フォームのaction値を確認
        action = request.form.get('action', 'save_draft')
        
        try:
            # スラッグの生成と重複チェック
            slug = form.slug.data or generate_slug_from_name(form.title.data)
            original_slug = slug
            counter = 1
            
            # スラッグの重複をチェックし、重複している場合は番号を追加
            while Article.query.filter_by(slug=slug).first():
                slug = f"{original_slug}-{counter}"
                counter += 1
                current_app.logger.info(f"Slug duplicated, trying: {slug}")
            
            # 新規記事作成
            article = Article(
                title=form.title.data,
                slug=slug,
                summary=form.summary.data,
                author_id=current_user.id,
                use_block_editor=True,
                is_published=(action == 'publish') or (request.form.get('is_published') == 'true'),
                allow_comments=request.form.get('allow_comments', 'true') == 'true',
                meta_title=form.meta_title.data,
                meta_description=form.meta_description.data,
                meta_keywords=form.meta_keywords.data,
                canonical_url=form.canonical_url.data
            )
            
            if action == 'publish':
                article.published_at = datetime.utcnow()
            
            db.session.add(article)
            db.session.flush()  # IDを取得するため
            
            # カテゴリ関連付け
            if form.category_id.data and form.category_id.data != 0:
                category = Category.query.get(form.category_id.data)
                if category:
                    article.categories.append(category)
            
            db.session.commit()
            flash('記事を作成しました。ブロックを追加して内容を編集してください。', 'success')
            
            # リダイレクト先URLにブロック追加パラメータがあるかチェック
            redirect_url = url_for('admin.edit_article_block_editor', article_id=article.id)
            add_block_type = request.args.get('add_block')
            if add_block_type:
                redirect_url += f'?add_block={add_block_type}'
            
            return redirect(redirect_url)
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Block editor article creation error: {e}")
            flash('記事の作成に失敗しました。', 'danger')
    
    return render_template('admin/block_editor.html', 
                         form=form, 
                         article=None, 
                         blocks=[], 
                         all_categories=all_categories)

@admin_bp.route('/article/block-editor/edit/<int:article_id>/', methods=['GET', 'POST'])
@admin_required
def edit_article_block_editor(article_id):
    """ブロック型エディタで記事編集"""
    if not BLOCK_EDITOR_AVAILABLE:
        flash('ブロックエディタが利用できません。', 'warning')
        return redirect(url_for('admin.edit_article', article_id=article_id))
    
    article = Article.query.get_or_404(article_id)
    
    # 従来型記事の場合は従来型エディタにリダイレクト
    if not article.use_block_editor:
        flash('この記事は従来型エディタで作成されています。従来型エディタで編集してください。', 'info')
        return redirect(url_for('admin.edit_article', article_id=article_id))
    
    # この記事は既にブロック型として設定済み
    
    form = BlockEditorForm(obj=article)
    all_categories = Category.query.order_by(Category.name).all()
    
    # カテゴリの選択肢を設定
    form.category_id.choices = [(0, 'カテゴリを選択してください')] + [(cat.id, cat.name) for cat in all_categories]
    
    # 現在のカテゴリを設定
    current_category = article.categories.first()
    if current_category:
        form.category_id.data = current_category.id
    
    # フォームに記事の現在の状態を反映
    form.is_published.data = 'true' if article.is_published else 'false'
    form.allow_comments.data = 'true' if article.allow_comments else 'false'
    
    # デバッグ用ログ
    current_app.logger.info(f"Article {article.id} - is_published: {article.is_published}, allow_comments: {article.allow_comments}")
    current_app.logger.info(f"Form data - is_published: {form.is_published.data}, allow_comments: {form.allow_comments.data}")
    
    # 記事のブロックを取得
    blocks = article.get_visible_blocks()
    
    # 初期ブロック追加の処理
    add_block_type = request.args.get('add_block')
    if add_block_type and BLOCK_EDITOR_AVAILABLE:
        try:
            block_type = BlockType.query.filter_by(type_name=add_block_type).first()
            if block_type:
                # 最大順序番号を取得
                max_order = db.session.query(func.max(ArticleBlock.sort_order)).filter_by(article_id=article.id).scalar() or 0
                
                # 新しいブロックを作成
                new_block = ArticleBlock(
                    article_id=article.id,
                    block_type_id=block_type.id,
                    sort_order=max_order + 1,
                    title=f'新しい{block_type.type_label}'
                )
                
                db.session.add(new_block)
                db.session.commit()
                flash(f'{block_type.type_label}を追加しました。', 'success')
                
                # ブロックリストを更新
                blocks = article.get_visible_blocks()
        except Exception as e:
            current_app.logger.error(f"Initial block creation error: {e}")
            flash('ブロックの追加に失敗しました。', 'warning')
    
    if form.validate_on_submit():
        try:
            # フォームのaction値を確認
            action = request.form.get('action', 'save_draft')
            
            # 記事基本情報の更新
            article.title = form.title.data
            article.slug = form.slug.data
            article.summary = form.summary.data
            article.meta_title = form.meta_title.data
            article.meta_description = form.meta_description.data
            article.meta_keywords = form.meta_keywords.data
            article.canonical_url = form.canonical_url.data
            article.allow_comments = request.form.get('allow_comments') == 'true'
            article.updated_at = datetime.utcnow()
            
            # 公開状態の更新
            was_published = article.is_published
            is_published = (action == 'publish') or (request.form.get('is_published') == 'true')
            article.is_published = is_published
            if is_published and not was_published:
                article.published_at = datetime.utcnow()
            
            # カテゴリ関連付けの更新
            # dynamic relationshipの場合は直接clearできないため、手動で削除
            current_category_ids = [cat.id for cat in article.categories.all()]
            for cat_id in current_category_ids:
                category_to_remove = Category.query.get(cat_id)
                if category_to_remove:
                    article.categories.remove(category_to_remove)
                    
            if form.category_id.data and form.category_id.data != 0:
                category = Category.query.get(form.category_id.data)
                if category:
                    article.categories.append(category)
            
            db.session.commit()
            flash('記事を更新しました。', 'success')
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Block editor article update error: {e}")
            flash('記事の更新に失敗しました。', 'danger')
    
    return render_template('admin/block_editor.html', 
                         form=form, 
                         article=article, 
                         blocks=blocks, 
                         all_categories=all_categories)

@admin_bp.route('/api/block/add', methods=['POST'])
@admin_required
def add_block():
    """新しいブロックを追加"""
    # 関数の開始を必ず記録
    print("=== add_block function called ===")
    current_app.logger.info("=== add_block function called ===")
    
    try:
        current_app.logger.info(f"Request method: {request.method}")
        current_app.logger.info(f"Request content type: {request.content_type}")
        current_app.logger.info(f"Request data raw: {request.data}")
        current_app.logger.info(f"Request form: {dict(request.form)}")
        current_app.logger.info(f"Request args: {dict(request.args)}")
        
        # リクエストの Content-Type を確認
        if 'application/json' not in (request.content_type or ''):
            current_app.logger.error(f"Invalid content type: {request.content_type}")
            return jsonify({'success': False, 'error': f'Content-Type が application/json ではありません: {request.content_type}'})
        
        data = request.get_json(force=True)
        current_app.logger.info(f"Parsed JSON data: {data}")
        
        if data is None:
            current_app.logger.error("No JSON data received")
            return jsonify({'success': False, 'error': 'JSONデータが受信されませんでした'})
        
        article_id = data.get('article_id')
        block_type_name = data.get('block_type')
        current_app.logger.info(f"article_id: {article_id}, block_type: {block_type_name}")
        
        if not article_id or not block_type_name:
            return jsonify({'success': False, 'error': '必要なパラメータが不足しています'})
        
        article = Article.query.get(article_id)
        if not article:
            return jsonify({'success': False, 'error': '記事が見つかりません'})
        
        block_type = BlockType.query.filter_by(type_name=block_type_name).first()
        if not block_type:
            return jsonify({'success': False, 'error': 'ブロックタイプが見つかりません'})
        
        # 最大順序番号を取得
        max_order = db.session.query(func.max(ArticleBlock.sort_order)).filter_by(article_id=article_id).scalar() or 0
        
        # 新しいブロックを作成
        new_block = ArticleBlock(
            article_id=article_id,
            block_type_id=block_type.id,
            sort_order=max_order + 1,
            title=f'新しい{block_type.type_label}'
        )
        
        db.session.add(new_block)
        db.session.commit()
        
        current_app.logger.info(f"Block added successfully: ID={new_block.id}, Type={block_type_name}")
        
        # ブロックHTMLを生成
        from flask import render_template_string
        block_html = render_template('admin/block_item.html', block=new_block)
        
        current_app.logger.info("Block HTML generated successfully")
        
        return jsonify({
            'success': True, 
            'block_id': new_block.id,
            'block_html': block_html
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Add block error: {e}")
        current_app.logger.error(f"Exception type: {type(e).__name__}")
        import traceback
        current_app.logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': f'ブロック追加エラー: {str(e)}'})

@admin_bp.route('/api/block/edit')
@admin_required
def edit_block():
    """ブロック編集フォームを取得"""
    try:
        block_id = request.args.get('block_id')
        if not block_id:
            return 'ブロックIDが指定されていません', 400
        
        block = ArticleBlock.query.get_or_404(block_id)
        form = create_block_form(block.block_type.type_name, obj=block)
        
        return render_template('admin/block_edit_form.html', block=block, form=form)
        
    except Exception as e:
        current_app.logger.error(f"Edit block form error: {e}")
        return 'ブロック編集フォームの読み込みに失敗しました', 500

@admin_bp.route('/api/block/save', methods=['POST'])
@admin_required
def save_block():
    """ブロックの保存"""
    try:
        current_app.logger.info("save_block function called")
        current_app.logger.info(f"Request method: {request.method}")
        current_app.logger.info(f"Request form keys: {list(request.form.keys())}")
        current_app.logger.info(f"Request headers: {dict(request.headers)}")
        
        # CSRFトークンをログで確認
        csrf_token = request.form.get('csrf_token')
        current_app.logger.info(f"CSRF token received: {csrf_token}")
        
        block_id = request.form.get('block_id')
        current_app.logger.info(f"Received block_id: {block_id}")
        
        if not block_id:
            current_app.logger.error("No block_id provided")
            return jsonify({'success': False, 'error': 'ブロックIDが指定されていません'})
        
        try:
            block = ArticleBlock.query.get(block_id)
            if not block:
                current_app.logger.error(f"Block not found: {block_id}")
                return jsonify({'success': False, 'error': f'ブロック（ID: {block_id}）が見つかりません'})
        except Exception as get_error:
            current_app.logger.error(f"Error getting block: {get_error}")
            return jsonify({'success': False, 'error': f'ブロック取得エラー: {str(get_error)}'})
        
        # フォーム検証を完全にスキップして直接更新
        current_app.logger.info(f"Form data: {dict(request.form)}")
        current_app.logger.info(f"Block type: {block.block_type.type_name}")
        current_app.logger.info(f"Block ID: {block_id}")
        
        # フォーム検証をスキップして直接フィールドを更新
        try:
            # ブロック共通フィールドの更新
            if 'title' in request.form:
                block.title = request.form.get('title', '')
            if 'css_classes' in request.form:
                block.css_classes = request.form.get('css_classes', '')
            
            # ブロックタイプ別の処理
            if block.is_text_block:
                content = request.form.get('content', '')
                current_app.logger.info(f"Content to save: {content}")
                block.content = content
                
            elif block.is_image_block or block.is_featured_image_block:
                # 画像メタデータの更新
                if 'image_alt_text' in request.form:
                    block.image_alt_text = request.form.get('image_alt_text', '')
                if 'image_caption' in request.form:
                    block.image_caption = request.form.get('image_caption', '')
                
                # 画像ファイルのアップロード処理
                if 'image_file' in request.files and request.files['image_file'].filename:
                    image_file = request.files['image_file']
                    current_app.logger.info(f"Processing image upload: {image_file.filename}")
                    
                    # トリミング情報を取得
                    crop_data = None
                    crop_x = request.form.get('crop_x')
                    crop_y = request.form.get('crop_y')
                    crop_width = request.form.get('crop_width')
                    crop_height = request.form.get('crop_height')
                    
                    if all([crop_x, crop_y, crop_width, crop_height]):
                        try:
                            crop_data = {
                                'x': int(float(crop_x)),
                                'y': int(float(crop_y)),
                                'width': int(float(crop_width)),
                                'height': int(float(crop_height))
                            }
                            current_app.logger.info(f"Crop data: {crop_data}")
                        except (ValueError, TypeError) as e:
                            current_app.logger.warning(f"Invalid crop data: {e}")
                            crop_data = None
                    
                    # 画像処理を実行
                    try:
                        if crop_data:
                            # トリミング付き画像処理
                            image_path = process_block_image_with_crop(
                                image_file, 
                                block.block_type.type_name, 
                                crop_data, 
                                block.id
                            )
                        else:
                            # 通常の画像処理
                            image_path = process_block_image(
                                image_file, 
                                block.block_type.type_name, 
                                block.id
                            )
                        
                        if image_path:
                            # 古い画像ファイルを削除
                            if block.image_path:
                                old_path = os.path.join(current_app.root_path, block.image_path)
                                if os.path.exists(old_path):
                                    os.remove(old_path)
                                    current_app.logger.info(f"Deleted old image: {old_path}")
                            
                            # 新しい画像パスを保存
                            block.image_path = image_path
                            current_app.logger.info(f"Image saved: {image_path}")
                        else:
                            current_app.logger.error("Image processing failed")
                            
                    except Exception as img_error:
                        current_app.logger.error(f"Image processing error: {img_error}")
                        # 画像処理が失敗してもメタデータの更新は続行
                
            elif block.is_sns_embed_block:
                if 'embed_url' in request.form:
                    embed_url = request.form.get('embed_url', '')
                    block.embed_url = embed_url
                    
                    # 表示モードの設定を保存
                    display_mode = request.form.get('display_mode', 'embed')
                    current_settings = block.get_settings_json()
                    current_settings['display_mode'] = display_mode
                    block.set_settings_json(current_settings)
                    current_app.logger.info(f"Display mode set to: {display_mode}")
                    
                    # SNSプラットフォーム検出
                    platform = detect_sns_platform(embed_url)
                    if platform:
                        block.embed_platform = platform
                        current_app.logger.info(f"Detected SNS platform: {platform}")
                        
                        # SNS固有IDの抽出
                        sns_id = extract_sns_id(embed_url, platform)
                        if sns_id:
                            block.embed_id = sns_id
                            current_app.logger.info(f"Extracted SNS ID: {sns_id}")
                            
                            # 埋込HTMLの生成（従来モード用）
                            embed_html = generate_sns_embed_html(embed_url, platform, sns_id)
                            if embed_html:
                                block.embed_html = embed_html
                                current_app.logger.info("Generated embed HTML")
                        else:
                            current_app.logger.warning(f"Could not extract SNS ID from: {embed_url}")
                    else:
                        current_app.logger.warning(f"Unsupported SNS platform: {embed_url}")
                        block.embed_platform = 'unknown'
                    
                    # OGPカード表示モード用のOGP情報を保存
                    if display_mode == 'ogp_card':
                        # OGP URLとして埋込URLを設定
                        block.ogp_url = embed_url
                        
                        # 自動OGP取得を試行（手動入力が空の場合のみ）
                        auto_fetch_ogp = (
                            not request.form.get('ogp_title', '').strip() and
                            not request.form.get('ogp_description', '').strip() and
                            not request.form.get('ogp_site_name', '').strip()
                        )
                        
                        if auto_fetch_ogp and embed_url:
                            current_app.logger.info(f"Auto-fetching SNS OGP data for: {embed_url}")
                            try:
                                from block_utils import fetch_sns_ogp_data
                                ogp_data = fetch_sns_ogp_data(embed_url, platform)
                                
                                if ogp_data:
                                    current_app.logger.info(f"SNS OGP data retrieved: {ogp_data}")
                                    block.ogp_title = ogp_data.get('title', '')
                                    block.ogp_description = ogp_data.get('description', '')
                                    block.ogp_site_name = ogp_data.get('site_name', '')
                                    block.ogp_image = ogp_data.get('image', '')
                                else:
                                    current_app.logger.warning(f"Failed to fetch SNS OGP data for: {embed_url}")
                            
                            except Exception as ogp_error:
                                current_app.logger.error(f"SNS OGP fetch error: {ogp_error}")
                        
                        # 手動入力値で上書き（手動入力が優先）
                        if 'ogp_title' in request.form and request.form.get('ogp_title', '').strip():
                            block.ogp_title = request.form.get('ogp_title', '')
                        if 'ogp_description' in request.form and request.form.get('ogp_description', '').strip():
                            block.ogp_description = request.form.get('ogp_description', '')
                        if 'ogp_site_name' in request.form and request.form.get('ogp_site_name', '').strip():
                            block.ogp_site_name = request.form.get('ogp_site_name', '')
                        if 'ogp_image' in request.form and request.form.get('ogp_image', '').strip():
                            block.ogp_image = request.form.get('ogp_image', '')
                        
                        block.ogp_cached_at = datetime.utcnow()
                        current_app.logger.info("SNS OGP data saved for embed block")
                
            elif block.is_external_article_block:
                # 外部記事URLの更新
                external_url = request.form.get('external_url', '')
                if 'external_url' in request.form and external_url:
                    block.ogp_url = external_url
                    
                    # OGPデータを自動取得
                    current_app.logger.info(f"Fetching OGP data for: {external_url}")
                    try:
                        ogp_data = fetch_ogp_data(external_url)
                        if ogp_data:
                            current_app.logger.info(f"OGP data retrieved: {ogp_data}")
                            
                            # 手動入力が優先、自動取得は空欄のみ埋める
                            if not request.form.get('ogp_title', '').strip():
                                block.ogp_title = ogp_data.get('title', '')
                            else:
                                block.ogp_title = request.form.get('ogp_title', '')
                                
                            if not request.form.get('ogp_description', '').strip():
                                block.ogp_description = ogp_data.get('description', '')
                            else:
                                block.ogp_description = request.form.get('ogp_description', '')
                                
                            if not request.form.get('ogp_site_name', '').strip():
                                block.ogp_site_name = ogp_data.get('site_name', '')
                            else:
                                block.ogp_site_name = request.form.get('ogp_site_name', '')
                                
                            # OGP画像の処理は将来実装
                            # block.ogp_image = ogp_data.get('image', '')
                        else:
                            current_app.logger.warning(f"Failed to fetch OGP data for: {external_url}")
                            # 手動入力値を使用
                            block.ogp_title = request.form.get('ogp_title', '')
                            block.ogp_description = request.form.get('ogp_description', '')
                            block.ogp_site_name = request.form.get('ogp_site_name', '')
                    except Exception as ogp_error:
                        current_app.logger.error(f"OGP fetch error: {ogp_error}")
                        # エラー時は手動入力値を使用
                        block.ogp_title = request.form.get('ogp_title', '')
                        block.ogp_description = request.form.get('ogp_description', '')
                        block.ogp_site_name = request.form.get('ogp_site_name', '')
                else:
                    # 手動でOGP情報を更新
                    if 'ogp_title' in request.form:
                        block.ogp_title = request.form.get('ogp_title', '')
                    if 'ogp_description' in request.form:
                        block.ogp_description = request.form.get('ogp_description', '')
                    if 'ogp_site_name' in request.form:
                        block.ogp_site_name = request.form.get('ogp_site_name', '')
            
            block.updated_at = datetime.utcnow()
            db.session.commit()
            
            current_app.logger.info(f"Block saved successfully: {block_id}")
            
            # 更新後のブロックHTMLを生成
            try:
                block_html = render_template('admin/block_item.html', block=block)
                current_app.logger.info("Block HTML rendered successfully")
            except Exception as render_error:
                current_app.logger.error(f"Template render error: {render_error}")
                # HTMLレンダリングが失敗してもブロックは保存されているので成功とする
                block_html = f'<div class="block-item">ブロック保存済み (ID: {block.id})</div>'
            
            # プレビューHTMLも生成
            try:
                from block_utils import render_block_content
                preview_html = render_block_content(block)
                current_app.logger.info("Block preview HTML rendered successfully")
            except Exception as preview_error:
                current_app.logger.error(f"Preview render error: {preview_error}")
                preview_html = '<div class="block-preview-error">プレビューの生成に失敗しました</div>'
            
            return jsonify({
                'success': True,
                'block_html': block_html,
                'preview_html': preview_html,
                'message': 'ブロックが正常に保存されました'
            })
            
        except Exception as update_error:
            db.session.rollback()
            current_app.logger.error(f"Block update error: {update_error}")
            return jsonify({'success': False, 'error': f'ブロック更新エラー: {str(update_error)}'})
            
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Save block error: {e}")
        current_app.logger.error(f"Exception type: {type(e).__name__}")
        import traceback
        current_app.logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': f'保存中にエラーが発生しました: {str(e)}'})

@admin_bp.route('/api/block/delete', methods=['POST'])
@admin_required
def delete_block():
    """ブロックの削除"""
    try:
        data = request.get_json()
        block_id = data.get('block_id')
        
        if not block_id:
            return jsonify({'success': False, 'error': 'ブロックIDが指定されていません'})
        
        block = ArticleBlock.query.get_or_404(block_id)
        
        # 画像ファイルが存在する場合は削除
        if block.image_path:
            from block_utils import delete_block_image
            delete_block_image(block.image_path)
        
        db.session.delete(block)
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Delete block error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/api/block/reorder', methods=['POST'])
@admin_required
def reorder_blocks():
    """ブロックの順序変更"""
    try:
        data = request.get_json()
        block_ids = data.get('block_ids', [])
        
        for index, block_id in enumerate(block_ids, 1):
            block = ArticleBlock.query.get(block_id)
            if block:
                block.sort_order = index
        
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Reorder blocks error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/api/fetch-ogp', methods=['POST'])
@admin_required  
def fetch_ogp():
    """OGP情報取得API"""
    if not BLOCK_EDITOR_AVAILABLE:
        return jsonify({'success': False, 'error': 'Block editor not available'})
    
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'success': False, 'error': 'URL is required'})
        
        # SNS URLかどうかを判定してOGP情報を取得
        platform = detect_sns_platform(url)
        
        if platform:
            # SNS URLs用の専用OGP取得
            current_app.logger.info(f"Detected SNS platform: {platform} for URL: {url}")
            from block_utils import fetch_sns_ogp_data
            ogp_data = fetch_sns_ogp_data(url, platform)
        else:
            # 一般的なOGP取得
            ogp_data = fetch_ogp_data(url)
        
        if ogp_data:
            return jsonify({
                'success': True,
                'ogp_data': {
                    'title': ogp_data.get('title', ''),
                    'description': ogp_data.get('description', ''),
                    'site_name': ogp_data.get('site_name', ''),
                    'image': ogp_data.get('image', '')
                }
            })
        else:
            return jsonify({'success': False, 'error': 'Could not fetch OGP data'})
            
    except Exception as e:
        current_app.logger.error(f"OGP fetch error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/api/remove-featured-image', methods=['POST'])
@admin_required
def remove_featured_image():
    """アイキャッチ画像を削除"""
    try:
        data = request.get_json()
        article_id = data.get('article_id')
        
        if not article_id:
            return jsonify({'success': False, 'error': '記事IDが指定されていません'})
        
        article = Article.query.get_or_404(article_id)
        
        # 画像ファイルを削除
        if article.featured_image:
            if delete_old_image(article.featured_image):
                current_app.logger.info(f"Deleted featured image: {article.featured_image}")
            
            # データベースからも削除
            article.featured_image = None
            db.session.commit()
            
            return jsonify({'success': True, 'message': 'アイキャッチ画像を削除しました'})
        else:
            return jsonify({'success': False, 'error': 'アイキャッチ画像が設定されていません'})
            
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Remove featured image error: {e}")
        return jsonify({'success': False, 'error': f'画像削除エラー: {str(e)}'})

@admin_bp.route('/article/preview/<int:article_id>')
@admin_required
def article_preview(article_id):
    """記事プレビュー（ブロックエディタ対応）"""
    article = Article.query.get_or_404(article_id)
    
    if article.use_block_editor:
        blocks = article.get_visible_blocks()
        return render_template('admin/article_preview.html', article=article, blocks=blocks)
    else:
        return render_template('article_detail.html', article=article, is_preview=True)

# ===============================
# WordPress インポート機能
# ===============================

@admin_bp.route('/wordpress-import/', methods=['GET', 'POST'])
@admin_required
def wordpress_import():
    """WordPress インポート画面"""
    form = WordPressImportForm()
    import_results = None
    
    if form.validate_on_submit():
        try:
            # XMLファイルの保存
            xml_file = form.xml_file.data
            filename = secure_filename(xml_file.filename)
            timestamp = int(time.time())
            filename = f"wp_import_{timestamp}_{filename}"
            
            # 一時保存ディレクトリ
            temp_dir = os.path.join(current_app.instance_path, 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            xml_path = os.path.join(temp_dir, filename)
            xml_file.save(xml_path)
            
            # 必要なモジュールをインポート
            import xml.etree.ElementTree as ET
            import html
            import requests
            from urllib.parse import urlparse
            
            # WordPress インポーターの統合版を作成
            class WebWordPressImporter:
                """Web版 WordPress インポーター"""
                
                def __init__(self, xml_file, author_id, options):
                    self.xml_file = xml_file
                    self.author_id = author_id
                    self.dry_run = options.get('dry_run', False)
                    self.import_categories = options.get('import_categories', True)
                    self.import_images = options.get('import_images', True)
                    self.skip_duplicates = options.get('skip_duplicates', True)
                    self.stats = {
                        'categories_imported': 0,
                        'posts_imported': 0,
                        'images_downloaded': 0,
                        'errors': [],
                        'skipped': []
                    }
                
                def run(self):
                    """インポート実行"""
                    
                    # WordPress XML の名前空間定義
                    namespaces = {
                        'wp': 'http://wordpress.org/export/1.2/',
                        'dc': 'http://purl.org/dc/elements/1.1/',
                        'content': 'http://purl.org/rss/1.0/modules/content/',
                        'excerpt': 'http://wordpress.org/export/1.2/excerpt/'
                    }
                    
                    try:
                        # XML解析
                        tree = ET.parse(self.xml_file)
                        root = tree.getroot()
                        
                        # カテゴリ抽出・インポート
                        if self.import_categories:
                            categories = self._extract_categories(root, namespaces)
                            self._import_categories(categories)
                        
                        # 記事抽出・インポート
                        posts = self._extract_posts(root, namespaces)
                        self._import_posts(posts)
                        
                        return True
                        
                    except Exception as e:
                        current_app.logger.error(f"WordPress import error: {e}")
                        self.stats['errors'].append(f"インポートエラー: {e}")
                        return False
                
                def _generate_slug(self, text):
                    """スラッグ生成"""
                    if not text:
                        return 'untitled'
                    slug = re.sub(r'[^\w\s-]', '', text.lower())
                    slug = re.sub(r'[-\s]+', '-', slug)
                    return slug.strip('-')[:50]
                
                def _extract_categories(self, root, namespaces):
                    """カテゴリ抽出"""
                    categories = []
                    for cat_elem in root.findall('.//wp:category', namespaces):
                        cat_name = cat_elem.find('wp:cat_name', namespaces)
                        category_nicename = cat_elem.find('wp:category_nicename', namespaces)
                        category_description = cat_elem.find('wp:category_description', namespaces)
                        
                        if cat_name is not None and cat_name.text:
                            categories.append({
                                'name': html.unescape(cat_name.text),
                                'slug': category_nicename.text if category_nicename is not None else self._generate_slug(cat_name.text),
                                'description': html.unescape(category_description.text) if category_description is not None and category_description.text else ''
                            })
                    return categories
                
                def _extract_posts(self, root, namespaces):
                    """記事抽出"""
                    posts = []
                    for item in root.findall('.//item'):
                        post_type = item.find('wp:post_type', namespaces)
                        post_status = item.find('wp:status', namespaces)
                        
                        if (post_type is not None and post_type.text == 'post' and 
                            post_status is not None and post_status.text == 'publish'):
                            
                            title = item.find('title')
                            content = item.find('content:encoded', namespaces)
                            excerpt = item.find('excerpt:encoded', namespaces)
                            post_name = item.find('wp:post_name', namespaces)
                            post_date = item.find('wp:post_date', namespaces)
                            
                            # カテゴリ抽出
                            categories = []
                            for cat in item.findall('category[@domain="category"]'):
                                if cat.text:
                                    categories.append(cat.text)
                            
                            posts.append({
                                'title': html.unescape(title.text) if title is not None else 'Untitled',
                                'slug': post_name.text if post_name is not None else self._generate_slug(title.text if title is not None else 'untitled'),
                                'content': html.unescape(content.text) if content is not None else '',
                                'summary': html.unescape(excerpt.text) if excerpt is not None and excerpt.text else '',
                                'published_at': self._parse_wp_date(post_date.text if post_date is not None else ''),
                                'categories': categories
                            })
                    return posts
                
                def _parse_wp_date(self, date_str):
                    """日付解析"""
                    if not date_str:
                        return datetime.now()
                    try:
                        return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        return datetime.now()
                
                def _import_categories(self, categories):
                    """カテゴリインポート"""
                    for category_data in categories:
                        try:
                            if self.skip_duplicates:
                                existing = Category.query.filter_by(slug=category_data['slug']).first()
                                if existing:
                                    self.stats['skipped'].append(f"カテゴリ: {category_data['name']}")
                                    continue
                            
                            if not self.dry_run:
                                category = Category(
                                    name=category_data['name'],
                                    slug=category_data['slug'],
                                    description=category_data['description']
                                )
                                db.session.add(category)
                                db.session.commit()
                            
                            self.stats['categories_imported'] += 1
                            
                        except Exception as e:
                            self.stats['errors'].append(f"カテゴリ作成失敗: {category_data['name']} - {e}")
                            db.session.rollback()
                
                def _import_posts(self, posts):
                    """記事インポート"""
                    for post_data in posts:
                        try:
                            if self.skip_duplicates:
                                existing = Article.query.filter_by(slug=post_data['slug']).first()
                                if existing:
                                    self.stats['skipped'].append(f"記事: {post_data['title']}")
                                    continue
                            
                            if not self.dry_run:
                                article = Article(
                                    title=post_data['title'],
                                    slug=post_data['slug'],
                                    content=post_data['content'],
                                    summary=post_data['summary'],
                                    status='published',
                                    published_at=post_data['published_at'],
                                    author_id=self.author_id,
                                    use_block_editor=False
                                )
                                db.session.add(article)
                                db.session.flush()
                                
                                # カテゴリ関連付け
                                for category_name in post_data['categories']:
                                    category = Category.query.filter_by(name=category_name).first()
                                    if not category:
                                        category_slug = self._generate_slug(category_name)
                                        category = Category.query.filter_by(slug=category_slug).first()
                                    
                                    if category:
                                        article_category = ArticleCategory(
                                            article_id=article.id,
                                            category_id=category.id
                                        )
                                        db.session.add(article_category)
                                
                                db.session.commit()
                            
                            self.stats['posts_imported'] += 1
                            
                        except Exception as e:
                            self.stats['errors'].append(f"記事作成失敗: {post_data['title']} - {e}")
                            db.session.rollback()
            
            # インポート実行
            options = {
                'dry_run': form.dry_run.data,
                'import_categories': form.import_categories.data,
                'import_images': form.import_images.data,
                'skip_duplicates': form.skip_duplicates.data
            }
            
            importer = WebWordPressImporter(xml_path, form.author_id.data, options)
            success = importer.run()
            import_results = importer.stats
            
            # 一時ファイル削除
            try:
                os.remove(xml_path)
            except:
                pass
            
            if success:
                flash(f'インポート完了: カテゴリ{import_results["categories_imported"]}個、記事{import_results["posts_imported"]}個', 'success')
            else:
                flash('インポート中にエラーが発生しました', 'danger')
                
        except Exception as e:
            current_app.logger.error(f"WordPress import form error: {e}")
            flash(f'インポートエラー: {e}', 'danger')
    
    return render_template('admin/wordpress_import.html', 
                         form=form, 
                         import_results=import_results)

# ===============================
# Google Analytics 設定機能
# ===============================

@admin_bp.route('/analytics/', methods=['GET', 'POST'])
@admin_required
def analytics_settings():
    """Google Analytics設定画面"""
    form = GoogleAnalyticsForm()
    
    # 現在の設定値を取得してフォームに設定
    if request.method == 'GET':
        form.google_analytics_enabled.data = SiteSetting.get_setting('google_analytics_enabled', 'false').lower() == 'true'
        form.google_analytics_id.data = SiteSetting.get_setting('google_analytics_id', '')
        form.google_tag_manager_id.data = SiteSetting.get_setting('google_tag_manager_id', '')
        form.custom_analytics_code.data = SiteSetting.get_setting('custom_analytics_code', '')
        form.analytics_track_admin.data = SiteSetting.get_setting('analytics_track_admin', 'false').lower() == 'true'
    
    if form.validate_on_submit():
        try:
            # 設定を保存
            SiteSetting.set_setting('google_analytics_enabled', 
                                   'true' if form.google_analytics_enabled.data else 'false',
                                   'Google Analyticsを有効にする', 'boolean', True)
            
            SiteSetting.set_setting('google_analytics_id', 
                                   form.google_analytics_id.data or '',
                                   'Google Analytics 4 Measurement ID', 'text', True)
            
            SiteSetting.set_setting('google_tag_manager_id', 
                                   form.google_tag_manager_id.data or '',
                                   'Google Tag Manager Container ID', 'text', True)
            
            SiteSetting.set_setting('custom_analytics_code', 
                                   form.custom_analytics_code.data or '',
                                   'カスタムアナリティクスコード', 'text', True)
            
            SiteSetting.set_setting('analytics_track_admin', 
                                   'true' if form.analytics_track_admin.data else 'false',
                                   '管理者のアクセスも追跡する', 'boolean', False)
            
            flash('Google Analytics設定を保存しました', 'success')
            current_app.logger.info('Google Analytics settings updated')
            
        except Exception as e:
            current_app.logger.error(f"Analytics settings save error: {e}")
            flash(f'設定の保存に失敗しました: {str(e)}', 'danger')
    else:
        # バリデーションエラーがある場合
        if form.errors:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'{field}: {error}', 'danger')
    
    # 現在の設定状況を取得（表示用）
    current_settings = {
        'google_analytics_enabled': SiteSetting.get_setting('google_analytics_enabled', 'false'),
        'google_analytics_id': SiteSetting.get_setting('google_analytics_id', ''),
        'google_tag_manager_id': SiteSetting.get_setting('google_tag_manager_id', ''),
        'analytics_track_admin': SiteSetting.get_setting('analytics_track_admin', 'false')
    }
    
    return render_template('admin/analytics_settings.html', 
                         form=form, 
                         current_settings=current_settings)

# ===============================
# アクセスログアナライザー機能
# ===============================

@admin_bp.route('/access-logs/', methods=['GET'])
@admin_required
def access_logs():
    """アクセスログ分析画面"""
    from access_log_analyzer import AccessLogAnalyzer
    
    log_files = []
    reports = {}
    error_message = None
    
    try:
        # 利用可能なログファイルを検索
        log_patterns = ['flask.log', 'server.log', 'access.log', 'app.log']
        for pattern in log_patterns:
            if os.path.exists(pattern):
                log_files.append(pattern)
        
        # デフォルトのログファイルを分析
        if log_files:
            primary_log = log_files[0]
            analyzer = AccessLogAnalyzer(primary_log)
            
            # 最新1000行のみ分析（パフォーマンス考慮）
            stats = analyzer.analyze_logs(max_lines=1000)
            reports[primary_log] = analyzer.generate_report()
            
            current_app.logger.info(f"Access log analysis completed for {primary_log}")
        else:
            error_message = "アクセスログファイルが見つかりません"
    
    except Exception as e:
        current_app.logger.error(f"Access log analysis error: {e}")
        error_message = f"ログ分析エラー: {str(e)}"
    
    return render_template('admin/access_logs.html', 
                         log_files=log_files,
                         reports=reports,
                         error_message=error_message)

@admin_bp.route('/access-logs/download/<log_file>')
@admin_required  
def download_log_report(log_file):
    """ログレポートのJSONダウンロード"""
    from access_log_analyzer import AccessLogAnalyzer
    from flask import jsonify
    
    try:
        if not os.path.exists(log_file):
            return jsonify({'error': 'ログファイルが見つかりません'}), 404
        
        analyzer = AccessLogAnalyzer(log_file)
        stats = analyzer.analyze_logs(max_lines=5000)  # より多くのデータを分析
        report = analyzer.generate_report()
        
        # タイムスタンプを追加
        report['generated_at'] = datetime.now().isoformat()
        report['log_file'] = log_file
        
        return jsonify(report)
    
    except Exception as e:
        current_app.logger.error(f"Log report download error: {e}")
        return jsonify({'error': str(e)}), 500

# ===============================
# AI/LLM SEO対策機能
# ===============================

@admin_bp.route('/seo-tools/', methods=['GET'])
@admin_required
def seo_tools():
    """SEO対策ツール画面"""
    # 最近の記事を取得（SEO分析対象）
    recent_articles = Article.query.order_by(Article.created_at.desc()).limit(10).all()
    
    return render_template('admin/seo_tools.html', 
                         recent_articles=recent_articles)

@admin_bp.route('/seo-analyze/<int:article_id>', methods=['GET', 'POST'])
@admin_required
def seo_analyze_article(article_id):
    """記事のSEO分析"""
    from seo_optimizer import SEOOptimizer
    
    article = Article.query.get_or_404(article_id)
    analysis_result = None
    llm_suggestions = None
    
    try:
        optimizer = SEOOptimizer()
        
        # 基本SEO分析
        content = article.content or article.body or ''
        target_keywords = article.meta_keywords.split(',') if article.meta_keywords else []
        target_keywords = [kw.strip() for kw in target_keywords if kw.strip()]
        
        analysis_result = optimizer.analyze_content(
            title=article.title,
            content=content,
            target_keywords=target_keywords
        )
        
        # LLM提案生成（オプション）
        if request.method == 'POST' and request.form.get('generate_llm_suggestions'):
            llm_suggestions = optimizer.generate_llm_suggestions(
                title=article.title,
                content=content,
                target_keywords=target_keywords
            )
        
        current_app.logger.info(f"SEO analysis completed for article {article_id}")
        
    except Exception as e:
        current_app.logger.error(f"SEO analysis error: {e}")
        flash(f'SEO分析エラー: {str(e)}', 'danger')
    
    return render_template('admin/seo_analyze.html',
                         article=article,
                         analysis=analysis_result,
                         llm_suggestions=llm_suggestions)

@admin_bp.route('/seo-batch-analyze/', methods=['GET', 'POST'])
@admin_required
def seo_batch_analyze():
    """複数記事の一括SEO分析"""
    from seo_optimizer import SEOOptimizer
    
    results = []
    
    if request.method == 'POST':
        try:
            # 分析対象記事の選択
            article_ids = request.form.getlist('article_ids')
            if not article_ids:
                flash('分析対象の記事を選択してください', 'warning')
                return redirect(url_for('admin.seo_batch_analyze'))
            
            optimizer = SEOOptimizer()
            
            for article_id in article_ids:
                article = Article.query.get(int(article_id))
                if not article:
                    continue
                
                content = article.content or article.body or ''
                target_keywords = article.meta_keywords.split(',') if article.meta_keywords else []
                target_keywords = [kw.strip() for kw in target_keywords if kw.strip()]
                
                analysis = optimizer.analyze_content(
                    title=article.title,
                    content=content,
                    target_keywords=target_keywords
                )
                
                results.append({
                    'article': article,
                    'analysis': analysis
                })
            
            flash(f'{len(results)}件の記事を分析しました', 'success')
            
        except Exception as e:
            current_app.logger.error(f"Batch SEO analysis error: {e}")
            flash(f'一括分析エラー: {str(e)}', 'danger')
    
    # 分析対象記事一覧
    articles = Article.query.order_by(Article.created_at.desc()).limit(50).all()
    
    return render_template('admin/seo_batch_analyze.html',
                         articles=articles,
                         results=results)

@admin_bp.route('/api/seo-suggestions', methods=['POST'])
@admin_required
def api_seo_suggestions():
    """SEO改善提案API"""
    from seo_optimizer import SEOOptimizer
    
    try:
        data = request.get_json()
        title = data.get('title', '')
        content = data.get('content', '')
        keywords = data.get('keywords', [])
        
        if not title and not content:
            return jsonify({'error': 'タイトルまたはコンテンツが必要です'}), 400
        
        optimizer = SEOOptimizer()
        analysis = optimizer.analyze_content(title, content, keywords)
        
        return jsonify({
            'success': True,
            'analysis': analysis
        })
        
    except Exception as e:
        current_app.logger.error(f"SEO suggestions API error: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/site_settings/', methods=['GET', 'POST'])
@admin_required
def site_settings():
    """サイト設定画面"""
    if request.method == 'POST':
        try:
            # サイト基本設定
            settings_to_update = [
                'site_title', 'site_subtitle', 'site_description', 'site_keywords',
                'site_author', 'site_email', 'site_url', 'site_logo',
                'contact_email', 'contact_phone', 'contact_address',
                'social_twitter', 'social_facebook', 'social_instagram', 'social_youtube',
                'seo_google_analytics', 'seo_google_search_console', 'seo_google_tag_manager',
                'maintenance_mode', 'registration_enabled', 'comments_enabled',
                'max_upload_size', 'allowed_file_types', 'posts_per_page'
            ]
            
            for setting_key in settings_to_update:
                setting_value = request.form.get(setting_key, '')
                
                # 既存設定を取得または新規作成
                setting = SiteSetting.query.filter_by(key=setting_key).first()
                if setting:
                    setting.value = setting_value
                else:
                    setting = SiteSetting(key=setting_key, value=setting_value)
                    db.session.add(setting)
            
            db.session.commit()
            flash('サイト設定を更新しました', 'success')
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Site settings update error: {e}")
            flash(f'設定更新エラー: {str(e)}', 'danger')
    
    # 現在の設定値を取得
    settings = {}
    all_settings = SiteSetting.query.all()
    for setting in all_settings:
        settings[setting.key] = setting.value
    
    return render_template('admin/site_settings.html', settings=settings)

@admin_bp.route('/preview_markdown', methods=['POST'])
@admin_required
def preview_markdown():
    """Markdownプレビュー用エンドポイント"""
    markdown_text = request.form.get('markdown_text', '')
    
    if not markdown_text:
        return '<p class="text-muted">プレビューを表示するには本文を入力してください。</p>'
    
    try:
        # app.pyのmarkdown_filterを使用してHTMLに変換
        from app import markdown_filter
        html_content = markdown_filter(markdown_text)
        return str(html_content)
    except Exception as e:
        current_app.logger.error(f"Markdown preview error: {e}")
        return f'<p class="text-danger">プレビューエラー: {str(e)}</p>'

@admin_bp.route('/upload_image', methods=['POST'])
@admin_required
def upload_image():
    """画像アップロード用APIエンドポイント"""
    try:
        # ファイル取得
        if 'image' not in request.files:
            return jsonify({
                'success': False,
                'error': '画像ファイルが送信されていません。'
            }), 400
        
        image_file = request.files['image']
        alt_text = request.form.get('alt_text', '').strip()
        caption = request.form.get('caption', '').strip()
        description = request.form.get('description', '').strip()
        
        # 画像処理
        uploaded_image, error = process_uploaded_image(
            image_file, alt_text, caption, description
        )
        
        if error:
            return jsonify({
                'success': False,
                'error': error
            }), 400
        
        # 成功レスポンス
        return jsonify({
            'success': True,
            'image': {
                'id': uploaded_image.id,
                'filename': uploaded_image.filename,
                'original_filename': uploaded_image.original_filename,
                'url': uploaded_image.file_url,
                'alt_text': uploaded_image.alt_text,
                'caption': uploaded_image.caption,
                'width': uploaded_image.width,
                'height': uploaded_image.height,
                'file_size': uploaded_image.file_size_mb,
                'markdown': uploaded_image.markdown_syntax
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Upload image API error: {e}")
        return jsonify({
            'success': False,
            'error': '画像のアップロードに失敗しました。'
        }), 500

@admin_bp.route('/images', methods=['GET'])
@admin_required
def list_images():
    """アップロード済み画像一覧API"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '').strip()
        
        # 基本クエリ
        query = UploadedImage.query.filter_by(is_active=True)
        
        # 検索フィルター
        if search:
            search_filter = f'%{search}%'
            query = query.filter(
                db.or_(
                    UploadedImage.original_filename.ilike(search_filter),
                    UploadedImage.alt_text.ilike(search_filter),
                    UploadedImage.caption.ilike(search_filter),
                    UploadedImage.description.ilike(search_filter)
                )
            )
        
        # ページネーション
        pagination = query.order_by(UploadedImage.upload_date.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        images = []
        for img in pagination.items:
            images.append({
                'id': img.id,
                'filename': img.filename,
                'original_filename': img.original_filename,
                'url': img.file_url,
                'alt_text': img.alt_text,
                'caption': img.caption,
                'width': img.width,
                'height': img.height,
                'file_size': img.file_size_mb,
                'upload_date': img.upload_date.strftime('%Y-%m-%d %H:%M:%S'),
                'usage_count': img.usage_count,
                'markdown': img.markdown_syntax
            })
        
        return jsonify({
            'success': True,
            'images': images,
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_prev': pagination.has_prev,
                'has_next': pagination.has_next
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"List images API error: {e}")
        return jsonify({
            'success': False,
            'error': '画像一覧の取得に失敗しました。'
        }), 500

@admin_bp.route('/images/<int:image_id>', methods=['PUT'])
@admin_required
def update_image(image_id):
    """画像情報更新API"""
    try:
        image = UploadedImage.query.get_or_404(image_id)
        
        # フォームデータから取得
        alt_text = request.form.get('alt_text', '').strip()
        caption = request.form.get('caption', '').strip()
        description = request.form.get('description', '').strip()
        
        # バリデーション
        if not alt_text:
            return jsonify({
                'success': False,
                'error': 'Alt属性は必須です。'
            }), 400
        
        # 更新
        image.alt_text = alt_text
        image.caption = caption if caption else None
        image.description = description if description else None
        image.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '画像情報を更新しました。',
            'image': {
                'id': image.id,
                'alt_text': image.alt_text,
                'caption': image.caption,
                'description': image.description,
                'markdown': image.markdown_syntax
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Update image API error: {e}")
        return jsonify({
            'success': False,
            'error': '画像情報の更新に失敗しました。'
        }), 500

@admin_bp.route('/images/<int:image_id>', methods=['DELETE'])
@admin_required
def delete_image(image_id):
    """画像削除API"""
    try:
        image = UploadedImage.query.get_or_404(image_id)
        
        # ファイル削除
        file_path = os.path.join(current_app.static_folder, image.file_path)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # データベースから削除（論理削除）
        image.is_active = False
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '画像を削除しました。'
        })
        
    except Exception as e:
        current_app.logger.error(f"Delete image API error: {e}")
        return jsonify({
            'success': False,
            'error': '画像の削除に失敗しました。'
        }), 500

@admin_bp.route('/images_manager/')
@admin_required
def images_manager():
    """画像管理ページ"""
    try:
        page = request.args.get('page', 1, type=int)
        search = request.args.get('search', '').strip()
        per_page = 12  # グリッド表示のため12個ずつ
        
        # 基本クエリ
        query = UploadedImage.query.filter_by(is_active=True)
        
        # 検索フィルター
        if search:
            search_filter = f'%{search}%'
            query = query.filter(
                db.or_(
                    UploadedImage.original_filename.ilike(search_filter),
                    UploadedImage.alt_text.ilike(search_filter),
                    UploadedImage.caption.ilike(search_filter),
                    UploadedImage.description.ilike(search_filter)
                )
            )
        
        # ページネーション
        images_pagination = query.order_by(UploadedImage.upload_date.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # 統計情報
        total_images = UploadedImage.query.filter_by(is_active=True).count()
        total_size = db.session.query(func.sum(UploadedImage.file_size)).filter_by(is_active=True).scalar() or 0
        
        stats = {
            'total_images': total_images,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'search_results': len(images_pagination.items) if search else None
        }
        
        return render_template('admin/images.html',
                             images=images_pagination,
                             search=search,
                             stats=stats)
                             
    except Exception as e:
        current_app.logger.error(f"Images manager error: {e}")
        flash('画像管理ページの読み込みに失敗しました。', 'danger')
        return redirect(url_for('admin.dashboard'))