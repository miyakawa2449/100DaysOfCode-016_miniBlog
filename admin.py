from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from models import db, User, Article, Category, Comment  # CategoryとCommentをインポート
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# 管理者認証デコレータ
def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        user = User.query.get(user_id) if user_id else None
        if not user or user.role != 'admin':
            flash('管理者権限が必要です')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ダッシュボード
@admin_bp.route('/')
@admin_required
def dashboard():
    user_count = User.query.count()
    article_count = Article.query.count()
    category_count = Category.query.count() # カテゴリ数を取得
    comment_count = Comment.query.count()   # コメント数を取得
    
    # 最近の投稿5件を取得
    recent_articles = Article.query.order_by(Article.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html', 
                        user_count=user_count, 
                        article_count=article_count,
                        category_count=category_count,
                        comment_count=comment_count,
                        recent_articles=recent_articles)

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
        user.name = request.form['name']
        user.handle_name = request.form['handle_name']
        user.role = request.form['role']
        db.session.commit()
        flash('ユーザ情報を更新しました')
        return redirect(url_for('admin.users'))
    return render_template('admin/edit_user.html', user=user)

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
    if request.method == 'POST':
        title = request.form.get('title')
        slug = request.form.get('slug')
        body = request.form.get('body')
        author_id = session.get('user_id')
        category_ids = request.form.getlist('categories') # 選択されたカテゴリIDのリストを取得

        if not title or not slug:
            flash('タイトルとスラッグは必須です。', 'danger')
        else:
            # スラッグの重複チェック
            existing_article = Article.query.filter_by(slug=slug).first()
            if existing_article:
                flash('そのスラッグは既に使用されています。', 'danger')
            else:
                new_article = Article(title=title, slug=slug, body=body, author_id=author_id)
                
                # 選択されたカテゴリを記事に関連付ける
                if category_ids:
                    for cat_id in category_ids:
                        category = Category.query.get(cat_id)
                        if category:
                            new_article.categories.append(category) # リレーションシップに追加
                
                db.session.add(new_article)
                db.session.commit()
                flash('記事が作成されました。', 'success')
                return redirect(url_for('admin.articles'))
    
    all_categories = Category.query.order_by(Category.name).all() # カテゴリ一覧をテンプレートに渡す
    return render_template('admin/create_article.html', all_categories=all_categories)

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
    if request.method == 'POST':
        name = request.form.get('name')
        slug = request.form.get('slug')
        description = request.form.get('description')
        parent_id = request.form.get('parent_id')
        # --- 追加フィールドの取得 ---
        ogp_image = request.form.get('ogp_image')
        meta_keywords = request.form.get('meta_keywords')
        canonical_url = request.form.get('canonical_url')
        json_ld = request.form.get('json_ld')
        ext_json = request.form.get('ext_json')
        # --- ここまで ---
        
        if not name or not slug:
            flash('カテゴリ名とスラッグは必須です。', 'danger')
        else:
            existing_category_slug = Category.query.filter_by(slug=slug).first()
            existing_category_name = Category.query.filter_by(name=name).first()
            if existing_category_slug:
                flash('そのスラッグは既に使用されています。', 'danger')
            elif existing_category_name:
                flash('そのカテゴリ名は既に使用されています。', 'danger')
            else:
                new_category = Category(
                    name=name, 
                    slug=slug, 
                    description=description,
                    parent_id=int(parent_id) if parent_id else None,
                    # --- 追加フィールドの保存 ---
                    ogp_image=ogp_image,
                    meta_keywords=meta_keywords,
                    canonical_url=canonical_url,
                    json_ld=json_ld,
                    ext_json=ext_json
                    # --- ここまで ---
                )
                db.session.add(new_category)
                db.session.commit()
                flash('カテゴリが作成されました。', 'success')
                return redirect(url_for('admin.categories'))
                
    parent_categories = Category.query.order_by(Category.name).all()
    return render_template('admin/create_category.html', parent_categories=parent_categories)

@admin_bp.route('/category/edit/<int:category_id>/', methods=['GET', 'POST'])
@admin_required
def edit_category(category_id):
    category = Category.query.get_or_404(category_id)
    if request.method == 'POST':
        name = request.form.get('name')
        slug = request.form.get('slug')
        description = request.form.get('description')
        parent_id = request.form.get('parent_id')
        # --- 追加フィールドの取得 ---
        ogp_image = request.form.get('ogp_image')
        meta_keywords = request.form.get('meta_keywords')
        canonical_url = request.form.get('canonical_url')
        json_ld = request.form.get('json_ld')
        ext_json = request.form.get('ext_json')
        # --- ここまで ---

        if not name or not slug:
            flash('カテゴリ名とスラッグは必須です。', 'danger')
        else:
            # スラッグの重複チェック（自分自身を除く）
            existing_category_slug = Category.query.filter(Category.id != category_id, Category.slug == slug).first()
            existing_category_name = Category.query.filter(Category.id != category_id, Category.name == name).first()
            if existing_category_slug:
                flash('そのスラッグは既に使用されています。', 'danger')
            elif existing_category_name:
                flash('そのカテゴリ名は既に使用されています。', 'danger')
            else:
                category.name = name
                category.slug = slug
                category.description = description
                category.parent_id = int(parent_id) if parent_id else None
                # --- 追加フィールドの更新 ---
                category.ogp_image = ogp_image
                category.meta_keywords = meta_keywords
                category.canonical_url = canonical_url
                category.json_ld = json_ld
                category.ext_json = ext_json
                # --- ここまで ---
                db.session.commit()
                flash('カテゴリが更新されました。', 'success')
                return redirect(url_for('admin.categories'))

    parent_categories = Category.query.filter(Category.id != category_id).order_by(Category.name).all()
    return render_template('admin/edit_category.html', category=category, parent_categories=parent_categories)

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
    flash("コメント管理ページ - 未実装")
    return "コメント管理ページ - 未実装" # 一時的に文字列を返す

# サイト管理
@admin_bp.route('/site_settings/')
@admin_required
def site_settings():
    flash("サイト管理ページ - 未実装")
    return "サイト管理ページ - 未実装" # 一時的に文字列を返す

# Blueprint登録（app.pyの末尾で）
# app.register_blueprint(admin_bp)