"""
データベースモデル定義
ミニブログシステムの全データベーステーブル定義
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from flask_login import UserMixin
import pyotp
import secrets
from itsdangerous import URLSafeTimedSerializer
from sqlalchemy import select, func

db = SQLAlchemy()

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
    
    # TOTP関連フィールド
    totp_secret = db.Column(db.String(255), nullable=True)
    totp_enabled = db.Column(db.Boolean, default=False)
    
    # パスワードリセット関連フィールド
    reset_token = db.Column(db.String(255), nullable=True)
    reset_token_expires = db.Column(db.DateTime, nullable=True)
    
    # 通知設定
    notify_on_publish = db.Column(db.Boolean, default=False)
    notify_on_comment = db.Column(db.Boolean, default=False)
    
    # プロフィール情報
    introduction = db.Column(db.Text, nullable=True)  # 紹介文（250文字以内）
    birthplace = db.Column(db.String(10), nullable=True)  # 出身地（10文字以内）
    birthday = db.Column(db.Date, nullable=True)  # 誕生日
    
    # SNSアカウント情報（個別カラム）
    sns_x = db.Column(db.String(100), nullable=True)  # X（旧Twitter）
    sns_facebook = db.Column(db.String(100), nullable=True)  # Facebook
    sns_instagram = db.Column(db.String(100), nullable=True)  # Instagram
    sns_threads = db.Column(db.String(100), nullable=True)  # Threads
    sns_youtube = db.Column(db.String(100), nullable=True)  # YouTube
    
    ext_json = db.Column(db.Text, nullable=True)  # 拡張用JSON
    
    articles = db.relationship('Article', backref='author', lazy=True) # UserとArticleの1対多
    
    def generate_totp_secret(self):
        """TOTP用のシークレットキーを生成"""
        self.totp_secret = pyotp.random_base32()
        return self.totp_secret
    
    def get_totp_uri(self, issuer_name="MiniBlog"):
        """Google Authenticator用のURI生成"""
        if not self.totp_secret:
            self.generate_totp_secret()
        return pyotp.totp.TOTP(self.totp_secret).provisioning_uri(
            name=self.email,
            issuer_name=issuer_name
        )
    
    def verify_totp(self, token):
        """TOTPトークンの検証"""
        if not self.totp_secret or not self.totp_enabled:
            return False
        totp = pyotp.TOTP(self.totp_secret)
        return totp.verify(token, valid_window=1)
    
    def generate_reset_token(self):
        """パスワードリセット用トークンを生成"""
        self.reset_token = secrets.token_urlsafe(32)
        self.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
        return self.reset_token
    
    def verify_reset_token(self, token):
        """パスワードリセットトークンの検証"""
        if not self.reset_token or not self.reset_token_expires:
            return False
        if datetime.utcnow() > self.reset_token_expires:
            return False
        return self.reset_token == token
    
    def clear_reset_token(self):
        """パスワードリセットトークンをクリア"""
        self.reset_token = None
        self.reset_token_expires = None

class Article(db.Model):
    __tablename__ = 'articles'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), unique=True, nullable=False)
    summary = db.Column(db.Text, nullable=True)  # 記事概要
    body = db.Column(db.Text)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 公開設定
    is_published = db.Column(db.Boolean, default=False)
    published_at = db.Column(db.DateTime, nullable=True)
    allow_comments = db.Column(db.Boolean, default=True)
    
    # SEO関連フィールド
    meta_title = db.Column(db.String(255), nullable=True)
    meta_description = db.Column(db.Text, nullable=True)
    meta_keywords = db.Column(db.String(255), nullable=True)
    canonical_url = db.Column(db.String(255), nullable=True)
    
    # 画像関連
    featured_image = db.Column(db.String(255), nullable=True)  # アイキャッチ画像
    featured_image_alt = db.Column(db.String(255), nullable=True)  # アイキャッチ画像のalt属性
    
    # ブロック型エディタ関連
    use_block_editor = db.Column(db.Boolean, default=False)  # ブロックエディタ使用フラグ
    legacy_body_backup = db.Column(db.Text, nullable=True)  # 従来のbodyフィールドのバックアップ
    
    # 拡張用
    ext_json = db.Column(db.Text, nullable=True)

    # Article から Category へのリレーションシップ
    categories = db.relationship(
        'Category',
        secondary=article_categories,
        lazy='select',
        back_populates='articles'  # ★ 変更: Category.articles と紐づける
    )
    
    # Article から ArticleBlock へのリレーションシップ
    blocks = db.relationship(
        'ArticleBlock',
        backref='article',
        lazy='select',
        cascade='all, delete-orphan',  # 記事削除時にブロックも削除
        order_by='ArticleBlock.sort_order'
    )
    
    def get_visible_blocks(self):
        """表示可能なブロックを順序付きで取得"""
        if not hasattr(self, 'blocks') or self.blocks is None:
            return []
        return self.blocks.filter_by(is_visible=True).order_by(ArticleBlock.sort_order).all()
    
    def get_text_content(self):
        """ブロックからテキストコンテンツを抽出（検索用）"""
        if not self.use_block_editor:
            return self.body or ''
        
        text_parts = []
        for block in self.get_visible_blocks():
            if block.is_text_block and block.content:
                text_parts.append(block.content)
            elif block.title:
                text_parts.append(block.title)
            elif block.is_external_article_block and block.ogp_title:
                text_parts.append(block.ogp_title)
        
        return '\n'.join(text_parts)
    
    def has_featured_image_block(self):
        """アイキャッチ画像ブロックが存在するかチェック"""
        return self.blocks.join(BlockType).filter(
            BlockType.type_name == 'featured_image',
            ArticleBlock.is_visible == True
        ).first() is not None
    
    def convert_to_block_editor(self):
        """従来形式からブロック型エディタに変換"""
        if self.use_block_editor:
            return False  # 既にブロック型
        
        # 従来のbodyをバックアップ
        self.legacy_body_backup = self.body
        
        # アイキャッチ画像をブロックとして追加
        if self.featured_image:
            featured_block_type = db.session.execute(select(BlockType).where(BlockType.type_name == 'featured_image')).scalar_one_or_none()
            if featured_block_type:
                featured_block = ArticleBlock(
                    article_id=self.id,
                    block_type_id=featured_block_type.id,
                    sort_order=1,
                    image_path=self.featured_image,
                    image_alt_text=f"{self.title}のアイキャッチ画像"
                )
                db.session.add(featured_block)
        
        # 本文をテキストブロックとして追加
        if self.body:
            text_block_type = db.session.execute(select(BlockType).where(BlockType.type_name == 'text')).scalar_one_or_none()
            if text_block_type:
                text_block = ArticleBlock(
                    article_id=self.id,
                    block_type_id=text_block_type.id,
                    sort_order=2,
                    content=self.body
                )
                db.session.add(text_block)
        
        self.use_block_editor = True
        self.body = None  # 従来のbodyをクリア
        db.session.commit()
        return True

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
    ogp_image_alt = db.Column(db.String(255), nullable=True)  # OGP画像のalt属性
    canonical_url = db.Column(db.String(255), nullable=True)
    json_ld = db.Column(db.Text, nullable=True)
    ext_json = db.Column(db.Text, nullable=True)

    parent = db.relationship('Category', remote_side=[id], backref=db.backref('children', lazy='select'))

    # Category から Article へのリレーションシップ
    articles = db.relationship(
        'Article',
        secondary=article_categories,
        lazy='select',
        back_populates='categories' # ★ 変更: Article.categories と紐づける
    )

    def __repr__(self):
        return f'<Category {self.name}>'

class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'), nullable=False)
    author_name = db.Column(db.String(100), nullable=False)
    author_email = db.Column(db.String(255), nullable=False)
    author_website = db.Column(db.String(255), nullable=True)
    content = db.Column(db.Text, nullable=False)
    is_approved = db.Column(db.Boolean, default=False)
    ip_address = db.Column(db.String(45), nullable=True)  # IPv6対応
    user_agent = db.Column(db.String(500), nullable=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=True)  # 返信機能用
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # リレーションシップ
    article = db.relationship('Article', backref=db.backref('comments', lazy='select'))
    parent = db.relationship('Comment', remote_side=[id], backref=db.backref('replies', lazy='select'))
    
    def __repr__(self):
        return f'<Comment {self.id}: {self.author_name} on Article {self.article_id}>'

class SiteSetting(db.Model):
    __tablename__ = 'site_settings'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), nullable=False, unique=True)
    value = db.Column(db.Text, nullable=True)
    description = db.Column(db.Text, nullable=True)
    setting_type = db.Column(db.String(20), default='text')  # text, boolean, number, json
    is_public = db.Column(db.Boolean, default=False)  # 公開設定かどうか
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<SiteSetting {self.key}: {self.value}>'
    
    @staticmethod
    def get_setting(key, default=None):
        """設定値を取得"""
        setting = db.session.execute(select(SiteSetting).where(SiteSetting.key == key)).scalar_one_or_none()
        return setting.value if setting else default
    
    @staticmethod
    def set_setting(key, value, description=None, setting_type='text', is_public=False):
        """設定値を保存または更新"""
        setting = db.session.execute(select(SiteSetting).where(SiteSetting.key == key)).scalar_one_or_none()
        if setting:
            setting.value = value
            setting.description = description or setting.description
            setting.setting_type = setting_type
            setting.is_public = is_public
            setting.updated_at = datetime.utcnow()
        else:
            setting = SiteSetting(
                key=key,
                value=value,
                description=description,
                setting_type=setting_type,
                is_public=is_public
            )
            db.session.add(setting)
        db.session.commit()
        return setting

# --- 画像管理用モデル ---

class UploadedImage(db.Model):
    """アップロード済み画像管理"""
    __tablename__ = 'uploaded_images'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)  # 保存時のファイル名
    original_filename = db.Column(db.String(255), nullable=False)  # 元のファイル名
    file_path = db.Column(db.String(500), nullable=False)  # 相対パス
    file_size = db.Column(db.Integer, nullable=False)  # ファイルサイズ（バイト）
    mime_type = db.Column(db.String(100), nullable=False)  # MIMEタイプ
    width = db.Column(db.Integer)  # 画像幅
    height = db.Column(db.Integer)  # 画像高さ
    
    # メタデータ
    alt_text = db.Column(db.String(255))  # alt属性
    caption = db.Column(db.Text)  # キャプション
    description = db.Column(db.Text)  # 説明
    
    # アップロード情報
    uploader_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 管理情報
    is_active = db.Column(db.Boolean, default=True)
    usage_count = db.Column(db.Integer, default=0)  # 使用回数
    last_used_at = db.Column(db.DateTime)  # 最終使用日時
    
    # タイムスタンプ
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # リレーションシップ
    uploader = db.relationship('User', backref=db.backref('uploaded_images', lazy='select'))
    
    def __repr__(self):
        return f'<UploadedImage {self.filename}: {self.alt_text or "No alt"}>'
    
    @property
    def file_url(self):
        """画像のURLを取得"""
        return f"/static/{self.file_path}"
    
    @property
    def file_size_mb(self):
        """ファイルサイズをMBで取得"""
        return round(self.file_size / (1024 * 1024), 2)
    
    @property
    def markdown_syntax(self):
        """マークダウン記法を生成"""
        alt = self.alt_text or self.original_filename
        if self.caption:
            return f'![{alt}]({self.file_url} "{self.caption}")'
        else:
            return f'![{alt}]({self.file_url})'
    
    def increment_usage(self):
        """使用回数を増加"""
        self.usage_count += 1
        self.last_used_at = datetime.utcnow()
        db.session.commit()

# --- ブロック型エディタ用モデル ---

class BlockType(db.Model):
    """ブロックタイプ定義"""
    __tablename__ = 'block_types'
    
    id = db.Column(db.Integer, primary_key=True)
    type_name = db.Column(db.String(50), nullable=False, unique=True)
    type_label = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    settings_schema = db.Column(db.Text)  # JSONスキーマ
    template_name = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # リレーションシップ
    blocks = db.relationship('ArticleBlock', backref='block_type', lazy='select')
    
    def __repr__(self):
        return f'<BlockType {self.type_name}: {self.type_label}>'
    
    @staticmethod
    def get_active_types():
        """アクティブなブロックタイプを取得"""
        return db.session.execute(select(BlockType).where(BlockType.is_active == True)).scalars().all()

class ArticleBlock(db.Model):
    """記事ブロック"""
    __tablename__ = 'article_blocks'
    
    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id', ondelete='CASCADE'), nullable=False)
    block_type_id = db.Column(db.Integer, db.ForeignKey('block_types.id'), nullable=False)
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    
    # ブロック共通フィールド
    title = db.Column(db.String(255))
    content = db.Column(db.Text)
    
    # 画像ブロック用
    image_path = db.Column(db.String(500))
    image_alt_text = db.Column(db.String(255))
    image_caption = db.Column(db.Text)
    crop_data = db.Column(db.Text)
    
    # SNS埋込用
    embed_url = db.Column(db.String(1000))
    embed_platform = db.Column(db.String(50))
    embed_id = db.Column(db.String(200))
    embed_html = db.Column(db.Text)
    
    # 外部記事埋込用（OGP）
    ogp_title = db.Column(db.String(500))
    ogp_description = db.Column(db.Text)
    ogp_image = db.Column(db.String(500))
    ogp_site_name = db.Column(db.String(200))
    ogp_url = db.Column(db.String(1000))
    ogp_cached_at = db.Column(db.DateTime)
    
    # ブロック設定・表示制御
    settings = db.Column(db.Text)  # JSON
    css_classes = db.Column(db.String(500))
    is_visible = db.Column(db.Boolean, default=True)
    
    # メタデータ
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # リレーションシップ（Articleから定義されるためここでは不要）
    
    def __repr__(self):
        return f'<ArticleBlock {self.id}: {self.block_type.type_name if self.block_type else "Unknown"} in Article {self.article_id}>'
    
    @property
    def is_text_block(self):
        """テキストブロックかどうか"""
        return self.block_type and self.block_type.type_name == 'text'
    
    @property
    def is_image_block(self):
        """画像ブロックかどうか"""
        return self.block_type and self.block_type.type_name == 'image'
    
    @property
    def is_sns_embed_block(self):
        """SNS埋込ブロックかどうか"""
        return self.block_type and self.block_type.type_name == 'sns_embed'
    
    @property
    def is_external_article_block(self):
        """外部記事埋込ブロックかどうか"""
        return self.block_type and self.block_type.type_name == 'external_article'
    
    @property
    def is_featured_image_block(self):
        """アイキャッチ画像ブロックかどうか"""
        return self.block_type and self.block_type.type_name == 'featured_image'
    
    def get_settings_json(self):
        """設定をJSONとして取得"""
        import json
        try:
            return json.loads(self.settings) if self.settings else {}
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_settings_json(self, settings_dict):
        """設定をJSONとして保存"""
        import json
        self.settings = json.dumps(settings_dict, ensure_ascii=False) if settings_dict else None
    
    @staticmethod
    def reorder_blocks(article_id, block_ids):
        """ブロックの順序を再設定"""
        for order, block_id in enumerate(block_ids, 1):
            block = db.session.execute(select(ArticleBlock).where(ArticleBlock.id == block_id, ArticleBlock.article_id == article_id)).scalar_one_or_none()
            if block:
                block.sort_order = order
        db.session.commit()