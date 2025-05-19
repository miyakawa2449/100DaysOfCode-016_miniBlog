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

    categories = db.relationship(
        'Category', 
        secondary=article_categories,
        lazy='dynamic', 
        backref=db.backref('articles', lazy='dynamic') 
    )

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    slug = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    
    # --- 追加フィールド ---
    ogp_image = db.Column(db.String(255), nullable=True)      # OGP画像のパス
    meta_keywords = db.Column(db.String(255), nullable=True)  # メタキーワード (カンマ区切りなど)
    canonical_url = db.Column(db.String(255), nullable=True) # 正規URL
    json_ld = db.Column(db.Text, nullable=True)               # JSON-LD 構造化データ
    ext_json = db.Column(db.Text, nullable=True)              # 拡張用JSONデータ (用途に応じて)
    # --- ここまで追加フィールド ---
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    parent = db.relationship('Category', remote_side=[id], backref='children', lazy=True)
    # 'articles' リレーションシップは Article モデルの backref で定義済み

    def __repr__(self):
        return f'<Category {self.name}>'

class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    article = db.relationship('Article', backref=db.backref('comments', lazy='dynamic'))