#!/usr/bin/env python3
"""
アイキャッチ画像データの修正・再移行
"""

import sqlite3
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

def fix_featured_images():
    sqlite_conn = sqlite3.connect('instance/miniblog.db')
    sqlite_conn.row_factory = sqlite3.Row
    
    mysql_url = os.environ.get('DATABASE_URL')
    mysql_engine = create_engine(mysql_url)
    
    print("🖼️ アイキャッチ画像データの修正を開始...")
    
    try:
        with mysql_engine.connect() as mysql_conn:
            # SQLiteからアイキャッチ画像情報を取得
            featured_articles = sqlite_conn.execute("""
                SELECT id, featured_image, featured_image_alt 
                FROM articles 
                WHERE featured_image IS NOT NULL AND featured_image != ''
            """).fetchall()
            
            print(f"📋 修正対象: {len(featured_articles)}件")
            
            for article in featured_articles:
                # MySQLの記事レコードを更新
                mysql_conn.execute(text("""
                    UPDATE articles 
                    SET featured_image = :featured_image, 
                        featured_image_alt = :featured_image_alt
                    WHERE id = :id
                """), {
                    'id': article['id'],
                    'featured_image': article['featured_image'],
                    'featured_image_alt': article['featured_image_alt']
                })
                
                print(f"✅ 記事ID:{article['id']} - {article['featured_image']}")
            
            mysql_conn.commit()
            
            # 確認
            print("\n🔍 修正後の確認:")
            result = mysql_conn.execute(text("""
                SELECT COUNT(*) as count 
                FROM articles 
                WHERE featured_image IS NOT NULL AND featured_image != ''
            """)).fetchone()
            
            print(f"📊 アイキャッチ画像付き記事: {result[0]}件")
            
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False
    
    finally:
        sqlite_conn.close()
    
    print("🎉 アイキャッチ画像データの修正完了！")
    return True

if __name__ == "__main__":
    fix_featured_images()