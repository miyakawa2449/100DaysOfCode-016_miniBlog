from flask import Blueprint, render_template, redirect, url_for, request, flash, session, current_app
from flask_login import login_required, current_user
from models import db, User, Article, Category, Comment, SiteSetting  # すべてのモデルをインポート
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from sqlalchemy import func
import os
from PIL import Image
import time
from forms import CategoryForm, ArticleForm # CategoryFormとArticleFormをインポート

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# 管理者認証デコレータ
def admin_required(f):
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
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

# ダッシュボード
@admin_bp.route('/')
@admin_required
def dashboard():
    # 基本統計
    user_count = User.query.count()
    article_count = Article.query.count()
    category_count = Category.query.count()
    
    # コメント数（テーブルが存在しない可能性を考慮）
    try:
        comment_count = Comment.query.count()
    except:
        comment_count = 0
    
    # 今月の統計
    today = datetime.now()
    month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    articles_this_month = Article.query.filter(Article.created_at >= month_start).count()
    users_this_month = User.query.filter(User.created_at >= month_start).count()
    
    # コメント関連統計（テーブルが存在しない可能性を考慮）
    try:
        comments_this_month = Comment.query.filter(Comment.created_at >= month_start).count()
        pending_comments = Comment.query.filter(Comment.is_approved == False).count()
        recent_comments = Comment.query.order_by(Comment.created_at.desc()).limit(5).all()
        popular_articles = db.session.query(Article)\
            .outerjoin(Comment)\
            .group_by(Article.id)\
            .order_by(func.count(Comment.id).desc())\
            .limit(5).all()
    except:
        comments_this_month = 0
        pending_comments = 0
        recent_comments = []
        popular_articles = Article.query.order_by(Article.created_at.desc()).limit(5).all()
    
    # 最近の投稿5件を取得
    recent_articles = Article.query.order_by(Article.created_at.desc()).limit(5).all()
    
    # 月別記事投稿数（過去6ヶ月）
    monthly_stats = []
    for i in range(6):
        month_date = today - timedelta(days=30*i)
        month_start = month_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if i == 0:
            month_end = today
        else:
            next_month = month_start + timedelta(days=32)
            month_end = next_month.replace(day=1) - timedelta(seconds=1)
        
        month_articles = Article.query.filter(
            Article.created_at >= month_start,
            Article.created_at <= month_end
        ).count()
        
        monthly_stats.append({
            'month': month_start.strftime('%Y-%m'),
            'articles': month_articles
        })
    
    monthly_stats.reverse()  # 古い順に並べ替え
    
    return render_template('admin/dashboard.html', 
                        user_count=user_count, 
                        article_count=article_count,
                        category_count=category_count,
                        comment_count=comment_count,
                        articles_this_month=articles_this_month,
                        comments_this_month=comments_this_month,
                        users_this_month=users_this_month,
                        pending_comments=pending_comments,
                        recent_articles=recent_articles,
                        recent_comments=recent_comments,
                        popular_articles=popular_articles,
                        monthly_stats=monthly_stats)

# ユーザ管理
@admin_bp.route('/users/')
@admin_required
def users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

# ユーザ編集
@admin_bp.route('/user/edit/<int:user_id>/', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        # 自分自身の管理者権限を削除しようとしていないかチェック
        if user.id == current_user.id and request.form.get('role') != 'admin':
            flash('自分自身の管理者権限は削除できません。', 'danger')
            return render_template('admin/edit_user.html', user=user)
        
        user.name = request.form.get('name', user.name)
        user.handle_name = request.form.get('handle_name', user.handle_name)
        user.role = request.form.get('role', user.role)
        user.introduction = request.form.get('introduction', user.introduction)
        user.birthplace = request.form.get('birthplace', user.birthplace)
        
        # パスワード変更がある場合
        new_password = request.form.get('new_password')
        if new_password:
            user.password_hash = generate_password_hash(new_password)
        
        # 通知設定
        user.notify_on_publish = 'notify_on_publish' in request.form
        user.notify_on_comment = 'notify_on_comment' in request.form
        
        try:
            db.session.commit()
            flash('ユーザー情報を更新しました。', 'success')
            return redirect(url_for('admin.users'))
        except Exception as e:
            db.session.rollback()
            flash('ユーザー情報の更新に失敗しました。', 'danger')
    
    return render_template('admin/edit_user.html', user=user)

# ユーザー削除
@admin_bp.route('/user/delete/<int:user_id>/', methods=['POST'])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # 自分自身を削除しようとしていないかチェック
    if user.id == current_user.id:
        flash('自分自身を削除することはできません。', 'danger')
        return redirect(url_for('admin.users'))
    
    # 最後の管理者を削除しようとしていないかチェック
    admin_count = User.query.filter_by(role='admin').count()
    if user.role == 'admin' and admin_count <= 1:
        flash('最後の管理者を削除することはできません。', 'danger')
        return redirect(url_for('admin.users'))
    
    # ユーザーに関連する記事の処理
    user_articles = Article.query.filter_by(author_id=user.id).all()
    if user_articles:
        action = request.form.get('article_action', 'keep')
        if action == 'delete':
            # 記事も削除
            for article in user_articles:
                db.session.delete(article)
        elif action == 'transfer':
            # 他のユーザーに移管
            transfer_to_id = request.form.get('transfer_to_user')
            if transfer_to_id:
                for article in user_articles:
                    article.author_id = int(transfer_to_id)
        # action == 'keep' の場合は何もしない（孤立した記事になる）
    
    try:
        db.session.delete(user)
        db.session.commit()
        flash(f'ユーザー「{user.name}」を削除しました。', 'success')
    except Exception as e:
        db.session.rollback()
        flash('ユーザーの削除に失敗しました。', 'danger')
    
    return redirect(url_for('admin.users'))

# ユーザー作成
@admin_bp.route('/user/create/', methods=['GET', 'POST'])
@admin_required
def create_user():
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        password = request.form.get('password')
        role = request.form.get('role', 'author')
        
        # バリデーション
        if not email or not name or not password:
            flash('必須項目を入力してください。', 'danger')
            return render_template('admin/create_user.html')
        
        # 重複チェック
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('このメールアドレスは既に使用されています。', 'danger')
            return render_template('admin/create_user.html')
        
        # パスワード強度チェック（簡易版）
        if len(password) < 8:
            flash('パスワードは8文字以上である必要があります。', 'danger')
            return render_template('admin/create_user.html')
        
        try:
            new_user = User(
                email=email,
                name=name,
                password_hash=generate_password_hash(password),
                role=role,
                handle_name=request.form.get('handle_name', ''),
                introduction=request.form.get('introduction', '')
            )
            db.session.add(new_user)
            db.session.commit()
            flash(f'ユーザー「{name}」を作成しました。', 'success')
            return redirect(url_for('admin.users'))
        except Exception as e:
            db.session.rollback()
            flash('ユーザーの作成に失敗しました。', 'danger')
    
    return render_template('admin/create_user.html')

# 記事管理
@admin_bp.route('/articles/')
@admin_required
def articles():
    page = request.args.get('page', 1, type=int)
    # 記事を作成日時の降順で取得し、ページネーションを適用
    articles_pagination = Article.query.order_by(Article.created_at.desc()).paginate(page=page, per_page=10) # 1ページあたり10件表示
    # テンプレートには paginate オブジェクトを渡す (テンプレート側で .items でリストにアクセス)
    return render_template('admin/articles.html', articles_list=articles_pagination)

# 記事作成
@admin_bp.route('/article/create/', methods=['GET', 'POST'])
@admin_required
def create_article():
    form = ArticleForm()
    all_categories = Category.query.order_by(Category.name).all()
    
    if form.validate_on_submit():
        title = form.title.data
        slug = form.slug.data
        body = form.body.data
        author_id = session.get('user_id')
        category_ids = request.form.getlist('categories')  # カテゴリは別途取得

        # スラッグの重複チェック
        existing_article = Article.query.filter_by(slug=slug).first()
        if existing_article:
            flash('そのスラッグは既に使用されています。', 'danger')
        else:
            # HTMLサニタイゼーションを適用
            from app import sanitize_html
            sanitized_body = sanitize_html(body) if body else ""
            new_article = Article(title=title, slug=slug, body=sanitized_body, author_id=author_id)
            
            # 選択されたカテゴリを記事に関連付ける
            if category_ids:
                for cat_id in category_ids:
                    category = Category.query.get(cat_id)
                    if category:
                        new_article.categories.append(category)
            
            db.session.add(new_article)
            db.session.commit()
            flash('記事が作成されました。', 'success')
            return redirect(url_for('admin.articles'))
    
    return render_template('admin/create_article.html', form=form, all_categories=all_categories)

# 記事編集
@admin_bp.route('/article/edit/<int:article_id>/', methods=['GET', 'POST'])
@admin_required
def edit_article(article_id):
    article = Article.query.get_or_404(article_id)
    if request.method == 'POST':
        title = request.form.get('title')
        slug = request.form.get('slug')
        body = request.form.get('body')
        category_ids = request.form.getlist('categories')

        if not title or not slug:
            flash('タイトルとスラッグは必須です。', 'danger')
        else:
            # スラッグの重複チェック (自分自身を除く)
            existing_article = Article.query.filter(Article.id != article_id, Article.slug == slug).first()
            if existing_article:
                flash('そのスラッグは既に使用されています。', 'danger')
            else:
                article.title = title
                article.slug = slug
                article.body = body
                
                # カテゴリの関連付けを更新
                article.categories = [] # 一旦クリア
                if category_ids:
                    for cat_id in category_ids:
                        category = Category.query.get(cat_id)
                        if category:
                            article.categories.append(category)
                            
                db.session.commit()
                flash('記事が更新されました。', 'success')
                return redirect(url_for('admin.articles'))

    all_categories = Category.query.order_by(Category.name).all()
    # 記事が既に持っているカテゴリIDのリストを作成 (テンプレートでの選択状態復元用)
    article_category_ids = [cat.id for cat in article.categories]
    return render_template('admin/edit_article.html', article=article, all_categories=all_categories, article_category_ids=article_category_ids)

# 記事削除
@admin_bp.route('/article/delete/<int:article_id>/', methods=['POST'])
@admin_required
def delete_article(article_id):
    article = Article.query.get_or_404(article_id)
    
    try:
        # 関連するコメントも削除
        comments = Comment.query.filter_by(article_id=article_id).all()
        for comment in comments:
            db.session.delete(comment)
        
        # 記事を削除
        db.session.delete(article)
        db.session.commit()
        flash(f'記事「{article.title}」を削除しました。', 'success')
    except Exception as e:
        db.session.rollback()
        flash('記事の削除に失敗しました。', 'danger')
    
    return redirect(url_for('admin.articles'))

# 記事の公開状態変更
@admin_bp.route('/article/toggle_publish/<int:article_id>/', methods=['POST'])
@admin_required
def toggle_article_publish(article_id):
    article = Article.query.get_or_404(article_id)
    
    try:
        # is_publishedフィールドがない場合は、published_atで判断
        if hasattr(article, 'is_published'):
            article.is_published = not article.is_published
        elif hasattr(article, 'published_at'):
            if article.published_at:
                article.published_at = None
                status = '下書きに戻しました'
            else:
                article.published_at = datetime.utcnow()
                status = '公開しました'
        else:
            flash('公開状態の変更機能が利用できません。', 'warning')
            return redirect(url_for('admin.articles'))
        
        db.session.commit()
        flash(f'記事「{article.title}」を{status}。', 'success')
    except Exception as e:
        db.session.rollback()
        flash('公開状態の変更に失敗しました。', 'danger')
    
    return redirect(url_for('admin.articles'))

# 記事の一括操作
@admin_bp.route('/article/bulk_action/', methods=['POST'])
@admin_required
def bulk_article_action():
    action = request.form.get('action')
    article_ids = request.form.getlist('article_ids')
    
    if not article_ids:
        flash('記事が選択されていません。', 'warning')
        return redirect(url_for('admin.articles'))
    
    articles = Article.query.filter(Article.id.in_(article_ids)).all()
    
    try:
        if action == 'publish':
            for article in articles:
                if hasattr(article, 'is_published'):
                    article.is_published = True
                elif hasattr(article, 'published_at'):
                    article.published_at = datetime.utcnow()
            flash(f'{len(articles)}件の記事を公開しました。', 'success')
        elif action == 'unpublish':
            for article in articles:
                if hasattr(article, 'is_published'):
                    article.is_published = False
                elif hasattr(article, 'published_at'):
                    article.published_at = None
            flash(f'{len(articles)}件の記事を下書きに戻しました。', 'info')
        elif action == 'delete':
            for article in articles:
                # 関連するコメントも削除
                comments = Comment.query.filter_by(article_id=article.id).all()
                for comment in comments:
                    db.session.delete(comment)
                db.session.delete(article)
            flash(f'{len(articles)}件の記事を削除しました。', 'success')
        
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash('一括操作に失敗しました。', 'danger')
    
    return redirect(url_for('admin.articles'))

# カテゴリ管理
@admin_bp.route('/categories/')
@admin_required
def categories():
    page = request.args.get('page', 1, type=int)
    categories_list = Category.query.order_by(Category.name).paginate(page=page, per_page=10)
    return render_template('admin/categories.html', categories_list=categories_list)

@admin_bp.route('/category/create/', methods=['GET', 'POST'])
@admin_required
def create_category():
    form = CategoryForm()
    print(f"--- Request method: {request.method} ---")

    if request.method == 'POST':
        print("--- POST request received ---")
        print(f"--- form.ogp_image_file.data: {form.ogp_image_file.data} ---")
        print(f"--- form.ogp_crop_x.data: {form.ogp_crop_x.data} ---")

        if form.validate_on_submit():
            print("--- Form IS valid ---")
            ogp_image_file = form.ogp_image_file.data

            ogp_image_path = None
            if ogp_image_file:
                current_app.logger.debug(f"New OGP image file provided: {ogp_image_file.filename}")
                try:
                    timestamp = int(time.time())
                    file_ext = os.path.splitext(secure_filename(ogp_image_file.filename))[1]
                    new_ogp_filename = f"category_ogp_new_{timestamp}{file_ext}"
                    current_app.logger.debug(f"Generated new OGP filename: {new_ogp_filename}")
                    
                    upload_folder = current_app.config['CATEGORY_OGP_UPLOAD_FOLDER']
                    current_app.logger.debug(f"Upload folder from config: {upload_folder}")

                    if not os.path.exists(upload_folder):
                        os.makedirs(upload_folder)
                        current_app.logger.info(f"Created upload folder: {upload_folder}")
                    ogp_image_save_path = os.path.join(upload_folder, new_ogp_filename)
                    current_app.logger.debug(f"OGP image save path: {ogp_image_save_path}")

                    temp_image_path = os.path.join(upload_folder, f"temp_{new_ogp_filename}")
                    ogp_image_file.save(temp_image_path)

                    img = Image.open(temp_image_path)

                    try:
                        crop_x_str = form.ogp_crop_x.data
                        crop_y_str = form.ogp_crop_y.data
                        crop_width_str = form.ogp_crop_width.data
                        crop_height_str = form.ogp_crop_height.data
                        current_app.logger.debug(f"Crop data strings from form: x='{crop_x_str}', y='{crop_y_str}', width='{crop_width_str}', height='{crop_height_str}'")

                        crop_x = int(crop_x_str) if crop_x_str else None
                        crop_y = int(crop_y_str) if crop_y_str else None
                        crop_width = int(crop_width_str) if crop_width_str else None
                        crop_height = int(crop_height_str) if crop_height_str else None

                    except (ValueError, TypeError) as e:
                        current_app.logger.warning(f"Could not convert crop data to int: {e}. Setting to None.")
                        crop_x, crop_y, crop_width, crop_height = None, None, None, None

                    current_app.logger.debug(f"Converted crop data: x={type(crop_x).__name__}:{crop_x}, y={type(crop_y).__name__}:{crop_y}, width={type(crop_width).__name__}:{crop_width}, height={type(crop_height).__name__}:{crop_height}")

                    if crop_x is not None and crop_y is not None and \
                        crop_width is not None and crop_height is not None and \
                        crop_width > 0 and crop_height > 0:
                        current_app.logger.debug("Applying crop to image.")
                        cropped_img = img.crop((crop_x, crop_y, crop_x + crop_width, crop_y + crop_height))
                        
                        # クロップした画像をリサイズ
                        resized_img = cropped_img.resize((1200, 630), Image.LANCZOS)
                        resized_img.save(ogp_image_save_path, format='JPEG', quality=85)
                        current_app.logger.info(f"Cropped and resized OGP image saved to: {ogp_image_save_path}")
                    else:
                        current_app.logger.debug("No valid crop data provided. Saving original image with resize.")
                        # 元の画像をリサイズのみ
                        resized_img = img.resize((1200, 630), Image.LANCZOS)
                        resized_img.save(ogp_image_save_path, format='JPEG', quality=85)
                        current_app.logger.info(f"Resized OGP image saved to: {ogp_image_save_path}")

                    # 一時ファイルを削除
                    if os.path.exists(temp_image_path):
                        os.remove(temp_image_path)
                        current_app.logger.debug(f"Temporary file deleted: {temp_image_path}")

                    # 相対パスをDBに保存（static/uploads/category_ogp/ からの相対パス）
                    ogp_image_path = os.path.relpath(ogp_image_save_path, current_app.static_folder)
                    current_app.logger.info(f"OGP image relative path for DB: {ogp_image_path}")

                except Exception as e:
                    current_app.logger.error(f"Error processing OGP image: {e}")
                    flash('OGP画像の処理中にエラーが発生しました。', 'danger')
                    return render_template('admin/create_category.html', form=form)

            # スラッグが空の場合は名前から自動生成
            slug = form.slug.data
            if not slug:
                import re
                slug = re.sub(r'[^\w\s-]', '', form.name.data.lower())
                slug = re.sub(r'[\s_-]+', '-', slug)
                slug = slug.strip('-')

            if not slug:
                flash('有効なスラッグを生成できませんでした。スラッグを手動で入力してください。', 'danger')
                return render_template('admin/create_category.html', form=form)

            # 重複チェック
            existing_category_slug = Category.query.filter_by(slug=slug).first()
            existing_category_name = Category.query.filter_by(name=form.name.data).first()
            if existing_category_slug:
                flash('そのスラッグは既に使用されています。', 'danger')
                return render_template('admin/create_category.html', form=form)
            elif existing_category_name:
                flash('そのカテゴリ名は既に使用されています。', 'danger')
                return render_template('admin/create_category.html', form=form)

            # 新しいカテゴリを作成
            new_category = Category(
                name=form.name.data,
                slug=slug,
                description=form.description.data,
                parent_id=form.parent_id.data if form.parent_id.data else None,
                ogp_image=ogp_image_path,
                meta_keywords=form.meta_keywords.data,
                canonical_url=form.canonical_url.data,
                json_ld=form.json_ld.data,
                ext_json=form.ext_json.data
            )
            
            db.session.add(new_category)
            db.session.commit()
            flash('カテゴリが作成されました。', 'success')
            return redirect(url_for('admin.categories'))
        else:
            print("--- Form validation failed ---")
            print(f"--- Form errors: {form.errors} ---")

    return render_template('admin/create_category.html', form=form)

@admin_bp.route('/category/edit/<int:category_id>/', methods=['GET', 'POST'])
@admin_required
def edit_category(category_id):
    category = Category.query.get_or_404(category_id)
    form = CategoryForm(obj=category)
    print(f"--- Request method: {request.method} ---")
    print(f"--- Initial category.ogp_image: {category.ogp_image} ---")

    if request.method == 'POST': # validate_on_submit の前にPOSTかどうか確認
        print("--- POST request received ---")
        print(f"--- form.ogp_image_file.data: {form.ogp_image_file.data} ---")
        print(f"--- form.ogp_crop_x.data: {form.ogp_crop_x.data} ---")
        # 他のトリミングデータも同様にprint

        if form.validate_on_submit():
            print("--- Form IS valid ---")
            ogp_image_file = form.ogp_image_file.data
            old_ogp_image_path = category.ogp_image # 更新前のOGP画像パスを保持

            if ogp_image_file:
                current_app.logger.debug(f"New OGP image file provided: {ogp_image_file.filename}")
                try:
                    timestamp = int(time.time())
                    file_ext = os.path.splitext(secure_filename(ogp_image_file.filename))[1]
                    new_ogp_filename = f"category_ogp_{category.id}_{timestamp}{file_ext}"
                    current_app.logger.debug(f"Generated new OGP filename: {new_ogp_filename}")
                    
                    upload_folder = current_app.config['CATEGORY_OGP_UPLOAD_FOLDER'] # ★★★ 修正後 ★★★
                    current_app.logger.debug(f"Upload folder from config: {upload_folder}")


                    if not os.path.exists(upload_folder):
                        os.makedirs(upload_folder)
                        current_app.logger.info(f"Created upload folder: {upload_folder}")
                    ogp_image_save_path = os.path.join(upload_folder, new_ogp_filename)
                    current_app.logger.debug(f"OGP image save path: {ogp_image_save_path}")

                    temp_image_path = os.path.join(upload_folder, f"temp_{new_ogp_filename}")
                    ogp_image_file.save(temp_image_path)

                    img = Image.open(temp_image_path)

                    try:
                        crop_x_str = form.ogp_crop_x.data
                        crop_y_str = form.ogp_crop_y.data
                        crop_width_str = form.ogp_crop_width.data
                        crop_height_str = form.ogp_crop_height.data
                        current_app.logger.debug(f"Crop data strings from form: x='{crop_x_str}', y='{crop_y_str}', width='{crop_width_str}', height='{crop_height_str}'")

                        # 文字列から整数への変換を試みる
                        crop_x = int(crop_x_str) if crop_x_str else None
                        crop_y = int(crop_y_str) if crop_y_str else None
                        crop_width = int(crop_width_str) if crop_width_str else None
                        crop_height = int(crop_height_str) if crop_height_str else None

                    except (ValueError, TypeError) as e:
                        current_app.logger.warning(f"Could not convert crop data to int: {e}. Setting to None.")
                        crop_x, crop_y, crop_width, crop_height = None, None, None, None

                    current_app.logger.debug(f"Converted crop data: x={type(crop_x).__name__}:{crop_x}, y={type(crop_y).__name__}:{crop_y}, width={type(crop_width).__name__}:{crop_width}, height={type(crop_height).__name__}:{crop_height}")

                    if crop_x is not None and crop_y is not None and \
                        crop_width is not None and crop_height is not None and \
                        crop_width > 0 and crop_height > 0:
                        current_app.logger.debug("Applying crop to image.")
                        # Pillow の crop メソッドは (left, upper, right, lower) のタプルを期待する
                        cropped_img = img.crop((crop_x, crop_y, crop_x + crop_width, crop_y + crop_height))
                        
                        # --- ★★★ クロップした画像をリサイズ ★★★ ---
                        target_width = 1200
                        target_height = 630
                        current_app.logger.debug(f"Resizing cropped image to {target_width}x{target_height}")
                        resized_img = cropped_img.resize((target_width, target_height), Image.Resampling.LANCZOS) # 高画質なリサイズ方法
                        # --- ★★★ ここまで追加 ★★★ ---

                        resized_img.save(ogp_image_save_path) # リサイズされた画像を保存
                        category.ogp_image = os.path.join('uploads/category_ogp', new_ogp_filename).replace("\\", "/")
                    else:
                        current_app.logger.warning(f"Crop conditions not met or data invalid after conversion. Saving original image. Crop data: x={crop_x}, y={crop_y}, w={crop_width}, h={crop_height}")
                        # トリミング条件を満たさない場合、オリジナル画像をリサイズするかどうかを検討
                        # もしオリジナル画像も特定のサイズにしたい場合は、ここでもリサイズ処理を入れる
                        # 例: target_width = 1200
                        #     target_height = 630
                        #     resized_original_img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
                        #     resized_original_img.save(ogp_image_save_path)
                        # 現状はオリジナルをそのまま保存
                        img.save(ogp_image_save_path)
                        category.ogp_image = os.path.join('uploads/category_ogp', new_ogp_filename).replace("\\", "/")

                    if os.path.exists(temp_image_path):
                        os.remove(temp_image_path)

                    if old_ogp_image_path and old_ogp_image_path != category.ogp_image:
                        try:
                            full_old_path = os.path.join(current_app.static_folder, old_ogp_image_path)
                            if os.path.exists(full_old_path):
                                os.remove(full_old_path)
                                flash(f'古いOGP画像 {old_ogp_image_path} を削除しました。', 'info')
                        except Exception as e:
                            current_app.logger.error(f"古いOGP画像の削除に失敗: {e}")
                            flash(f'古いOGP画像の削除に失敗しました: {old_ogp_image_path}', 'warning')
                
                except Exception as e:
                    current_app.logger.error(f"OGP画像のアップロードまたは処理に失敗: {e}")
                    flash('OGP画像のアップロードまたは処理中にエラーが発生しました。', 'danger')
            
            category.name = form.name.data
            category.slug = form.slug.data
            category.meta_title = form.meta_title.data
            category.meta_description = form.meta_description.data
            category.meta_keywords = form.meta_keywords.data
            category.canonical_url = form.canonical_url.data
            category.json_ld = form.json_ld.data
            category.ext_json = form.ext_json.data
            
            try:
                db.session.commit()
                flash('カテゴリが正常に更新されました。', 'success')
                return redirect(url_for('admin.categories'))
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"カテゴリ更新時のデータベースコミット失敗: {e}")
                flash('カテゴリの更新中にエラーが発生しました。', 'danger')
        else:
            print("--- Form IS NOT valid ---")
            print(f"--- Form errors: {form.errors} ---") # ★重要: バリデーションエラー内容を確認

    elif request.method == 'GET':
        form.name.data = category.name
        form.slug.data = category.slug
        form.meta_title.data = form.meta_title.data
        form.meta_description.data = form.meta_description.data
        form.meta_keywords.data = form.meta_keywords.data
        form.canonical_url.data = form.canonical_url.data
        form.json_ld.data = form.json_ld.data
        form.ext_json.data = form.ext_json.data

    print(f"--- Rendering template with category.ogp_image: {category.ogp_image} ---")
    return render_template('admin/edit_category.html', form=form, category=category)

@admin_bp.route('/category/delete/<int:category_id>/', methods=['POST']) # 安全のためPOST推奨
@admin_required
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)
    # TODO: 子カテゴリが存在する場合の処理、記事が紐づいている場合の処理を検討
    db.session.delete(category)
    db.session.commit()
    flash('カテゴリが削除されました。', 'success')
    return redirect(url_for('admin.categories'))

# コメント管理
@admin_bp.route('/comments/')
@admin_required
def comments():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    
    # ベースクエリ
    query = Comment.query
    
    # ステータスフィルター
    if status_filter == 'approved':
        query = query.filter(Comment.is_approved == True)
    elif status_filter == 'pending':
        query = query.filter(Comment.is_approved == False)
    
    # ページネーション
    comments_pagination = query.order_by(Comment.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # 統計情報
    total_comments = Comment.query.count()
    approved_comments = Comment.query.filter(Comment.is_approved == True).count()
    pending_comments = Comment.query.filter(Comment.is_approved == False).count()
    
    return render_template('admin/comments.html',
                         comments_list=comments_pagination,
                         status_filter=status_filter,
                         total_comments=total_comments,
                         approved_comments=approved_comments,
                         pending_comments=pending_comments)

@admin_bp.route('/comment/approve/<int:comment_id>/', methods=['POST'])
@admin_required
def approve_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    comment.is_approved = True
    db.session.commit()
    flash('コメントを承認しました。', 'success')
    return redirect(url_for('admin.comments'))

@admin_bp.route('/comment/unapprove/<int:comment_id>/', methods=['POST'])
@admin_required
def unapprove_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    comment.is_approved = False
    db.session.commit()
    flash('コメントの承認を取り消しました。', 'info')
    return redirect(url_for('admin.comments'))

@admin_bp.route('/comment/delete/<int:comment_id>/', methods=['POST'])
@admin_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    # 返信コメントも削除
    replies = Comment.query.filter(Comment.parent_id == comment_id).all()
    for reply in replies:
        db.session.delete(reply)
    db.session.delete(comment)
    db.session.commit()
    flash('コメントを削除しました。', 'success')
    return redirect(url_for('admin.comments'))

@admin_bp.route('/comment/bulk_action/', methods=['POST'])
@admin_required
def bulk_comment_action():
    action = request.form.get('action')
    comment_ids = request.form.getlist('comment_ids')
    
    if not comment_ids:
        flash('コメントが選択されていません。', 'warning')
        return redirect(url_for('admin.comments'))
    
    comments = Comment.query.filter(Comment.id.in_(comment_ids)).all()
    
    if action == 'approve':
        for comment in comments:
            comment.is_approved = True
        flash(f'{len(comments)}件のコメントを承認しました。', 'success')
    elif action == 'unapprove':
        for comment in comments:
            comment.is_approved = False
        flash(f'{len(comments)}件のコメントの承認を取り消しました。', 'info')
    elif action == 'delete':
        for comment in comments:
            # 返信コメントも削除
            replies = Comment.query.filter(Comment.parent_id == comment.id).all()
            for reply in replies:
                db.session.delete(reply)
            db.session.delete(comment)
        flash(f'{len(comments)}件のコメントを削除しました。', 'success')
    
    db.session.commit()
    return redirect(url_for('admin.comments'))

# サイト管理
@admin_bp.route('/site_settings/')
@admin_required
def site_settings():
    # 基本設定項目の定義
    default_settings = [
        {'key': 'site_title', 'description': 'サイトタイトル', 'type': 'text', 'default': 'ミニブログ'},
        {'key': 'site_description', 'description': 'サイト説明', 'type': 'textarea', 'default': 'シンプルなブログシステム'},
        {'key': 'site_keywords', 'description': 'サイトキーワード', 'type': 'text', 'default': 'ブログ,記事,投稿'},
        {'key': 'site_url', 'description': 'サイトURL', 'type': 'url', 'default': 'http://localhost:5000'},
        {'key': 'admin_email', 'description': '管理者メールアドレス', 'type': 'email', 'default': 'admin@example.com'},
        {'key': 'posts_per_page', 'description': '1ページあたりの記事数', 'type': 'number', 'default': '10'},
        {'key': 'enable_comments', 'description': 'コメント機能を有効にする', 'type': 'boolean', 'default': 'true'},
        {'key': 'comment_moderation', 'description': 'コメント承認制', 'type': 'boolean', 'default': 'true'},
        {'key': 'enable_registration', 'description': 'ユーザー登録を有効にする', 'type': 'boolean', 'default': 'false'},
        {'key': 'maintenance_mode', 'description': 'メンテナンスモード', 'type': 'boolean', 'default': 'false'},
        {'key': 'google_analytics_id', 'description': 'Google Analytics ID', 'type': 'text', 'default': ''},
        {'key': 'social_twitter', 'description': 'TwitterアカウントURL', 'type': 'url', 'default': ''},
        {'key': 'social_facebook', 'description': 'FacebookページURL', 'type': 'url', 'default': ''},
        {'key': 'social_instagram', 'description': 'InstagramアカウントURL', 'type': 'url', 'default': ''},
    ]
    
    # 既存設定の取得
    settings = {}
    for setting_def in default_settings:
        setting = SiteSetting.query.filter_by(key=setting_def['key']).first()
        settings[setting_def['key']] = {
            'value': setting.value if setting else setting_def['default'],
            'description': setting_def['description'],
            'type': setting_def['type']
        }
    
    if request.method == 'POST':
        # 設定の更新
        for setting_def in default_settings:
            key = setting_def['key']
            value = request.form.get(key, '')
            
            # boolean型の場合の処理
            if setting_def['type'] == 'boolean':
                value = 'true' if key in request.form else 'false'
            
            SiteSetting.set_setting(
                key=key,
                value=value,
                description=setting_def['description'],
                setting_type=setting_def['type'],
                is_public=True
            )
        
        flash('サイト設定を更新しました。', 'success')
        return redirect(url_for('admin.site_settings'))
    
    return render_template('admin/site_settings.html', settings=settings)

@admin_bp.route('/site_settings/', methods=['POST'])
@admin_required
def update_site_settings():
    return site_settings()  # POST処理は上のメソッドで処理

# Blueprint登録（app.pyの末尾で）
# app.register_blueprint(admin_bp)