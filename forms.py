# filepath: c:\Users\tmiya\projects\100Day_new\016_miniBlog\forms.py (または適切な場所)
"""
フォーム定義
ユーザー入力フォームとバリデーション定義
"""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, FileField, IntegerField, HiddenField, PasswordField, BooleanField, SelectField
from wtforms.validators import DataRequired, Optional, URL, Length, Email, ValidationError
import re
from wtforms.widgets import HiddenInput
from flask_wtf.file import FileAllowed

class CategoryForm(FlaskForm):
    name = StringField('カテゴリ名', validators=[DataRequired(), Length(max=100)])
    slug = StringField('スラッグ', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('説明', validators=[Optional()])
    parent_id = IntegerField('親カテゴリID', validators=[Optional()])

    # OGP画像関連
    ogp_image_file = FileField('OGP画像', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], '画像ファイルのみアップロード可能です。')
    ])
    ogp_crop_x = HiddenField('OGP Crop X')
    ogp_crop_y = HiddenField('OGP Crop Y')
    ogp_crop_width = HiddenField('OGP Crop Width')
    ogp_crop_height = HiddenField('OGP Crop Height')
    ogp_crop_rotate = IntegerField('OGP Crop Rotate', widget=HiddenInput(), validators=[Optional()])
    ogp_crop_scaleX = IntegerField('OGP Crop ScaleX', widget=HiddenInput(), validators=[Optional()])
    ogp_crop_scaleY = IntegerField('OGP Crop ScaleY', widget=HiddenInput(), validators=[Optional()])

    # SEO関連フィールド
    meta_title = StringField('メタタイトル', validators=[Optional(), Length(max=255)])
    meta_description = TextAreaField('メタディスクリプション', validators=[Optional()])
    meta_keywords = StringField('メタキーワード (カンマ区切り)', validators=[Optional(), Length(max=255)])
    canonical_url = StringField('正規URL', validators=[Optional(), URL(), Length(max=255)])
    json_ld = TextAreaField('JSON-LD 構造化データ', validators=[Optional()])
    ext_json = TextAreaField('拡張JSONデータ', validators=[Optional()])

    submit = SubmitField('更新')

class LoginForm(FlaskForm):
    email = StringField('メールアドレス', validators=[DataRequired(), Email()])
    password = PasswordField('パスワード', validators=[DataRequired()])
    submit = SubmitField('ログイン')

class ArticleForm(FlaskForm):
    title = StringField('タイトル', validators=[DataRequired(), Length(max=255)])
    slug = StringField('スラッグ', validators=[DataRequired(), Length(max=255)])
    summary = TextAreaField('記事概要', validators=[Optional(), Length(max=500)])
    body = TextAreaField('本文', validators=[Optional()])
    
    # SEO関連フィールド
    meta_title = StringField('メタタイトル', validators=[Optional(), Length(max=255)])
    meta_description = TextAreaField('メタディスクリプション', validators=[Optional(), Length(max=300)])
    meta_keywords = StringField('メタキーワード', validators=[Optional(), Length(max=255)])
    canonical_url = StringField('正規URL', validators=[Optional(), URL(), Length(max=255)])
    
    # 画像アップロード
    featured_image = FileField('アイキャッチ画像', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], '画像ファイルのみアップロード可能です。')
    ])
    
    # 公開設定
    category_id = SelectField('カテゴリ', coerce=int, validators=[Optional()])
    is_published = BooleanField('公開する', validators=[Optional()])
    allow_comments = BooleanField('コメントを許可', validators=[Optional()])
    
    submit = SubmitField('保存')

def validate_password_strength(password):
    """パスワード強度チェック"""
    if len(password) < 8:
        raise ValidationError('パスワードは8文字以上である必要があります。')
    if not re.search(r'[A-Z]', password):
        raise ValidationError('パスワードには大文字を含む必要があります。')
    if not re.search(r'[a-z]', password):
        raise ValidationError('パスワードには小文字を含む必要があります。')
    if not re.search(r'\d', password):
        raise ValidationError('パスワードには数字を含む必要があります。')
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', password):
        raise ValidationError('パスワードには特殊文字を含む必要があります。')

class UserRegistrationForm(FlaskForm):
    email = StringField('メールアドレス', validators=[DataRequired(), Email()])
    name = StringField('氏名', validators=[DataRequired(), Length(max=100)])
    password = PasswordField('パスワード', validators=[DataRequired()])
    password_confirm = PasswordField('パスワード確認', validators=[DataRequired()])
    submit = SubmitField('登録')

    def validate_password(self, field):
        validate_password_strength(field.data)

    def validate_password_confirm(self, field):
        if field.data != self.password.data:
            raise ValidationError('パスワードが一致しません。')

class TOTPVerificationForm(FlaskForm):
    totp_code = StringField('認証コード', validators=[DataRequired(), Length(min=6, max=6)])
    submit = SubmitField('認証')

class TOTPSetupForm(FlaskForm):
    totp_code = StringField('認証コード', validators=[DataRequired(), Length(min=6, max=6)])
    submit = SubmitField('2段階認証を有効化')

class PasswordResetRequestForm(FlaskForm):
    email = StringField('メールアドレス', validators=[DataRequired(), Email()])
    submit = SubmitField('パスワードリセット要求')

class PasswordResetForm(FlaskForm):
    password = PasswordField('新しいパスワード', validators=[DataRequired()])
    password_confirm = PasswordField('パスワード確認', validators=[DataRequired()])
    submit = SubmitField('パスワードを変更')

    def validate_password(self, field):
        validate_password_strength(field.data)

    def validate_password_confirm(self, field):
        if field.data != self.password.data:
            raise ValidationError('パスワードが一致しません。')