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
    articles = Article.query.order_by(Article.created_at.desc()).all()
    return render_template('admin/articles.html', articles=articles)

# 記事作成
@admin_bp.route('/article/create/', methods=['GET', 'POST'])
@admin_required
def create_article():
    if request.method == 'POST':
        title = request.form['title']
        slug = request.form['slug']
        body = request.form['body']
        author_id = session.get('user_id')
        article = Article(title=title, slug=slug, body=body, author_id=author_id)
        db.session.add(article)
        db.session.commit()
        flash('記事を作成しました')
        return redirect(url_for('admin.articles'))
    return render_template('admin/create_article.html')

# 記事編集
@admin_bp.route('/article/edit/<int:article_id>/', methods=['GET', 'POST'])
@admin_required
def edit_article(article_id):
    article = Article.query.get_or_404(article_id)
    flash(f"記事編集ページ (ID: {article_id}) - 未実装")
    return render_template('admin/edit_article.html', article=article) # 仮のテンプレート

# カテゴリ管理
@admin_bp.route('/categories/')
@admin_required
def categories():
    flash("カテゴリ管理ページ - 未実装")
    return "カテゴリ管理ページ - 未実装" # 一時的に文字列を返す

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