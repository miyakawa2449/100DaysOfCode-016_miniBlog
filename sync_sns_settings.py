from models import db, SiteSetting
from app import app
import json

with app.app_context():
    # 個別のSNS設定を確認
    social_twitter = SiteSetting.get_setting('social_twitter', '')
    social_facebook = SiteSetting.get_setting('social_facebook', '')
    social_instagram = SiteSetting.get_setting('social_instagram', '')
    social_github = SiteSetting.get_setting('social_github', '')
    social_youtube = SiteSetting.get_setting('social_youtube', '')
    
    print("現在の個別SNS設定:")
    print(f"Twitter: {social_twitter}")
    print(f"Facebook: {social_facebook}")
    print(f"Instagram: {social_instagram}")
    print(f"GitHub: {social_github}")
    print(f"YouTube: {social_youtube}")
    
    # social_media_links（JSON形式）の設定を更新
    sns_links = {
        "twitter": social_twitter,
        "facebook": social_facebook,
        "instagram": social_instagram,
        "github": social_github,
        "youtube": social_youtube
    }
    
    # GitHubの設定がない場合は作成
    if not social_github:
        SiteSetting.set_setting('social_github', '', 'GitHubプロフィールURL', 'text', True)
        print("GitHub設定を作成しました")
    
    # JSON形式の設定を更新
    SiteSetting.set_setting('social_media_links', json.dumps(sns_links), 'SNSリンク（JSON形式）', 'json', True)
    print("social_media_linksを更新しました:", json.dumps(sns_links))