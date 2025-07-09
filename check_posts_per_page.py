from models import db, SiteSetting
from app import app

with app.app_context():
    setting = db.session.execute(db.select(SiteSetting).where(SiteSetting.key == 'posts_per_page')).scalar_one_or_none()
    if setting:
        print('現在のposts_per_page:', setting.value)
        if setting.value != '8':
            setting.value = '8'
            db.session.commit()
            print('posts_per_pageを8に更新しました')
        else:
            print('既に8に設定されています')
    else:
        print('posts_per_page設定が見つかりません - 新規作成')
        SiteSetting.set_setting('posts_per_page', '8', '1ページあたりの記事数', 'number', False)
        print('posts_per_page設定を作成しました')