# データベース仕様書

**最終更新日**: 2025年7月7日  
**DBMS**: MySQL 9.3.0  
**ORM**: SQLAlchemy 2.0.41  
**Driver**: PyMySQL 1.1.1

## 📋 データベース概要

### 基本設定
- **文字セット**: utf8mb4 (絵文字対応)
- **照合順序**: utf8mb4_unicode_ci
- **エンジン**: InnoDB (トランザクション対応)
- **タイムゾーン**: UTC

### 接続設定
```python
DATABASE_URL = "mysql+pymysql://user:password@host:port/database"
SQLALCHEMY_DATABASE_URI = DATABASE_URL
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
    'echo': False  # 本番環境では False
}
```

## 🗄️ テーブル設計

### 1. users (ユーザー)

#### テーブル構造
```sql
CREATE TABLE users (
    id INTEGER NOT NULL AUTO_INCREMENT,
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    handle_name VARCHAR(100),
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'author',
    
    -- プロフィール情報
    bio TEXT,
    location VARCHAR(100),
    birthday DATE,
    
    -- SNSアカウント
    x_username VARCHAR(100),
    facebook_url VARCHAR(255),
    instagram_url VARCHAR(255),
    threads_url VARCHAR(255),
    youtube_url VARCHAR(255),
    
    -- 2段階認証
    totp_secret VARCHAR(32),
    totp_enabled BOOLEAN DEFAULT FALSE,
    backup_codes JSON,
    
    -- 通知設定
    notification_settings JSON,
    
    -- パスワードリセット
    reset_token VARCHAR(255),
    reset_token_expires DATETIME,
    
    -- システム情報
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME,
    
    PRIMARY KEY (id),
    INDEX idx_email (email),
    INDEX idx_handle_name (handle_name),
    INDEX idx_role (role)
);
```

#### フィールド詳細

| フィールド | 型 | NULL | デフォルト | 説明 |
|-----------|-----|------|-----------|------|
| id | INTEGER | NO | AUTO_INCREMENT | 主キー |
| email | VARCHAR(255) | NO | - | メールアドレス (ログインID) |
| name | VARCHAR(100) | NO | - | 表示名 |
| handle_name | VARCHAR(100) | YES | NULL | ハンドルネーム (URL用) |
| password_hash | VARCHAR(255) | NO | - | パスワードハッシュ (pbkdf2:sha256) |
| role | VARCHAR(20) | NO | 'author' | 権限 (admin/author) |
| bio | TEXT | YES | NULL | 自己紹介文 |
| location | VARCHAR(100) | YES | NULL | 出身地・居住地 |
| birthday | DATE | YES | NULL | 誕生日 |
| x_username | VARCHAR(100) | YES | NULL | X(Twitter)ユーザー名 |
| facebook_url | VARCHAR(255) | YES | NULL | FacebookページURL |
| instagram_url | VARCHAR(255) | YES | NULL | InstagramプロフィールURL |
| threads_url | VARCHAR(255) | YES | NULL | ThreadsプロフィールURL |
| youtube_url | VARCHAR(255) | YES | NULL | YouTubeチャンネルURL |
| totp_secret | VARCHAR(32) | YES | NULL | TOTP秘密鍵 |
| totp_enabled | BOOLEAN | NO | FALSE | 2FA有効フラグ |
| backup_codes | JSON | YES | NULL | バックアップコード |
| notification_settings | JSON | YES | NULL | 通知設定 |
| reset_token | VARCHAR(255) | YES | NULL | パスワードリセットトークン |
| reset_token_expires | DATETIME | YES | NULL | トークン有効期限 |
| created_at | DATETIME | NO | CURRENT_TIMESTAMP | 作成日時 |
| last_login | DATETIME | YES | NULL | 最終ログイン日時 |

#### 制約・インデックス
- **UNIQUE**: email
- **INDEX**: email, handle_name, role
- **CHECK**: role IN ('admin', 'author')

### 2. articles (記事)

#### テーブル構造
```sql
CREATE TABLE articles (
    id INTEGER NOT NULL AUTO_INCREMENT,
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL UNIQUE,
    summary TEXT,
    body LONGTEXT NOT NULL,
    
    -- SEO関連
    meta_title VARCHAR(255),
    meta_description TEXT,
    keywords VARCHAR(255),
    canonical_url VARCHAR(255),
    
    -- ステータス
    is_published BOOLEAN DEFAULT FALSE,
    allow_comments BOOLEAN DEFAULT TRUE,
    
    -- 画像
    featured_image VARCHAR(255),
    
    -- 関連
    author_id INTEGER NOT NULL,
    publication_date DATETIME,
    
    -- システム情報
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    PRIMARY KEY (id),
    FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_slug (slug),
    INDEX idx_author_id (author_id),
    INDEX idx_is_published (is_published),
    INDEX idx_publication_date (publication_date),
    INDEX idx_created_at (created_at)
);
```

#### フィールド詳細

| フィールド | 型 | NULL | デフォルト | 説明 |
|-----------|-----|------|-----------|------|
| id | INTEGER | NO | AUTO_INCREMENT | 主キー |
| title | VARCHAR(255) | NO | - | 記事タイトル |
| slug | VARCHAR(255) | NO | - | URLスラッグ (unique) |
| summary | TEXT | YES | NULL | 記事要約 |
| body | LONGTEXT | NO | - | 記事本文 (Markdown) |
| meta_title | VARCHAR(255) | YES | NULL | SEOタイトル |
| meta_description | TEXT | YES | NULL | SEO説明文 |
| keywords | VARCHAR(255) | YES | NULL | SEOキーワード |
| canonical_url | VARCHAR(255) | YES | NULL | 正規URL |
| is_published | BOOLEAN | NO | FALSE | 公開フラグ |
| allow_comments | BOOLEAN | NO | TRUE | コメント許可フラグ |
| featured_image | VARCHAR(255) | YES | NULL | アイキャッチ画像パス |
| author_id | INTEGER | NO | - | 投稿者ID (FK) |
| publication_date | DATETIME | YES | NULL | 公開予定日時 |
| created_at | DATETIME | NO | CURRENT_TIMESTAMP | 作成日時 |
| updated_at | DATETIME | NO | CURRENT_TIMESTAMP | 更新日時 |

#### 制約・インデックス
- **UNIQUE**: slug
- **FOREIGN KEY**: author_id → users(id)
- **INDEX**: slug, author_id, is_published, publication_date, created_at

### 3. categories (カテゴリ)

#### テーブル構造
```sql
CREATE TABLE categories (
    id INTEGER NOT NULL AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    
    -- 階層構造
    parent_id INTEGER,
    
    -- SEO関連
    meta_title VARCHAR(255),
    meta_description TEXT,
    keywords VARCHAR(255),
    
    -- 画像
    ogp_image VARCHAR(255),
    
    -- システム情報
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    PRIMARY KEY (id),
    FOREIGN KEY (parent_id) REFERENCES categories(id) ON DELETE SET NULL,
    INDEX idx_slug (slug),
    INDEX idx_parent_id (parent_id),
    INDEX idx_name (name)
);
```

#### フィールド詳細

| フィールド | 型 | NULL | デフォルト | 説明 |
|-----------|-----|------|-----------|------|
| id | INTEGER | NO | AUTO_INCREMENT | 主キー |
| name | VARCHAR(100) | NO | - | カテゴリ名 |
| slug | VARCHAR(100) | NO | - | URLスラッグ (unique) |
| description | TEXT | YES | NULL | カテゴリ説明 |
| parent_id | INTEGER | YES | NULL | 親カテゴリID (Self FK) |
| meta_title | VARCHAR(255) | YES | NULL | SEOタイトル |
| meta_description | TEXT | YES | NULL | SEO説明文 |
| keywords | VARCHAR(255) | YES | NULL | SEOキーワード |
| ogp_image | VARCHAR(255) | YES | NULL | OGP画像パス |
| created_at | DATETIME | NO | CURRENT_TIMESTAMP | 作成日時 |
| updated_at | DATETIME | NO | CURRENT_TIMESTAMP | 更新日時 |

#### 制約・インデックス
- **UNIQUE**: slug
- **FOREIGN KEY**: parent_id → categories(id) (Self Reference)
- **INDEX**: slug, parent_id, name

### 4. article_categories (記事-カテゴリ関連)

#### テーブル構造
```sql
CREATE TABLE article_categories (
    article_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    
    PRIMARY KEY (article_id, category_id),
    FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE,
    INDEX idx_article_id (article_id),
    INDEX idx_category_id (category_id)
);
```

#### フィールド詳細

| フィールド | 型 | NULL | デフォルト | 説明 |
|-----------|-----|------|-----------|------|
| article_id | INTEGER | NO | - | 記事ID (FK) |
| category_id | INTEGER | NO | - | カテゴリID (FK) |

#### 制約・インデックス
- **PRIMARY KEY**: (article_id, category_id)
- **FOREIGN KEY**: article_id → articles(id), category_id → categories(id)
- **INDEX**: article_id, category_id

### 5. comments (コメント)

#### テーブル構造
```sql
CREATE TABLE comments (
    id INTEGER NOT NULL AUTO_INCREMENT,
    content TEXT NOT NULL,
    author_name VARCHAR(100) NOT NULL,
    author_email VARCHAR(255) NOT NULL,
    
    -- 関連
    article_id INTEGER NOT NULL,
    parent_id INTEGER,
    
    -- 管理
    is_approved BOOLEAN DEFAULT FALSE,
    
    -- システム情報
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    
    PRIMARY KEY (id),
    FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_id) REFERENCES comments(id) ON DELETE CASCADE,
    INDEX idx_article_id (article_id),
    INDEX idx_parent_id (parent_id),
    INDEX idx_is_approved (is_approved),
    INDEX idx_created_at (created_at)
);
```

#### フィールド詳細

| フィールド | 型 | NULL | デフォルト | 説明 |
|-----------|-----|------|-----------|------|
| id | INTEGER | NO | AUTO_INCREMENT | 主キー |
| content | TEXT | NO | - | コメント内容 |
| author_name | VARCHAR(100) | NO | - | 投稿者名 |
| author_email | VARCHAR(255) | NO | - | 投稿者メール |
| article_id | INTEGER | NO | - | 記事ID (FK) |
| parent_id | INTEGER | YES | NULL | 親コメントID (返信用) |
| is_approved | BOOLEAN | NO | FALSE | 承認フラグ |
| created_at | DATETIME | NO | CURRENT_TIMESTAMP | 投稿日時 |
| ip_address | VARCHAR(45) | YES | NULL | 投稿者IP (IPv6対応) |

#### 制約・インデックス
- **FOREIGN KEY**: article_id → articles(id), parent_id → comments(id)
- **INDEX**: article_id, parent_id, is_approved, created_at

### 6. site_settings (サイト設定)

#### テーブル構造
```sql
CREATE TABLE site_settings (
    id INTEGER NOT NULL AUTO_INCREMENT,
    key VARCHAR(100) NOT NULL UNIQUE,
    value TEXT,
    description TEXT,
    setting_type VARCHAR(50) DEFAULT 'text',
    is_public BOOLEAN DEFAULT FALSE,
    
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    PRIMARY KEY (id),
    INDEX idx_key (key),
    INDEX idx_setting_type (setting_type),
    INDEX idx_is_public (is_public)
);
```

#### フィールド詳細

| フィールド | 型 | NULL | デフォルト | 説明 |
|-----------|-----|------|-----------|------|
| id | INTEGER | NO | AUTO_INCREMENT | 主キー |
| key | VARCHAR(100) | NO | - | 設定キー (unique) |
| value | TEXT | YES | NULL | 設定値 |
| description | TEXT | YES | NULL | 設定説明 |
| setting_type | VARCHAR(50) | NO | 'text' | 設定タイプ |
| is_public | BOOLEAN | NO | FALSE | 公開設定フラグ |
| updated_at | DATETIME | NO | CURRENT_TIMESTAMP | 更新日時 |

#### 制約・インデックス
- **UNIQUE**: key
- **INDEX**: key, setting_type, is_public

#### 設定タイプ
- **text**: テキスト設定
- **number**: 数値設定
- **boolean**: True/False設定
- **json**: JSON形式設定
- **file**: ファイルパス設定

### 7. uploaded_images (アップロード画像)

#### テーブル構造
```sql
CREATE TABLE uploaded_images (
    id INTEGER NOT NULL AUTO_INCREMENT,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(255) NOT NULL,
    file_size INTEGER NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    
    -- メタデータ
    alt_text VARCHAR(255),
    caption TEXT,
    description TEXT,
    
    -- 画像情報
    width INTEGER,
    height INTEGER,
    
    -- 関連
    uploader_id INTEGER NOT NULL,
    
    -- システム情報
    upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    
    PRIMARY KEY (id),
    FOREIGN KEY (uploader_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_filename (filename),
    INDEX idx_uploader_id (uploader_id),
    INDEX idx_upload_date (upload_date),
    INDEX idx_is_active (is_active)
);
```

#### フィールド詳細

| フィールド | 型 | NULL | デフォルト | 説明 |
|-----------|-----|------|-----------|------|
| id | INTEGER | NO | AUTO_INCREMENT | 主キー |
| filename | VARCHAR(255) | NO | - | ファイル名 |
| file_path | VARCHAR(255) | NO | - | ファイルパス |
| file_size | INTEGER | NO | - | ファイルサイズ (bytes) |
| mime_type | VARCHAR(100) | NO | - | MIMEタイプ |
| alt_text | VARCHAR(255) | YES | NULL | Alt属性 |
| caption | TEXT | YES | NULL | キャプション |
| description | TEXT | YES | NULL | 詳細説明 |
| width | INTEGER | YES | NULL | 画像幅 |
| height | INTEGER | YES | NULL | 画像高さ |
| uploader_id | INTEGER | NO | - | アップロード者ID (FK) |
| upload_date | DATETIME | NO | CURRENT_TIMESTAMP | アップロード日時 |
| is_active | BOOLEAN | NO | TRUE | 有効フラグ (論理削除) |

#### 制約・インデックス
- **FOREIGN KEY**: uploader_id → users(id)
- **INDEX**: filename, uploader_id, upload_date, is_active

## 🔗 リレーション設計

### 1. ユーザー関連

#### users → articles (1:N)
```python
# SQLAlchemy 2.0 定義
class User(db.Model):
    articles = db.relationship('Article', backref='author', lazy='select')

class Article(db.Model):
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
```

#### users → uploaded_images (1:N)
```python
class User(db.Model):
    uploaded_images = db.relationship('UploadedImage', backref='uploader', lazy='select')

class UploadedImage(db.Model):
    uploader_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
```

### 2. 記事関連

#### articles ↔ categories (N:M)
```python
# 中間テーブル
article_categories = db.Table('article_categories',
    db.Column('article_id', db.Integer, db.ForeignKey('articles.id'), primary_key=True),
    db.Column('category_id', db.Integer, db.ForeignKey('categories.id'), primary_key=True)
)

class Article(db.Model):
    categories = db.relationship('Category', secondary=article_categories, backref='articles', lazy='select')
```

#### articles → comments (1:N)
```python
class Article(db.Model):
    comments = db.relationship('Comment', backref='article', lazy='select')

class Comment(db.Model):
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'), nullable=False)
```

### 3. 階層構造

#### categories → categories (Self Reference)
```python
class Category(db.Model):
    parent_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    parent = db.relationship('Category', remote_side=[id], backref=db.backref('children', lazy='select'))
```

#### comments → comments (Self Reference)
```python
class Comment(db.Model):
    parent_id = db.Column(db.Integer, db.ForeignKey('comments.id'))
    parent = db.relationship('Comment', remote_side=[id], backref=db.backref('replies', lazy='select'))
```

## 📊 インデックス戦略

### 主要インデックス

#### 1. ユニーク制約
- `users.email` - ログイン高速化
- `articles.slug` - URL解決高速化
- `categories.slug` - URL解決高速化
- `site_settings.key` - 設定取得高速化

#### 2. 外部キー
- `articles.author_id` - 記事-ユーザー結合
- `comments.article_id` - コメント-記事結合
- `article_categories.article_id, category_id` - N:M結合

#### 3. フィルタリング
- `articles.is_published` - 公開記事検索
- `comments.is_approved` - 承認済みコメント検索
- `uploaded_images.is_active` - アクティブ画像検索

#### 4. ソート
- `articles.created_at` - 記事一覧ソート
- `comments.created_at` - コメント時系列ソート
- `uploaded_images.upload_date` - 画像一覧ソート

### 複合インデックス

#### 記事検索最適化
```sql
CREATE INDEX idx_articles_published_date ON articles(is_published, created_at DESC);
```

#### コメント検索最適化
```sql
CREATE INDEX idx_comments_article_approved ON comments(article_id, is_approved);
```

## 🔧 SQLAlchemy 2.0 対応

### クエリパターン

#### 基本検索
```python
# 単一レコード取得
user = db.session.execute(select(User).where(User.email == email)).scalar_one_or_none()

# 複数レコード取得
articles = db.session.execute(
    select(Article).where(Article.is_published.is_(True)).order_by(Article.created_at.desc())
).scalars().all()

# カウント
count = db.session.execute(select(func.count(Article.id))).scalar()
```

#### Boolean比較 (MySQL最適化)
```python
# 推奨: .is_() を使用
published_articles = select(Article).where(Article.is_published.is_(True))
pending_comments = select(Comment).where(Comment.is_approved.is_(False))

# NULL比較
parent_comments = select(Comment).where(Comment.parent_id.is_(None))
```

#### ページネーション
```python
# SQLAlchemy 2.0 対応
pagination = db.paginate(
    select(Article).order_by(Article.created_at.desc()),
    page=page, per_page=10, error_out=False
)
```

#### 関連データ取得
```python
# 記事とカテゴリの結合
articles_with_categories = db.session.execute(
    select(Article).options(selectinload(Article.categories))
).scalars().all()

# コメントと返信の階層取得
comments = db.session.execute(
    select(Comment).where(
        Comment.article_id == article_id,
        Comment.parent_id.is_(None)
    ).options(selectinload(Comment.replies))
).scalars().all()
```

## 🔒 セキュリティ考慮

### データ保護

#### パスワード
- **ハッシュ化**: pbkdf2:sha256 (Werkzeug Security)
- **ソルト**: 自動生成
- **最小長**: 8文字

#### TOTP秘密鍵
- **暗号化**: Base32エンコード
- **長さ**: 32文字
- **保存**: VARCHAR(32)

#### セッション
- **保存**: サーバーサイド
- **暗号化**: Flask SECRET_KEY
- **有効期限**: 24時間 (設定可能)

### データ整合性

#### 外部キー制約
- **CASCADE**: ユーザー削除時の記事・画像削除
- **SET NULL**: カテゴリ削除時の親カテゴリ無効化
- **RESTRICT**: 関連データ存在時の削除防止

#### チェック制約
```sql
-- 役割制限
ALTER TABLE users ADD CONSTRAINT chk_role CHECK (role IN ('admin', 'author'));

-- ファイルサイズ制限
ALTER TABLE uploaded_images ADD CONSTRAINT chk_file_size CHECK (file_size > 0 AND file_size <= 10485760);
```

## 📈 パフォーマンス最適化

### クエリ最適化

#### N+1問題対策
```python
# 悪い例: N+1問題発生
articles = db.session.execute(select(Article)).scalars().all()
for article in articles:
    print(article.author.name)  # 各記事で個別クエリ発生

# 良い例: eager loading
articles = db.session.execute(
    select(Article).options(selectinload(Article.author))
).scalars().all()
```

#### バッチ処理
```python
# 大量データの効率的な処理
for article_batch in db.session.execute(select(Article)).scalars().partitions(100):
    # 100件ずつ処理
    process_articles(article_batch)
```

### インデックス活用
```python
# インデックスを活用したクエリ
recent_published = db.session.execute(
    select(Article).where(
        Article.is_published.is_(True)  # idx_articles_published_date 活用
    ).order_by(Article.created_at.desc()).limit(10)
).scalars().all()
```

## 🗂️ データ移行

### マイグレーション履歴

#### 初期設定 (001)
```python
# users, articles, categories テーブル作成
def upgrade():
    op.create_table('users', ...)
    op.create_table('articles', ...)
    op.create_table('categories', ...)
```

#### コメント機能追加 (002)
```python
def upgrade():
    op.create_table('comments', ...)
```

#### 画像管理追加 (003)
```python
def upgrade():
    op.create_table('uploaded_images', ...)
```

#### SQLAlchemy 2.0対応 (004)
```python
def upgrade():
    # lazy='dynamic' → lazy='select' 変更
    # Boolean比較最適化
    pass
```

### データ整合性チェック
```sql
-- 孤立レコード検出
SELECT a.id, a.title FROM articles a 
LEFT JOIN users u ON a.author_id = u.id 
WHERE u.id IS NULL;

-- 循環参照検出
WITH RECURSIVE category_tree AS (
    SELECT id, parent_id, name, 0 as depth
    FROM categories WHERE parent_id IS NULL
    UNION ALL
    SELECT c.id, c.parent_id, c.name, ct.depth + 1
    FROM categories c
    JOIN category_tree ct ON c.parent_id = ct.id
    WHERE ct.depth < 10
)
SELECT * FROM category_tree WHERE depth >= 10;
```

## 📊 統計・分析

### 基本統計クエリ
```python
# ダッシュボード統計
stats = {
    'users': db.session.execute(select(func.count(User.id))).scalar(),
    'articles': db.session.execute(select(func.count(Article.id))).scalar(),
    'published': db.session.execute(
        select(func.count(Article.id)).where(Article.is_published.is_(True))
    ).scalar(),
    'comments': db.session.execute(select(func.count(Comment.id))).scalar(),
    'pending_comments': db.session.execute(
        select(func.count(Comment.id)).where(Comment.is_approved.is_(False))
    ).scalar()
}
```

### 月次統計
```python
from datetime import datetime, timedelta

this_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
next_month = (this_month + timedelta(days=32)).replace(day=1)

monthly_stats = {
    'articles': db.session.execute(
        select(func.count(Article.id)).where(
            Article.created_at >= this_month,
            Article.created_at < next_month
        )
    ).scalar(),
    'users': db.session.execute(
        select(func.count(User.id)).where(
            User.created_at >= this_month,
            User.created_at < next_month
        )
    ).scalar()
}
```

---

**テーブル数**: 7テーブル  
**リレーション数**: 8関係  
**インデックス数**: 20+個  
**最終更新**: 2025年7月7日