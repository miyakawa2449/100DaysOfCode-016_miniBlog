"""
ブロック型エディタ用フォーム定義
各ブロックタイプに対応したフォームクラス
"""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, HiddenField, FileField, SelectField, IntegerField
from wtforms.validators import DataRequired, Optional, URL, Length, ValidationError
from flask_wtf.file import FileAllowed
from wtforms.widgets import HiddenInput

class BaseBlockForm(FlaskForm):
    """ブロック共通フォーム"""
    block_id = HiddenField('Block ID')
    block_type = HiddenField('Block Type')
    sort_order = IntegerField('Sort Order', widget=HiddenInput())
    title = StringField('ブロックタイトル', validators=[Optional(), Length(max=255)])
    css_classes = StringField('追加CSSクラス', validators=[Optional(), Length(max=500)])

class TextBlockForm(BaseBlockForm):
    """テキストブロックフォーム（Markdown対応）"""
    content = TextAreaField('テキスト内容', validators=[Optional()])
    
    def validate_content(self, field):
        """Markdown形式の基本的なバリデーション"""
        # 基本的なサニタイゼーション（必要に応じて拡張）
        if field.data and len(field.data.strip()) == 0:
            field.data = None

class ImageBlockForm(BaseBlockForm):
    """画像ブロックフォーム（1:1比率700px）"""
    image_file = FileField('画像ファイル', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], '画像ファイルのみアップロード可能です。')
    ])
    image_alt_text = StringField('代替テキスト', validators=[Optional(), Length(max=255)])
    image_caption = TextAreaField('画像キャプション', validators=[Optional()])
    
    # 画像トリミング用フィールド
    crop_x = HiddenField('Crop X')
    crop_y = HiddenField('Crop Y') 
    crop_width = HiddenField('Crop Width')
    crop_height = HiddenField('Crop Height')

class FeaturedImageBlockForm(BaseBlockForm):
    """アイキャッチ画像ブロックフォーム（16:9比率800px）"""
    image_file = FileField('アイキャッチ画像', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], '画像ファイルのみアップロード可能です。')
    ])
    image_alt_text = StringField('代替テキスト', validators=[Optional(), Length(max=255)])
    image_caption = TextAreaField('画像キャプション', validators=[Optional()])
    
    # 16:9アスペクト比用トリミングフィールド
    crop_x = HiddenField('Crop X')
    crop_y = HiddenField('Crop Y') 
    crop_width = HiddenField('Crop Width')
    crop_height = HiddenField('Crop Height')

class SNSEmbedBlockForm(BaseBlockForm):
    """SNS埋込ブロックフォーム"""
    embed_url = StringField('SNS投稿URL', validators=[DataRequired(), URL(), Length(max=1000)])
    embed_platform = SelectField('プラットフォーム', choices=[
        ('', '自動検出'),
        ('twitter', 'X (Twitter)'),
        ('facebook', 'Facebook'),
        ('instagram', 'Instagram'),
        ('threads', 'Threads'),
        ('youtube', 'YouTube')
    ], validators=[Optional()])
    
    def validate_embed_url(self, field):
        """URL形式とプラットフォーム対応チェック"""
        url = field.data.lower() if field.data else ''
        
        # 対応プラットフォームのURLパターンチェック
        supported_patterns = [
            'twitter.com', 'x.com',  # Twitter/X
            'facebook.com', 'fb.com',  # Facebook
            'instagram.com',  # Instagram
            'threads.net',  # Threads
            'youtube.com', 'youtu.be'  # YouTube
        ]
        
        if not any(pattern in url for pattern in supported_patterns):
            raise ValidationError('対応していないSNSプラットフォームのURLです。')

class ExternalArticleBlockForm(BaseBlockForm):
    """外部記事埋込ブロックフォーム（OGPカード）"""
    external_url = StringField('記事URL', validators=[DataRequired(), URL(), Length(max=1000)])
    
    # OGP情報（自動取得されるが手動編集も可能）
    ogp_title = StringField('記事タイトル', validators=[Optional(), Length(max=500)])
    ogp_description = TextAreaField('記事説明', validators=[Optional()])
    ogp_site_name = StringField('サイト名', validators=[Optional(), Length(max=200)])

class BlockEditorForm(FlaskForm):
    """ブロックエディタ全体のフォーム"""
    # 記事基本情報
    article_id = HiddenField('Article ID')
    use_block_editor = HiddenField('Use Block Editor', default='true')
    
    # 記事基本フィールド（従来のArticleFormから移行）
    title = StringField('記事タイトル', validators=[DataRequired(), Length(max=255)])
    slug = StringField('スラッグ', validators=[Optional(), Length(max=255)])
    summary = TextAreaField('記事概要', validators=[Optional(), Length(max=500)])
    
    # SEO関連フィールド
    meta_title = StringField('メタタイトル', validators=[Optional(), Length(max=255)])
    meta_description = TextAreaField('メタディスクリプション', validators=[Optional(), Length(max=300)])
    meta_keywords = StringField('メタキーワード', validators=[Optional(), Length(max=255)])
    canonical_url = StringField('正規URL', validators=[Optional(), URL(), Length(max=255)])
    
    # 公開設定
    category_id = SelectField('カテゴリ', coerce=int, validators=[Optional()])
    is_published = HiddenField('Published Status')  # チェックボックスの代わり
    allow_comments = HiddenField('Allow Comments')  # チェックボックスの代わり
    
    # ブロック操作用フィールド
    blocks_data = HiddenField('Blocks Data')  # JSON形式でブロック情報を保存
    deleted_blocks = HiddenField('Deleted Blocks')  # 削除されたブロックのID一覧
    
    # 新規ブロック追加用
    new_block_type = SelectField('新しいブロックタイプ', choices=[
        ('', 'ブロックタイプを選択'),
        ('text', 'テキストブロック'),
        ('image', '画像ブロック'),
        ('sns_embed', 'SNS埋込ブロック'),
        ('external_article', '外部記事埋込ブロック'),
        ('featured_image', 'アイキャッチ画像ブロック')
    ], validators=[Optional()])

def get_block_form_class(block_type_name):
    """ブロックタイプに応じたフォームクラスを取得"""
    form_mapping = {
        'text': TextBlockForm,
        'image': ImageBlockForm,
        'featured_image': FeaturedImageBlockForm,
        'sns_embed': SNSEmbedBlockForm,
        'external_article': ExternalArticleBlockForm
    }
    return form_mapping.get(block_type_name, BaseBlockForm)

def create_block_form(block_type_name, **kwargs):
    """ブロックタイプに応じたフォームインスタンスを作成"""
    form_class = get_block_form_class(block_type_name)
    return form_class(**kwargs)