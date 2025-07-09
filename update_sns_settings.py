from models import db, SiteSetting
from app import app
import json

with app.app_context():
    # 現在のSNS設定を確認
    setting = db.session.execute(db.select(SiteSetting).where(SiteSetting.key == 'social_media_links')).scalar_one_or_none()
    
    if setting:
        print("現在のSNS設定:", setting.value)
        
        # サンプルSNSリンクを設定
        sns_links = {
            "twitter": "https://twitter.com/yourusername",
            "youtube": "https://youtube.com/@yourchannel",
            "instagram": "https://instagram.com/yourusername",
            "github": "https://github.com/yourusername",
            "facebook": "",
            "linkedin": ""
        }
        
        setting.value = json.dumps(sns_links)
        db.session.commit()
        print("SNS設定を更新しました:", setting.value)
    else:
        print("SNS設定が見つかりません")