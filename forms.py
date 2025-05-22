# filepath: c:\Users\tmiya\projects\100Day_new\016_miniBlog\forms.py (または適切な場所)
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, FileField, IntegerField, HiddenField
from wtforms.validators import DataRequired, Optional, URL, Length
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