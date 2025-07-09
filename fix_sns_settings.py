from models import db, SiteSetting
from app import app
import json

with app.app_context():
    # 個別設定を public に変更
    individual_settings = ['social_twitter', 'social_facebook', 'social_instagram', 'social_github', 'social_youtube']
    
    for key in individual_settings:
        setting = db.session.execute(db.select(SiteSetting).where(SiteSetting.key == key)).scalar_one_or_none()
        if setting:
            setting.is_public = True
            print(f'{key}: {setting.value} -> is_public=True')
    
    # 個別設定の値を取得
    twitter = SiteSetting.get_setting('social_twitter', '')
    facebook = SiteSetting.get_setting('social_facebook', '')
    instagram = SiteSetting.get_setting('social_instagram', '')
    github = SiteSetting.get_setting('social_github', '')
    youtube = SiteSetting.get_setting('social_youtube', '')
    
    # social_media_links（JSON）を更新
    sns_links = {
        'twitter': twitter,
        'facebook': facebook,
        'instagram': instagram,
        'github': github,
        'youtube': youtube
    }
    
    SiteSetting.set_setting('social_media_links', json.dumps(sns_links), 'SNSリンク（JSON形式）', 'json', True)
    
    db.session.commit()
    print('SNS設定を修正しました')
    print('social_media_links:', json.dumps(sns_links))