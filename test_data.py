# test_data.py
from app import app
from models import db, User, Article, Category
from werkzeug.security import generate_password_hash
from datetime import datetime

with app.app_context():
    # テーブル作成
    db.create_all()
    
    # テストユーザー作成
    if not User.query.first():
        admin_user = User(
            email='admin@example.com',
            name='管理者',
            password_hash=generate_password_hash('password123'),
            role='admin',
            created_at=datetime.utcnow()
        )
        db.session.add(admin_user)
        db.session.commit()
        print("Admin user created")
    
    # テストカテゴリ作成
    if not Category.query.first():
        category = Category(
            name='テクノロジー',
            slug='technology',
            description='技術関連の記事',
            created_at=datetime.utcnow()
        )
        db.session.add(category)
        db.session.commit()
        print("Test category created")
    
    # テスト記事作成
    if not Article.query.first():
        user = User.query.first()
        category = Category.query.first()
        
        article = Article(
            title='テスト記事',
            slug='test-article',
            body='これはテスト記事です。',
            author_id=user.id,
            created_at=datetime.utcnow()
        )
        if category:
            article.categories.append(category)
        
        db.session.add(article)
        db.session.commit()
        print("Test article created")
    
    print("Test data creation completed!")