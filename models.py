from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin # UserMixin をインポート

db = SQLAlchemy() # ← この行を有効にします (コメントアウトを解除)

# --- 中間テーブル: Article と Category の多対多関連 ---
article_categories = db.Table('article_categories',
    db.Column('article_id', db.Integer, db.ForeignKey('articles.id'), primary_key=True),
    db.Column('category_id', db.Integer, db.ForeignKey('categories.id'), primary_key=True)
)

class User(db.Model, UserMixin): # UserMixin を継承
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    handle_name = db.Column(db.String(100))
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='author') # 'admin', 'author'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    articles = db.relationship('Article', backref='author', lazy=True) # UserとArticleの1対多

class Article(db.Model):
    __tablename__ = 'articles'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), unique=True, nullable=False)
    body = db.Column(db.Text)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Article から Category へのリレーションシップ
    categories = db.relationship(
        'Category',
        secondary=article_categories,
        lazy='dynamic',
        back_populates='articles'  # ★ 変更: Category.articles と紐づける
    )

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    slug = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    meta_title = db.Column(db.String(255), nullable=True)
    meta_description = db.Column(db.Text, nullable=True)
    meta_keywords = db.Column(db.String(255), nullable=True)
    ogp_image = db.Column(db.String(255), nullable=True)
    canonical_url = db.Column(db.String(255), nullable=True)
    json_ld = db.Column(db.Text, nullable=True)
    ext_json = db.Column(db.Text, nullable=True)

    parent = db.relationship('Category', remote_side=[id], backref=db.backref('children', lazy='dynamic'))

    # Category から Article へのリレーションシップ
    articles = db.relationship(
        'Article',
        secondary=article_categories,
        lazy='dynamic',
        back_populates='categories' # ★ 変更: Article.categories と紐づける
    )

    def __repr__(self):
        return f'<Category {self.name}>'

class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    article = db.relationship('Article', backref=db.backref('comments', lazy='dynamic'))