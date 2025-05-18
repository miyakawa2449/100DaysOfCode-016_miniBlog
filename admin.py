from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from models import db, User, Article  # ← ここもmodelsからインポート
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
    return render_template('admin/dashboard.html', user_count=user_count, article_count=article_count)

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

# Blueprint登録（app.pyの末尾で）
# app.register_blueprint(admin_bp)