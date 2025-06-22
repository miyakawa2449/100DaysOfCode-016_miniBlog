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