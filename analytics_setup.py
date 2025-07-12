#!/usr/bin/env python3
"""
Google Analytics設定の初期化スクリプト
"""

import sys
sys.path.append('.')
import app as app_module
app = app_module.app
from models import db, SiteSetting

def setup_analytics_settings():
    """Google Analytics関連の設定を初期化"""
    with app.app_context():
        # Google Analytics設定
        analytics_settings = [
            {
                'key': 'google_analytics_id',
                'value': '',
                'description': 'Google Analytics 4 Measurement ID (例: G-XXXXXXXXXX)',
                'setting_type': 'text',
                'is_public': True
            },
            {
                'key': 'google_tag_manager_id',
                'value': '',
                'description': 'Google Tag Manager Container ID (例: GTM-XXXXXXX)',
                'setting_type': 'text',
                'is_public': True
            },
            {
                'key': 'google_analytics_enabled',
                'value': 'false',
                'description': 'Google Analyticsを有効にする',
                'setting_type': 'boolean',
                'is_public': True
            },
            {
                'key': 'custom_analytics_code',
                'value': '',
                'description': 'カスタムアナリティクスコード（HTMLタグ）',
                'setting_type': 'text',
                'is_public': True
            },
            {
                'key': 'analytics_track_admin',
                'value': 'false',
                'description': '管理者のアクセスも追跡する',
                'setting_type': 'boolean',
                'is_public': False
            },
            # GA4 Enhanced E-commerce設定
            {
                'key': 'enhanced_ecommerce_enabled',
                'value': 'false',
                'description': 'Enhanced E-commerce追跡を有効にする',
                'setting_type': 'boolean',
                'is_public': True
            },
            # カスタムイベント設定
            {
                'key': 'track_scroll_events',
                'value': 'true',
                'description': 'スクロール追跡を有効にする',
                'setting_type': 'boolean',
                'is_public': True
            },
            {
                'key': 'track_file_downloads',
                'value': 'true',
                'description': 'ファイルダウンロード追跡を有効にする',
                'setting_type': 'boolean',
                'is_public': True
            },
            {
                'key': 'track_external_links',
                'value': 'true',
                'description': '外部リンククリック追跡を有効にする',
                'setting_type': 'boolean',
                'is_public': True
            },
            {
                'key': 'track_page_engagement',
                'value': 'true',
                'description': 'ページエンゲージメント追跡を有効にする',
                'setting_type': 'boolean',
                'is_public': True
            },
            {
                'key': 'track_site_search',
                'value': 'true',
                'description': 'サイト内検索追跡を有効にする',
                'setting_type': 'boolean',
                'is_public': True
            },
            {
                'key': 'track_user_properties',
                'value': 'false',
                'description': 'ユーザープロパティ追跡を有効にする',
                'setting_type': 'boolean',
                'is_public': True
            },
            # プライバシー・Cookie同意管理
            {
                'key': 'cookie_consent_enabled',
                'value': 'true',
                'description': 'Cookie同意バナーを有効にする',
                'setting_type': 'boolean',
                'is_public': True
            },
            {
                'key': 'gdpr_mode',
                'value': 'true',
                'description': 'GDPR対応モードを有効にする',
                'setting_type': 'boolean',
                'is_public': True
            },
            {
                'key': 'ccpa_mode',
                'value': 'false',
                'description': 'CCPA対応モードを有効にする',
                'setting_type': 'boolean',
                'is_public': True
            },
            {
                'key': 'consent_banner_text',
                'value': 'このサイトではCookieを使用してサイトの利用状況を分析し、ユーザー体験を向上させています。',
                'description': 'Cookie同意バナーテキスト',
                'setting_type': 'text',
                'is_public': True
            },
            {
                'key': 'privacy_policy_url',
                'value': '/privacy-policy',
                'description': 'プライバシーポリシーURL',
                'setting_type': 'text',
                'is_public': True
            },
            {
                'key': 'analytics_storage',
                'value': 'denied',
                'description': 'Analytics Storage設定',
                'setting_type': 'text',
                'is_public': True
            },
            {
                'key': 'ad_storage',
                'value': 'denied',
                'description': 'Ad Storage設定',
                'setting_type': 'text',
                'is_public': True
            }
        ]
        
        for setting_data in analytics_settings:
            existing = SiteSetting.query.filter_by(key=setting_data['key']).first()
            if not existing:
                SiteSetting.set_setting(**setting_data)
                print(f"✅ 設定追加: {setting_data['key']}")
            else:
                print(f"⏭️  設定済み: {setting_data['key']}")
        
        print("🎉 Google Analytics設定の初期化が完了しました")

if __name__ == '__main__':
    setup_analytics_settings()