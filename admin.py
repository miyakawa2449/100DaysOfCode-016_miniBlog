from flask import Blueprint, render_template, redirect, url_for, request, flash, session, current_app
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
from forms import CategoryForm, ArticleForm

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
    
    # 今月の統計も簡単に
    monthly_stats = {
        'articles_this_month': 0,
        'users_this_month': 0,
        'comments_this_month': 0
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
            # データ更新
            user.name = request.form.get('name', user.name)
            user.handle_name = request.form.get('handle_name', user.handle_name or '')
            user.role = request.form.get('role', user.role)
            user.introduction = request.form.get('introduction', user.introduction or '')
            
            # パスワード変更
            new_password = request.form.get('new_password')
            if new_password:
                user.password_hash = generate_password_hash(new_password)
            
            # 通知設定（フィールドが存在する場合のみ）
            if hasattr(user, 'notify_on_publish'):
                user.notify_on_publish = 'notify_on_publish' in request.form
            if hasattr(user, 'notify_on_comment'):
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
    published_articles = 0  # 仮の値
    draft_articles = total_articles  # 仮の値（全て下書きとして扱う）
    this_month_articles = total_articles  # 仮の値
    
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
    
    if form.validate_on_submit():
        # スラッグ重複チェック
        if Article.query.filter_by(slug=form.slug.data).first():
            flash('そのスラッグは既に使用されています。', 'danger')
        else:
            try:
                new_article = Article(
                    title=form.title.data,
                    slug=form.slug.data,
                    body=form.body.data,
                    author_id=current_user.id,
                    created_at=datetime.utcnow()
                )
                
                # カテゴリ関連付け
                category_ids = request.form.getlist('categories')
                for cat_id in category_ids:
                    category = Category.query.get(cat_id)
                    if category:
                        new_article.categories.append(category)
                
                db.session.add(new_article)
                db.session.commit()
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
    
    if request.method == 'POST':
        title = request.form.get('title')
        slug = request.form.get('slug')
        body = request.form.get('body')
        
        if not title or not slug:
            flash('タイトルとスラッグは必須です。', 'danger')
        else:
            # スラッグ重複チェック（自分以外）
            existing = Article.query.filter(Article.id != article_id, Article.slug == slug).first()
            if existing:
                flash('そのスラッグは既に使用されています。', 'danger')
            else:
                try:
                    article.title = title
                    article.slug = slug
                    article.body = body
                    
                    # カテゴリ更新
                    article.categories = []
                    category_ids = request.form.getlist('categories')
                    for cat_id in category_ids:
                        category = Category.query.get(cat_id)
                        if category:
                            article.categories.append(category)
                    
                    db.session.commit()
                    flash('記事が更新されました。', 'success')
                    return redirect(url_for('admin.articles'))
                except Exception as e:
                    db.session.rollback()
                    current_app.logger.error(f"Article update error: {e}")
                    flash('記事の更新に失敗しました。', 'danger')
    
    all_categories = Category.query.order_by(Category.name).all()
    article_category_ids = [cat.id for cat in article.categories]
    return render_template('admin/edit_article.html', 
                         article=article, 
                         all_categories=all_categories, 
                         article_category_ids=article_category_ids)

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