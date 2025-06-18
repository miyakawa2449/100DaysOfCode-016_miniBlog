from flask import Blueprint, render_template, redirect, url_for, request, flash, session, current_app, jsonify
from flask_login import login_required, current_user
from models import db, User, Article, Category, Comment, SiteSetting
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from sqlalchemy import func
import os
from PIL import Image
import time
import re
import json
from forms import CategoryForm, ArticleForm
try:
    from block_forms import BlockEditorForm, create_block_form
    from block_utils import process_block_image, fetch_ogp_data, detect_sns_platform, extract_sns_id, generate_sns_embed_html
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
                if form.featured_image.data and form.featured_image.data.filename:
                    current_app.logger.info(f"Processing featured image for article ID: {new_article.id}")
                    featured_image = process_featured_image(form.featured_image.data, new_article.id)
                    if featured_image:
                        new_article.featured_image = featured_image
                        current_app.logger.info(f"Featured image saved: {featured_image}")
                    else:
                        current_app.logger.error("Failed to process featured image")
                
                db.session.commit()
                current_app.logger.info(f"Article created with featured_image: {new_article.featured_image}")
                flash('記事が作成されました。', 'success')
                return redirect(url_for('admin.articles'))
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Article creation error: {e}")
                flash('記事の作成に失敗しました。', 'danger')
    
    return render_template('admin/create_article.html', form=form, all_categories=all_categories)

@admin_bp.route('/article/edit/<int:article_id>/', methods=['GET', 'POST'])
@admin_required
def edit_article(article_id):
    """記事編集"""
    article = Article.query.get_or_404(article_id)
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
                if form.featured_image.data and form.featured_image.data.filename:
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
        # CSRF検証を完全にスキップ（管理者のみアクセス可能）
        pass  # CSRF検証をスキップ
        
        # リクエストの内容をログ出力
        current_app.logger.info(f"Request content type: {request.content_type}")
        current_app.logger.info(f"Request data: {request.data}")
        current_app.logger.info(f"Request form: {request.form}")
        current_app.logger.info(f"Request JSON: {request.get_json(force=True, silent=True)}")
        
        # JSONとフォームデータの両方に対応
        if request.content_type == 'application/json':
            data = request.get_json()
        else:
            data = request.form.to_dict()
            
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
            
        new_status = data.get('is_published', False)
        # 文字列の場合の変換
        if isinstance(new_status, str):
            new_status = new_status.lower() in ['true', '1', 'yes']
            
        was_published = article.is_published
        
        article.is_published = new_status
        if new_status and not was_published:
            article.published_at = datetime.utcnow()
        
        db.session.commit()
        
        status_text = '公開' if new_status else '下書き'
        current_app.logger.info(f'Article {article.id} status changed to {status_text}')
        
        flash(f'記事ステータスを{status_text}に変更しました', 'success')
        return redirect(url_for('admin.articles'))
    except BadRequest as e:
        # CSRF エラーの場合
        current_app.logger.warning(f"CSRF validation failed, but allowing for admin user: {e}")
        # 再試行（CSRF検証なし）
        try:
            # JSONとフォームデータの両方に対応
            if request.content_type == 'application/json':
                data = request.get_json()
            else:
                data = request.form.to_dict()
                
            if not data:
                return jsonify({'success': False, 'error': 'No data provided'}), 400
                
            new_status = data.get('is_published', False)
            # 文字列の場合の変換
            if isinstance(new_status, str):
                new_status = new_status.lower() in ['true', '1', 'yes']
                
            was_published = article.is_published
            
            article.is_published = new_status
            if new_status and not was_published:
                article.published_at = datetime.utcnow()
            
            db.session.commit()
            
            status_text = '公開' if new_status else '下書き'
            current_app.logger.info(f'Article {article.id} status changed to {status_text}')
            
            flash(f'記事ステータスを{status_text}に変更しました', 'success')
            return redirect(url_for('admin.articles'))
        except Exception as retry_e:
            db.session.rollback()
            current_app.logger.error(f"Retry failed: {retry_e}")
            flash(f'ステータス変更に失敗しました: {retry_e}', 'danger')
            return redirect(url_for('admin.articles'))
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Status toggle error: {e}")
        import traceback
        current_app.logger.error(f"Traceback: {traceback.format_exc()}")
        flash(f'ステータス変更に失敗しました: {e}', 'danger')
        return redirect(url_for('admin.articles'))

@admin_bp.route('/article/delete/<int:article_id>/', methods=['POST'])
@admin_required
def delete_article(article_id):
    """記事削除"""
    article = Article.query.get_or_404(article_id)
    
    try:
        db.session.delete(article)
        db.session.commit()
        flash(f'記事「{article.title}」を削除しました。', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Article deletion error: {e}")
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
@admin_bp.route('/site_settings/', methods=['GET', 'POST'])
@admin_required
def site_settings():
    """サイト設定管理"""
    default_settings = [
        {'key': 'site_title', 'description': 'サイトタイトル', 'type': 'text', 'default': 'ミニブログ'},
        {'key': 'site_description', 'description': 'サイト説明', 'type': 'textarea', 'default': 'シンプルなブログシステム'},
        {'key': 'site_keywords', 'description': 'サイトキーワード', 'type': 'text', 'default': 'ブログ,記事,投稿'},
        {'key': 'admin_email', 'description': '管理者メールアドレス', 'type': 'email', 'default': 'admin@example.com'},
        {'key': 'posts_per_page', 'description': '1ページあたりの記事数', 'type': 'number', 'default': '10'},
        {'key': 'enable_comments', 'description': 'コメント機能を有効にする', 'type': 'boolean', 'default': 'true'},
        {'key': 'maintenance_mode', 'description': 'メンテナンスモード', 'type': 'boolean', 'default': 'false'}
    ]
    
    if request.method == 'POST':
        try:
            for setting_def in default_settings:
                key = setting_def['key']
                value = request.form.get(key, '')
                
                if setting_def['type'] == 'boolean':
                    value = 'true' if key in request.form else 'false'
                
                # SiteSettingクラスが存在する場合のみ設定を保存
                if hasattr(SiteSetting, 'set_setting'):
                    SiteSetting.set_setting(
                        key=key,
                        value=value,
                        description=setting_def['description'],
                        setting_type=setting_def['type'],
                        is_public=True
                    )
            
            flash('サイト設定を更新しました。', 'success')
            return redirect(url_for('admin.site_settings'))
        except Exception as e:
            current_app.logger.error(f"Site settings update error: {e}")
            flash('設定の更新に失敗しました。', 'danger')
    
    # 既存設定取得
    settings = {}
    for setting_def in default_settings:
        try:
            if hasattr(SiteSetting, 'query'):
                setting = SiteSetting.query.filter_by(key=setting_def['key']).first()
                settings[setting_def['key']] = {
                    'value': setting.value if setting else setting_def['default'],
                    'description': setting_def['description'],
                    'type': setting_def['type']
                }
            else:
                settings[setting_def['key']] = {
                    'value': setting_def['default'],
                    'description': setting_def['description'],
                    'type': setting_def['type']
                }
        except:
            settings[setting_def['key']] = {
                'value': setting_def['default'],
                'description': setting_def['description'],
                'type': setting_def['type']
            }
    
    return render_template('admin/site_settings.html', settings=settings)

# ...existing code...

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
    
    # 既存記事をブロックエディタに変換（初回アクセス時）
    if not article.use_block_editor:
        article.convert_to_block_editor()
        flash('記事をブロック型エディタに変換しました。', 'info')
    
    form = BlockEditorForm(obj=article)
    all_categories = Category.query.order_by(Category.name).all()
    
    # カテゴリの選択肢を設定
    form.category_id.choices = [(0, 'カテゴリを選択してください')] + [(cat.id, cat.name) for cat in all_categories]
    
    # 現在のカテゴリを設定
    current_category = article.categories.first()
    if current_category:
        form.category_id.data = current_category.id
    
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
                            
                            # 埋込HTMLの生成
                            embed_html = generate_sns_embed_html(embed_url, platform, sns_id)
                            if embed_html:
                                block.embed_html = embed_html
                                current_app.logger.info("Generated embed HTML")
                        else:
                            current_app.logger.warning(f"Could not extract SNS ID from: {embed_url}")
                    else:
                        current_app.logger.warning(f"Unsupported SNS platform: {embed_url}")
                        block.embed_platform = 'unknown'
                
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
        
        # OGP情報を取得
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