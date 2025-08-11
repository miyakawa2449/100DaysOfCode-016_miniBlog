#!/usr/bin/env python3
"""
WordPress インポーター
WordPressのエクスポートXMLから記事、カテゴリ、メディアを miniBlog にインポートする

使用方法:
1. WordPressの管理画面から「ツール」→「エクスポート」でXMLファイルを取得
2. python wordpress_importer.py --xml wordpress_export.xml --author-id 1
"""

import xml.etree.ElementTree as ET
import re
import os
import sys
import argparse
import requests
from datetime import datetime
from urllib.parse import urlparse, urljoin
import html
from PIL import Image
import time

# Flask アプリケーションの初期化
from app import app, db
from models import User, Article, Category

# WordPress XML の名前空間定義
WP_NAMESPACES = {
    'wp': 'http://wordpress.org/export/1.2/',
    'dc': 'http://purl.org/dc/elements/1.1/',
    'content': 'http://purl.org/rss/1.0/modules/content/',
    'excerpt': 'http://wordpress.org/export/1.2/excerpt/',
    'wfw': 'http://wellformedweb.org/CommentAPI/',
    'category': 'http://wordpress.org/export/1.2/category/'
}

class WordPressImporter:
    """WordPress インポーター"""
    
    def __init__(self, xml_file, author_id, dry_run=False):
        self.xml_file = xml_file
        self.author_id = author_id
        self.dry_run = dry_run
        self.stats = {
            'categories_imported': 0,
            'posts_imported': 0,
            'images_downloaded': 0,
            'errors': []
        }
        
    def parse_xml(self):
        """WordPress XML を解析"""
        try:
            tree = ET.parse(self.xml_file)
            self.root = tree.getroot()
            print(f"✅ XML ファイルを読み込みました: {self.xml_file}")
            return True
        except ET.ParseError as e:
            print(f"❌ XML解析エラー: {e}")
            return False
        except FileNotFoundError:
            print(f"❌ ファイルが見つかりません: {self.xml_file}")
            return False
    
    def extract_categories(self):
        """カテゴリを抽出"""
        categories = []
        
        # wp:category 要素から抽出
        for cat_elem in self.root.findall('.//wp:category', WP_NAMESPACES):
            term_id = cat_elem.find('wp:term_id', WP_NAMESPACES)
            category_nicename = cat_elem.find('wp:category_nicename', WP_NAMESPACES)
            cat_name = cat_elem.find('wp:cat_name', WP_NAMESPACES)
            category_parent = cat_elem.find('wp:category_parent', WP_NAMESPACES)
            category_description = cat_elem.find('wp:category_description', WP_NAMESPACES)
            
            if cat_name is not None and cat_name.text:
                category_data = {
                    'wp_id': int(term_id.text) if term_id is not None else None,
                    'name': html.unescape(cat_name.text),
                    'slug': category_nicename.text if category_nicename is not None else self.generate_slug(cat_name.text),
                    'parent_slug': category_parent.text if category_parent is not None and category_parent.text else None,
                    'description': html.unescape(category_description.text) if category_description is not None and category_description.text else ''
                }
                categories.append(category_data)
        
        print(f"📁 カテゴリを {len(categories)} 個抽出しました")
        return categories
    
    def extract_posts(self):
        """記事を抽出"""
        posts = []
        
        for item in self.root.findall('.//item'):
            post_type = item.find('wp:post_type', WP_NAMESPACES)
            post_status = item.find('wp:status', WP_NAMESPACES)
            
            # 記事のみを対象（固定ページやその他の投稿タイプは除外）
            if (post_type is not None and post_type.text == 'post' and 
                post_status is not None and post_status.text == 'publish'):
                
                title = item.find('title')
                link = item.find('link')
                pub_date = item.find('pubDate')
                description = item.find('description')
                content = item.find('content:encoded', WP_NAMESPACES)
                excerpt = item.find('excerpt:encoded', WP_NAMESPACES)
                post_name = item.find('wp:post_name', WP_NAMESPACES)
                post_date = item.find('wp:post_date', WP_NAMESPACES)
                
                # カテゴリ抽出
                categories = []
                for cat in item.findall('category[@domain="category"]'):
                    if cat.text:
                        categories.append(cat.text)
                
                # アイキャッチ画像の抽出
                featured_image = self.extract_featured_image(content.text if content is not None else '')
                
                post_data = {
                    'title': html.unescape(title.text) if title is not None and title.text else 'Untitled',
                    'slug': post_name.text if post_name is not None else self.generate_slug(title.text if title is not None else 'untitled'),
                    'content': html.unescape(content.text) if content is not None and content.text else '',
                    'summary': html.unescape(excerpt.text) if excerpt is not None and excerpt.text else '',
                    'description': html.unescape(description.text) if description is not None and description.text else '',
                    'published_at': self.parse_wp_date(post_date.text if post_date is not None else pub_date.text if pub_date is not None else ''),
                    'categories': categories,
                    'featured_image': featured_image,
                    'wp_link': link.text if link is not None else ''
                }
                posts.append(post_data)
        
        print(f"📝 記事を {len(posts)} 個抽出しました")
        return posts
    
    def extract_featured_image(self, content):
        """記事内容からアイキャッチ画像を抽出"""
        # 最初の画像を検索
        img_pattern = r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>'
        match = re.search(img_pattern, content, re.IGNORECASE)
        if match:
            return match.group(1)
        return None
    
    def generate_slug(self, text):
        """タイトルからスラッグを生成"""
        if not text:
            return 'untitled'
        
        # HTMLタグを除去
        text = re.sub(r'<[^>]+>', '', text)
        # 英数字以外を - に置換
        slug = re.sub(r'[^\w\s-]', '', text.lower())
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug.strip('-')[:50]  # 50文字制限
    
    def parse_wp_date(self, date_str):
        """WordPress の日付文字列を datetime に変換"""
        if not date_str:
            return datetime.now()
        
        try:
            # WordPress の日付形式: YYYY-MM-DD HH:MM:SS
            return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            try:
                # RSS の日付形式: Mon, 01 Jan 2024 12:00:00 +0000
                return datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %z').replace(tzinfo=None)
            except ValueError:
                print(f"⚠️ 日付の解析に失敗: {date_str}")
                return datetime.now()
    
    def download_image(self, image_url, article_slug):
        """画像をダウンロードして保存"""
        if not image_url or self.dry_run:
            return None
        
        try:
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            
            # ファイル名生成
            parsed_url = urlparse(image_url)
            original_filename = os.path.basename(parsed_url.path)
            if not original_filename:
                original_filename = 'image.jpg'
            
            # 拡張子確認
            _, ext = os.path.splitext(original_filename)
            if ext.lower() not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                ext = '.jpg'
            
            timestamp = int(time.time())
            filename = f"wp_import_{article_slug}_{timestamp}{ext}"
            
            # 保存先ディレクトリ
            upload_dir = os.path.join('static', 'uploads', 'articles')
            os.makedirs(upload_dir, exist_ok=True)
            
            file_path = os.path.join(upload_dir, filename)
            
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            # 画像リサイズ（オプション）
            try:
                with Image.open(file_path) as img:
                    if img.width > 1200 or img.height > 800:
                        img.thumbnail((1200, 800), Image.Resampling.LANCZOS)
                        img.save(file_path, optimize=True, quality=85)
            except Exception as e:
                print(f"⚠️ 画像リサイズエラー: {e}")
            
            self.stats['images_downloaded'] += 1
            return os.path.join('uploads', 'articles', filename)  # 相対パス
            
        except Exception as e:
            print(f"⚠️ 画像ダウンロードエラー ({image_url}): {e}")
            self.stats['errors'].append(f"画像ダウンロード失敗: {image_url}")
            return None
    
    def import_categories(self, categories):
        """カテゴリをインポート"""
        imported_categories = {}
        
        with app.app_context():
            # 親カテゴリから順番にインポート
            for category_data in sorted(categories, key=lambda x: x['parent_slug'] is None, reverse=True):
                try:
                    # 既存チェック（SQLAlchemy 2.0対応）- slug と name の両方でチェック（大文字小文字区別なし）
                    from sqlalchemy import select, or_, func
                    existing = db.session.execute(
                        select(Category).where(
                            or_(Category.slug == category_data['slug'], 
                                Category.name == category_data['name'],
                                func.lower(Category.name) == category_data['name'].lower())
                        )
                    ).scalar_one_or_none()
                    if existing:
                        print(f"⏭️  カテゴリ '{category_data['name']}' は既存 '{existing.name}' と類似のためスキップ")
                        imported_categories[category_data['slug']] = existing
                        continue
                    
                    if self.dry_run:
                        print(f"🔍 [DRY RUN] カテゴリ作成: {category_data['name']}")
                        continue
                    
                    # 親カテゴリ設定
                    parent_id = None
                    if category_data['parent_slug'] and category_data['parent_slug'] in imported_categories:
                        parent_id = imported_categories[category_data['parent_slug']].id
                    
                    # カテゴリ作成
                    category = Category(
                        name=category_data['name'],
                        slug=category_data['slug'],
                        description=category_data['description'],
                        parent_id=parent_id
                    )
                    
                    db.session.add(category)
                    db.session.commit()
                    
                    imported_categories[category_data['slug']] = category
                    self.stats['categories_imported'] += 1
                    print(f"✅ カテゴリ作成: {category_data['name']}")
                    
                except Exception as e:
                    print(f"❌ カテゴリ作成エラー ({category_data['name']}): {e}")
                    self.stats['errors'].append(f"カテゴリ作成失敗: {category_data['name']} - {e}")
                    db.session.rollback()
        
        return imported_categories
    
    def import_posts(self, posts, imported_categories):
        """記事をインポート"""
        from sqlalchemy import select
        with app.app_context():
            for post_data in posts:
                try:
                    # 既存チェック（SQLAlchemy 2.0対応）
                    existing = db.session.execute(
                        select(Article).where(Article.slug == post_data['slug'])
                    ).scalar_one_or_none()
                    if existing:
                        print(f"⏭️  記事 '{post_data['title']}' は既存のためスキップ")
                        continue
                    
                    if self.dry_run:
                        print(f"🔍 [DRY RUN] 記事作成: {post_data['title']}")
                        continue
                    
                    # アイキャッチ画像のダウンロード
                    featured_image_path = None
                    if post_data['featured_image']:
                        featured_image_path = self.download_image(post_data['featured_image'], post_data['slug'])
                    
                    # 記事作成（元記事の日付を使用）
                    publish_date = post_data['published_at']
                    article = Article(
                        title=post_data['title'],
                        slug=post_data['slug'],
                        body=post_data['content'],
                        summary=post_data['summary'],
                        meta_description=post_data['description'],
                        featured_image=featured_image_path,
                        is_published=True,
                        published_at=publish_date,
                        created_at=publish_date,  # 元記事の日付を作成日にも設定
                        updated_at=publish_date,  # 元記事の日付を更新日にも設定
                        author_id=self.author_id
                    )
                    
                    db.session.add(article)
                    db.session.flush()  # IDを取得
                    
                    # カテゴリ関連付け
                    for category_name in post_data['categories']:
                        category = None
                        # スラッグで検索
                        category_slug = self.generate_slug(category_name)
                        if category_slug in imported_categories:
                            category = imported_categories[category_slug]
                        else:
                            # 名前で検索（SQLAlchemy 2.0対応）
                            category = db.session.execute(
                                select(Category).where(Category.name == category_name)
                            ).scalar_one_or_none()
                        
                        if category:
                            # 多対多関係の追加（article_categoriesテーブル使用）
                            article.categories.append(category)
                    
                    db.session.commit()
                    self.stats['posts_imported'] += 1
                    print(f"✅ 記事作成: {post_data['title']}")
                    
                except Exception as e:
                    print(f"❌ 記事作成エラー ({post_data['title']}): {e}")
                    self.stats['errors'].append(f"記事作成失敗: {post_data['title']} - {e}")
                    db.session.rollback()
    
    def run(self):
        """インポート実行"""
        print("🚀 WordPress インポート開始")
        print(f"📁 XMLファイル: {self.xml_file}")
        print(f"👤 著者ID: {self.author_id}")
        print(f"🧪 ドライラン: {'有効' if self.dry_run else '無効'}")
        print("-" * 50)
        
        # XML解析
        if not self.parse_xml():
            return False
        
        # データ抽出
        categories = self.extract_categories()
        posts = self.extract_posts()
        
        # インポート実行
        imported_categories = self.import_categories(categories)
        self.import_posts(posts, imported_categories)
        
        # 結果表示
        print("\n" + "=" * 50)
        print("📊 インポート結果")
        print("=" * 50)
        print(f"✅ カテゴリ: {self.stats['categories_imported']} 個")
        print(f"✅ 記事: {self.stats['posts_imported']} 個")
        print(f"✅ 画像: {self.stats['images_downloaded']} 個")
        
        if self.stats['errors']:
            print(f"\n⚠️  エラー ({len(self.stats['errors'])} 件):")
            for error in self.stats['errors'][:10]:  # 最初の10件のみ表示
                print(f"   - {error}")
            if len(self.stats['errors']) > 10:
                print(f"   ... 他 {len(self.stats['errors']) - 10} 件")
        
        print("\n🎉 インポート完了!")
        return True

def main():
    parser = argparse.ArgumentParser(description='WordPress インポーター')
    parser.add_argument('--xml', required=True, help='WordPress エクスポート XML ファイル')
    parser.add_argument('--author-id', type=int, required=True, help='記事の著者ユーザーID')
    parser.add_argument('--dry-run', action='store_true', help='ドライラン（実際にはインポートしない）')
    
    args = parser.parse_args()
    
    # 著者存在チェック
    with app.app_context():
        author = db.session.get(User, args.author_id)
        if not author:
            print(f"❌ 著者ID {args.author_id} のユーザーが見つかりません")
            sys.exit(1)
        print(f"👤 著者: {author.name} ({author.email})")
    
    # インポート実行
    importer = WordPressImporter(args.xml, args.author_id, args.dry_run)
    success = importer.run()
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()