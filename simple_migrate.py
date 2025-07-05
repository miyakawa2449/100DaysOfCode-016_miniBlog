#!/usr/bin/env python3
"""
簡単なSQLiteからMySQLへのデータ移行スクリプト
"""

import sqlite3
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# .envファイルを読み込み
load_dotenv()

def migrate_data():
    # SQLite接続
    sqlite_conn = sqlite3.connect('instance/miniblog.db')
    sqlite_conn.row_factory = sqlite3.Row
    
    # MySQL接続
    mysql_url = os.environ.get('DATABASE_URL')
    mysql_engine = create_engine(mysql_url)
    
    print("🚀 簡単データ移行を開始します...")
    
    try:
        with mysql_engine.connect() as mysql_conn:
            # 1. ユーザーデータの移行（基本フィールドのみ）
            print("👥 ユーザーデータを移行中...")
            users = sqlite_conn.execute("SELECT id, email, name, handle_name, password_hash, role, created_at, totp_secret, totp_enabled FROM users").fetchall()
            
            for user in users:
                mysql_conn.execute(text("""
                    INSERT INTO users (id, email, name, handle_name, password_hash, role, created_at, totp_secret, totp_enabled)
                    VALUES (:id, :email, :name, :handle_name, :password_hash, :role, :created_at, :totp_secret, :totp_enabled)
                """), dict(user))
            
            print(f"✅ ユーザー {len(users)}件を移行完了")
            
            # 2. カテゴリデータの移行（基本フィールドのみ）
            print("📁 カテゴリデータを移行中...")
            categories = sqlite_conn.execute("SELECT id, name, slug, description, parent_id, created_at, updated_at FROM categories").fetchall()
            
            for category in categories:
                mysql_conn.execute(text("""
                    INSERT INTO categories (id, name, slug, description, parent_id, created_at, updated_at)
                    VALUES (:id, :name, :slug, :description, :parent_id, :created_at, :updated_at)
                """), dict(category))
            
            print(f"✅ カテゴリ {len(categories)}件を移行完了")
            
            # 3. 記事データの移行（基本フィールドのみ）
            print("📝 記事データを移行中...")
            articles = sqlite_conn.execute("SELECT id, title, slug, body, summary, author_id, created_at, updated_at, published_at, is_published FROM articles").fetchall()
            
            for article in articles:
                mysql_conn.execute(text("""
                    INSERT INTO articles (id, title, slug, body, summary, author_id, created_at, updated_at, published_at, is_published)
                    VALUES (:id, :title, :slug, :body, :summary, :author_id, :created_at, :updated_at, :published_at, :is_published)
                """), dict(article))
            
            print(f"✅ 記事 {len(articles)}件を移行完了")
            
            # 4. 記事-カテゴリ関係の移行
            print("🔗 記事-カテゴリ関係を移行中...")
            article_categories = sqlite_conn.execute("SELECT article_id, category_id FROM article_categories").fetchall()
            
            for ac in article_categories:
                mysql_conn.execute(text("""
                    INSERT INTO article_categories (article_id, category_id)
                    VALUES (:article_id, :category_id)
                """), dict(ac))
            
            print(f"✅ 記事-カテゴリ関係 {len(article_categories)}件を移行完了")
            
            # コミット
            mysql_conn.commit()
            
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        return False
    
    finally:
        sqlite_conn.close()
    
    print("🎉 基本データ移行が完了しました！")
    return True

if __name__ == "__main__":
    migrate_data()