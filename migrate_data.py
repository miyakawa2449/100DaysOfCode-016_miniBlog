#!/usr/bin/env python3
"""
SQLiteからMySQLへのデータ移行スクリプト
"""

import sqlite3
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from datetime import datetime

# .envファイルを読み込み
load_dotenv()

def migrate_data():
    # SQLite接続
    sqlite_conn = sqlite3.connect('instance/miniblog.db')
    sqlite_conn.row_factory = sqlite3.Row  # 辞書形式でアクセス可能
    
    # MySQL接続
    mysql_url = os.environ.get('DATABASE_URL')
    mysql_engine = create_engine(mysql_url)
    
    print("🚀 データ移行を開始します...")
    
    try:
        with mysql_engine.connect() as mysql_conn:
            # 1. ユーザーデータの移行
            print("👥 ユーザーデータを移行中...")
            users = sqlite_conn.execute("SELECT * FROM users").fetchall()
            
            for user in users:
                mysql_conn.execute(text("""
                    INSERT INTO users (id, email, name, handle_name, password_hash, role,
                                     created_at, totp_secret, totp_enabled, reset_token,
                                     reset_token_expires, notify_on_publish, notify_on_comment,
                                     introduction, birthplace, birthday, sns_x, sns_facebook,
                                     sns_instagram, sns_threads, sns_youtube, ext_json)
                    VALUES (:id, :email, :name, :handle_name, :password_hash, :role,
                           :created_at, :totp_secret, :totp_enabled, :reset_token,
                           :reset_token_expires, :notify_on_publish, :notify_on_comment,
                           :introduction, :birthplace, :birthday, :sns_x, :sns_facebook,
                           :sns_instagram, :sns_threads, :sns_youtube, :ext_json)
                """), dict(user))
            
            print(f"✅ ユーザー {len(users)}件を移行完了")
            
            # 2. カテゴリデータの移行
            print("📁 カテゴリデータを移行中...")
            categories = sqlite_conn.execute("SELECT * FROM categories").fetchall()
            
            for category in categories:
                mysql_conn.execute(text("""
                    INSERT INTO categories (id, name, slug, description, parent_id, 
                                          created_at, updated_at, seo_title, seo_description,
                                          seo_keywords, canonical_url, ogp_image_path, ext_json)
                    VALUES (:id, :name, :slug, :description, :parent_id,
                           :created_at, :updated_at, :seo_title, :seo_description,
                           :seo_keywords, :canonical_url, :ogp_image_path, :ext_json)
                """), dict(category))
            
            print(f"✅ カテゴリ {len(categories)}件を移行完了")
            
            # 3. 記事データの移行
            print("📝 記事データを移行中...")
            articles = sqlite_conn.execute("SELECT * FROM articles").fetchall()
            
            for article in articles:
                mysql_conn.execute(text("""
                    INSERT INTO articles (id, title, slug, content, summary, author_id,
                                        created_at, updated_at, published_at, is_published,
                                        view_count, seo_title, seo_description, seo_keywords,
                                        canonical_url, featured_image_path, ext_json)
                    VALUES (:id, :title, :slug, :content, :summary, :author_id,
                           :created_at, :updated_at, :published_at, :is_published,
                           :view_count, :seo_title, :seo_description, :seo_keywords,
                           :canonical_url, :featured_image_path, :ext_json)
                """), dict(article))
            
            print(f"✅ 記事 {len(articles)}件を移行完了")
            
            # 4. 記事-カテゴリ関係の移行
            print("🔗 記事-カテゴリ関係を移行中...")
            article_categories = sqlite_conn.execute("SELECT * FROM article_categories").fetchall()
            
            for ac in article_categories:
                mysql_conn.execute(text("""
                    INSERT INTO article_categories (article_id, category_id)
                    VALUES (:article_id, :category_id)
                """), dict(ac))
            
            print(f"✅ 記事-カテゴリ関係 {len(article_categories)}件を移行完了")
            
            # 5. コメントデータの移行
            print("💬 コメントデータを移行中...")
            comments = sqlite_conn.execute("SELECT * FROM comments").fetchall()
            
            for comment in comments:
                mysql_conn.execute(text("""
                    INSERT INTO comments (id, article_id, author_name, author_email,
                                        content, created_at, is_approved, ext_json)
                    VALUES (:id, :article_id, :author_name, :author_email,
                           :content, :created_at, :is_approved, :ext_json)
                """), dict(comment))
            
            print(f"✅ コメント {len(comments)}件を移行完了")
            
            # 6. アップロード画像データの移行
            print("🖼️ 画像データを移行中...")
            try:
                uploaded_images = sqlite_conn.execute("SELECT * FROM uploaded_images").fetchall()
                
                for image in uploaded_images:
                    mysql_conn.execute(text("""
                        INSERT INTO uploaded_images (id, filename, original_filename,
                                                   file_path, file_size, mime_type,
                                                   uploaded_at, alt_text, description, ext_json)
                        VALUES (:id, :filename, :original_filename,
                               :file_path, :file_size, :mime_type,
                               :uploaded_at, :alt_text, :description, :ext_json)
                    """), dict(image))
                
                print(f"✅ 画像 {len(uploaded_images)}件を移行完了")
            except sqlite3.OperationalError:
                print("ℹ️ uploaded_images テーブルが存在しないため、スキップしました")
            
            # コミット
            mysql_conn.commit()
            
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        return False
    
    finally:
        sqlite_conn.close()
    
    print("🎉 データ移行が完了しました！")
    return True

if __name__ == "__main__":
    migrate_data()