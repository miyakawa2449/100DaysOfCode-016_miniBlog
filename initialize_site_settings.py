#!/usr/bin/env python
"""
サイト設定初期化スクリプト
基本的なサイト設定項目を初期化します
"""

from app import app
from models import db, SiteSetting

# 初期設定項目の定義
INITIAL_SETTINGS = [
    # 基本情報
    {
        'key': 'site_name',
        'value': 'ミニブログ',
        'description': 'サイト名',
        'setting_type': 'text',
        'is_public': True
    },
    {
        'key': 'site_description',
        'value': 'プログラミング、テック、ライフスタイルに関する記事をお届けします',
        'description': 'サイトの説明文',
        'setting_type': 'text',
        'is_public': True
    },
    {
        'key': 'site_logo_url',
        'value': '',
        'description': 'サイトロゴのURL',
        'setting_type': 'text',
        'is_public': True
    },
    {
        'key': 'site_favicon_url',
        'value': '',
        'description': 'ファビコンのURL',
        'setting_type': 'text',
        'is_public': True
    },
    {
        'key': 'contact_email',
        'value': 'contact@example.com',
        'description': 'お問い合わせメールアドレス',
        'setting_type': 'text',
        'is_public': True
    },
    
    # SNSリンク（JSON形式）
    {
        'key': 'social_media_links',
        'value': '{"twitter": "", "facebook": "", "instagram": "", "youtube": ""}',
        'description': 'SNSリンク（JSON形式）',
        'setting_type': 'json',
        'is_public': True
    },
    
    # 機能設定
    {
        'key': 'maintenance_mode',
        'value': 'false',
        'description': 'メンテナンスモード',
        'setting_type': 'boolean',
        'is_public': False
    },
    {
        'key': 'registration_enabled',
        'value': 'true',
        'description': '新規登録の許可',
        'setting_type': 'boolean',
        'is_public': False
    },
    {
        'key': 'comment_moderation',
        'value': 'true',
        'description': 'コメント承認制',
        'setting_type': 'boolean',
        'is_public': False
    },
    {
        'key': 'max_upload_size',
        'value': '5',
        'description': 'アップロードファイル上限サイズ (MB)',
        'setting_type': 'number',
        'is_public': False
    },
    
    # SEO設定
    {
        'key': 'seo_keywords',
        'value': 'ブログ,プログラミング,テック,ライフスタイル',
        'description': 'SEOキーワード',
        'setting_type': 'text',
        'is_public': True
    },
    {
        'key': 'google_analytics_id',
        'value': '',
        'description': 'Google Analytics測定ID',
        'setting_type': 'text',
        'is_public': False
    },
    {
        'key': 'google_search_console_verification',
        'value': '',
        'description': 'Google Search Console認証コード',
        'setting_type': 'text',
        'is_public': False
    },
    
    # 外観設定
    {
        'key': 'theme_color',
        'value': '#007bff',
        'description': 'テーマカラー',
        'setting_type': 'text',
        'is_public': True
    },
    {
        'key': 'footer_text',
        'value': '© 2025 ミニブログ. All rights reserved.',
        'description': 'フッターテキスト',
        'setting_type': 'text',
        'is_public': True
    },
    
    # 投稿設定
    {
        'key': 'posts_per_page',
        'value': '8',
        'description': '1ページあたりの記事数',
        'setting_type': 'number',
        'is_public': False
    }
]

def initialize_settings():
    """サイト設定を初期化"""
    with app.app_context():
        print("サイト設定を初期化中...")
        
        for setting_data in INITIAL_SETTINGS:
            # 既存の設定をチェック
            existing_setting = db.session.execute(
                db.select(SiteSetting).where(SiteSetting.key == setting_data['key'])
            ).scalar_one_or_none()
            
            if existing_setting:
                print(f"設定 '{setting_data['key']}' は既に存在します - スキップ")
                continue
            
            # 新しい設定を作成
            new_setting = SiteSetting(
                key=setting_data['key'],
                value=setting_data['value'],
                description=setting_data['description'],
                setting_type=setting_data['setting_type'],
                is_public=setting_data['is_public']
            )
            
            db.session.add(new_setting)
            print(f"設定 '{setting_data['key']}' を追加しました")
        
        try:
            db.session.commit()
            print("サイト設定の初期化が完了しました")
        except Exception as e:
            db.session.rollback()
            print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    initialize_settings()