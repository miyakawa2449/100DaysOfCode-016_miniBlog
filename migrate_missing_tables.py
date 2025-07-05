#!/usr/bin/env python3
"""
不足テーブルのデータ移行
"""

import sqlite3
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

def migrate_missing_tables():
    sqlite_conn = sqlite3.connect('instance/miniblog.db')
    sqlite_conn.row_factory = sqlite3.Row
    
    mysql_url = os.environ.get('DATABASE_URL')
    mysql_engine = create_engine(mysql_url)
    
    print("🚀 不足テーブルのデータ移行を開始...")
    
    try:
        with mysql_engine.connect() as mysql_conn:
            # 1. site_settings の移行
            print("⚙️ site_settings を移行中...")
            settings = sqlite_conn.execute("SELECT * FROM site_settings").fetchall()
            
            for setting in settings:
                mysql_conn.execute(text("""
                    INSERT INTO site_settings (id, `key`, value, description, setting_type, is_public, created_at, updated_at)
                    VALUES (:id, :key, :value, :description, :setting_type, :is_public, :created_at, :updated_at)
                """), dict(setting))
            
            print(f"✅ site_settings {len(settings)}件を移行完了")
            
            # 2. block_types の移行
            print("🧱 block_types を移行中...")
            block_types = sqlite_conn.execute("SELECT * FROM block_types").fetchall()
            
            for block_type in block_types:
                mysql_conn.execute(text("""
                    INSERT INTO block_types (id, type_name, type_label, description, settings_schema, template_name, is_active, created_at, updated_at)
                    VALUES (:id, :type_name, :type_label, :description, :settings_schema, :template_name, :is_active, :created_at, :updated_at)
                """), dict(block_type))
            
            print(f"✅ block_types {len(block_types)}件を移行完了")
            
            # 3. article_blocks の移行
            print("📦 article_blocks を移行中...")
            article_blocks = sqlite_conn.execute("SELECT * FROM article_blocks").fetchall()
            
            for block in article_blocks:
                mysql_conn.execute(text("""
                    INSERT INTO article_blocks (id, article_id, block_type_id, sort_order, title, content, 
                                              image_path, image_alt_text, image_caption, crop_data,
                                              embed_url, embed_platform, embed_id, embed_html,
                                              ogp_title, ogp_description, ogp_image, ogp_site_name, ogp_url, ogp_cached_at,
                                              settings, css_classes, is_visible, created_at, updated_at)
                    VALUES (:id, :article_id, :block_type_id, :sort_order, :title, :content,
                           :image_path, :image_alt_text, :image_caption, :crop_data,
                           :embed_url, :embed_platform, :embed_id, :embed_html,
                           :ogp_title, :ogp_description, :ogp_image, :ogp_site_name, :ogp_url, :ogp_cached_at,
                           :settings, :css_classes, :is_visible, :created_at, :updated_at)
                """), dict(block))
            
            print(f"✅ article_blocks {len(article_blocks)}件を移行完了")
            
            mysql_conn.commit()
            
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False
    
    finally:
        sqlite_conn.close()
    
    print("🎉 不足テーブルの移行完了！")
    return True

if __name__ == "__main__":
    migrate_missing_tables()