#!/usr/bin/env python3
"""
記事ID 19の編集状況確認スクリプト
ブロック型エディタと従来型エディタでの一貫性をチェック
"""

import os
import sys

# アプリケーションのパスを追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import db, User, Article, Category
from werkzeug.security import generate_password_hash
import importlib

def init_app():
    """Flask アプリケーションを初期化"""
    from flask import Flask
    from flask_migrate import Migrate
    from flask_wtf.csrf import CSRFProtect
    from flask_mail import Mail
    from flask_login import LoginManager
    import os
    
    # Flask アプリケーションを作成
    app = Flask(__name__)
    
    # 設定を読み込み
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_default_secret_key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///miniblog.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # データベースを初期化
    db.init_app(app)
    
    return app

def check_article_19():
    """記事ID 19の詳細情報を確認"""
    app = init_app()
    
    with app.app_context():
        print("=== 記事ID 19の編集状況確認 ===\n")
        
        # 記事ID 19を取得
        article = Article.query.get(19)
        
        if not article:
            print("❌ 記事ID 19が見つかりません")
            return False
        
        print(f"📰 記事タイトル: {article.title}")
        print(f"📝 記事概要: {article.summary or 'なし'}")
        print(f"🔗 スラッグ: {article.slug}")
        print(f"📅 作成日時: {article.created_at}")
        print(f"📅 更新日時: {article.updated_at}")
        print(f"✅ 公開状態: {article.is_published}")
        print(f"💬 コメント許可: {article.allow_comments}")
        print(f"🔧 ブロック型エディタ使用: {article.use_block_editor}")
        
        # SEO・メタ情報
        print(f"\n--- SEO・メタ情報 ---")
        print(f"🏷️ メタタイトル: {article.meta_title or 'なし'}")
        print(f"📋 メタ説明: {article.meta_description or 'なし'}")
        print(f"🔍 キーワード: {article.meta_keywords or 'なし'}")
        print(f"🔗 カノニカルURL: {article.canonical_url or 'なし'}")
        
        # カテゴリ情報
        print(f"\n--- カテゴリ情報 ---")
        categories = article.categories.all()
        if categories:
            for cat in categories:
                print(f"📂 カテゴリ: {cat.name} (ID: {cat.id})")
        else:
            print("📂 カテゴリ: なし")
        
        # アイキャッチ画像
        print(f"\n--- 画像情報 ---")
        print(f"🖼️ アイキャッチ画像: {article.featured_image or 'なし'}")
        
        # ブロック情報（ブロック型エディタの場合）
        if article.use_block_editor:
            print(f"\n--- ブロック情報 ---")
            blocks = article.get_visible_blocks()
            print(f"🧱 ブロック数: {len(blocks)}")
            for i, block in enumerate(blocks, 1):
                block_type_name = getattr(block.block_type, 'display_name', None) or getattr(block.block_type, 'type_name', 'Unknown')
                print(f"  {i}. {block_type_name} (順序: {block.sort_order})")
                if hasattr(block, 'title') and block.title:
                    print(f"     タイトル: {block.title}")
                if hasattr(block, 'content') and block.content:
                    content_preview = block.content[:100] + "..." if len(block.content) > 100 else block.content
                    print(f"     内容: {content_preview}")
        
        # 従来型エディタの本文
        if article.body:
            print(f"\n--- 従来型エディタ本文 ---")
            body_preview = article.body[:200] + "..." if len(article.body) > 200 else article.body
            print(f"📝 本文: {body_preview}")
        
        # バックアップ情報
        if article.legacy_body_backup:
            print(f"\n--- バックアップ情報 ---")
            backup_preview = article.legacy_body_backup[:200] + "..." if len(article.legacy_body_backup) > 200 else article.legacy_body_backup
            print(f"💾 従来型本文バックアップ: {backup_preview}")
        
        print(f"\n✅ 記事ID 19の確認が完了しました")
        return True

def check_database_state():
    """データベースの全体的な状態を確認"""
    app = init_app()
    
    with app.app_context():
        print("=== データベース状態確認 ===\n")
        
        user_count = User.query.count()
        article_count = Article.query.count()
        category_count = Category.query.count()
        
        print(f"👥 ユーザー数: {user_count}")
        print(f"📰 記事数: {article_count}")
        print(f"📂 カテゴリ数: {category_count}")
        
        # 管理者ユーザーの確認
        admin_user = User.query.filter_by(role='admin').first()
        if admin_user:
            print(f"👑 管理者: {admin_user.name} ({admin_user.email})")
        else:
            print("❌ 管理者ユーザーが見つかりません")

if __name__ == '__main__':
    try:
        print("データベース状態を確認中...\n")
        check_database_state()
        print("\n" + "="*50 + "\n")
        check_article_19()
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()