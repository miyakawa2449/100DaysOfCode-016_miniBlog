#!/usr/bin/env python3
"""
ブロック型エディタ用データベースマイグレーションスクリプト
既存のデータベースにブロックエディタ機能を追加
"""

import os
import sys
from flask import Flask
from models import db, Article, BlockType, ArticleBlock
from datetime import datetime

def create_app():
    """Flask アプリケーションを作成"""
    app = Flask(__name__)
    
    # 設定読み込み
    app.config['SECRET_KEY'] = 'your-secret-key-here'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///miniblog.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    return app

def check_column_exists(table_name, column_name):
    """指定されたテーブルにカラムが存在するかチェック"""
    from sqlalchemy import text
    with db.engine.connect() as conn:
        result = conn.execute(text(f"PRAGMA table_info({table_name})"))
        columns = [row[1] for row in result]
        return column_name in columns

def migrate_database():
    """データベースマイグレーション実行"""
    print("ブロック型エディタ用データベースマイグレーション開始...")
    
    try:
        # 1. 新しいテーブル作成
        print("新しいテーブルを作成中...")
        db.create_all()
        print("✓ テーブル作成完了")
        
        # 2. Articles テーブルに新しいカラムを追加
        print("Articles テーブルのカラム追加中...")
        
        # use_block_editor カラムの追加
        if not check_column_exists('articles', 'use_block_editor'):
            from sqlalchemy import text
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE articles ADD COLUMN use_block_editor BOOLEAN DEFAULT FALSE'))
                conn.commit()
            print("✓ use_block_editor カラム追加")
        else:
            print("○ use_block_editor カラムは既に存在")
            
        # legacy_body_backup カラムの追加
        if not check_column_exists('articles', 'legacy_body_backup'):
            from sqlalchemy import text
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE articles ADD COLUMN legacy_body_backup TEXT'))
                conn.commit()
            print("✓ legacy_body_backup カラム追加")
        else:
            print("○ legacy_body_backup カラムは既に存在")
        
        # 3. 初期ブロックタイプデータの挿入
        print("初期ブロックタイプデータを挿入中...")
        
        block_types_data = [
            {
                'type_name': 'text',
                'type_label': 'テキストブロック',
                'description': 'Markdown対応のテキストコンテンツ',
                'template_name': 'blocks/text_block.html'
            },
            {
                'type_name': 'image',
                'type_label': '画像ブロック',
                'description': '1:1比率700pxの画像ブロック',
                'template_name': 'blocks/image_block.html'
            },
            {
                'type_name': 'sns_embed',
                'type_label': 'SNS埋込',
                'description': 'X/Facebook/Instagram/Threads/YouTube埋込',
                'template_name': 'blocks/sns_embed_block.html'
            },
            {
                'type_name': 'external_article',
                'type_label': '外部記事埋込',
                'description': 'URL入力でOGPカード化',
                'template_name': 'blocks/external_article_block.html'
            },
            {
                'type_name': 'featured_image',
                'type_label': 'アイキャッチ画像',
                'description': '16:9比率800pxのアイキャッチ画像（記事先頭専用）',
                'template_name': 'blocks/featured_image_block.html'
            }
        ]
        
        for block_data in block_types_data:
            existing_block = BlockType.query.filter_by(type_name=block_data['type_name']).first()
            if not existing_block:
                block_type = BlockType(**block_data)
                db.session.add(block_type)
                print(f"✓ {block_data['type_label']} ブロックタイプ追加")
            else:
                print(f"○ {block_data['type_label']} ブロックタイプは既に存在")
        
        # 4. 変更をコミット
        db.session.commit()
        print("✓ データベース変更をコミット")
        
        # 5. マイグレーション完了確認
        print("\nマイグレーション完了確認:")
        article_count = Article.query.count()
        block_type_count = BlockType.query.count()
        print(f"- 記事数: {article_count}")
        print(f"- ブロックタイプ数: {block_type_count}")
        
        print("\n✅ ブロック型エディタ用データベースマイグレーション完了!")
        print("これでダッシュボードにアクセスできるようになります。")
        
    except Exception as e:
        print(f"❌ マイグレーション中にエラーが発生しました: {e}")
        db.session.rollback()
        return False
    
    return True

def rollback_migration():
    """マイグレーションのロールバック（必要に応じて）"""
    print("マイグレーションのロールバック中...")
    
    try:
        # ブロック関連テーブルを削除
        from sqlalchemy import text
        with db.engine.connect() as conn:
            conn.execute(text('DROP TABLE IF EXISTS article_blocks'))
            conn.execute(text('DROP TABLE IF EXISTS block_types'))
            conn.commit()
        
        # Articles テーブルから追加カラムを削除
        # SQLiteではカラム削除が制限されているため、テーブル再作成が必要
        print("注意: SQLiteではカラム削除が制限されています。")
        print("完全なロールバックには手動でデータベースファイルを復元してください。")
        
        print("✅ ロールバック完了")
        
    except Exception as e:
        print(f"❌ ロールバック中にエラーが発生しました: {e}")

def main():
    """メイン関数"""
    app = create_app()
    
    with app.app_context():
        if len(sys.argv) > 1 and sys.argv[1] == 'rollback':
            rollback_migration()
        else:
            migrate_database()

if __name__ == '__main__':
    main()