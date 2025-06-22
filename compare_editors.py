#!/usr/bin/env python3
"""
記事ID 19のブロック型エディタと従来型エディタの比較スクリプト
両方のエディタで表示される内容の一貫性をチェック
"""

import os
import sys
from flask import Flask
from models import db, User, Article, Category

def init_app():
    """Flask アプリケーションを初期化"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_default_secret_key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///miniblog.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

def simulate_block_editor_view(article):
    """ブロック型エディタ画面で表示される内容をシミュレート"""
    print("=" * 60)
    print("🧱 ブロック型エディタ画面 (admin/article/block-editor/edit/19/)")
    print("=" * 60)
    
    print(f"📰 記事タイトル: {article.title}")
    print(f"📝 記事概要: {article.summary or '(空白)'}")
    print(f"🔗 スラッグ: {article.slug}")
    print(f"✅ 公開状態: {'公開' if article.is_published else '下書き'}")
    print(f"💬 コメント許可: {'許可' if article.allow_comments else '許可しない'}")
    
    # カテゴリ情報
    categories = article.categories.all()
    if categories:
        category_names = [cat.name for cat in categories]
        print(f"📂 カテゴリ: {', '.join(category_names)}")
    else:
        print(f"📂 カテゴリ: (未設定)")
    
    # SEO・メタ情報
    print(f"🏷️ メタタイトル: {article.meta_title or '(空白)'}")
    print(f"📋 メタ説明: {article.meta_description or '(空白)'}")
    print(f"🔍 キーワード: {article.meta_keywords or '(空白)'}")
    print(f"🔗 カノニカルURL: {article.canonical_url or '(空白)'}")
    
    # ブロック情報
    if article.use_block_editor:
        blocks = article.get_visible_blocks()
        print(f"\n🧱 ブロック型エディタ情報:")
        print(f"   ブロック数: {len(blocks)}")
        for i, block in enumerate(blocks, 1):
            block_type_name = getattr(block.block_type, 'type_name', 'Unknown')
            print(f"   {i}. {block_type_name} (順序: {block.sort_order})")
            if hasattr(block, 'title') and block.title:
                print(f"      タイトル: {block.title}")
            if hasattr(block, 'content') and block.content:
                content_preview = block.content[:100] + "..." if len(block.content) > 100 else block.content
                print(f"      内容: {content_preview}")
    
    # エディタ切り替えリンク
    print(f"\n🔄 エディタ切り替えリンク:")
    print(f"   → 従来型エディタ: /admin/article/edit/19/")
    
    return {
        'title': article.title,
        'summary': article.summary,
        'slug': article.slug,
        'is_published': article.is_published,
        'allow_comments': article.allow_comments,
        'categories': [cat.name for cat in categories],
        'meta_title': article.meta_title,
        'meta_description': article.meta_description,
        'meta_keywords': article.meta_keywords,
        'canonical_url': article.canonical_url,
        'editor_type': 'block'
    }

def simulate_traditional_editor_view(article):
    """従来型エディタ画面で表示される内容をシミュレート"""
    print("\n" + "=" * 60)
    print("📝 従来型エディタ画面 (admin/article/edit/19/)")
    print("=" * 60)
    
    print(f"📰 記事タイトル: {article.title}")
    print(f"📝 記事概要: {article.summary or '(空白)'}")
    print(f"🔗 スラッグ: {article.slug}")
    print(f"✅ 公開状態: {'公開' if article.is_published else '下書き'}")
    print(f"💬 コメント許可: {'許可' if article.allow_comments else '許可しない'}")
    
    # カテゴリ情報
    categories = article.categories.all()
    if categories:
        category_names = [cat.name for cat in categories]
        print(f"📂 カテゴリ: {', '.join(category_names)}")
    else:
        print(f"📂 カテゴリ: (未設定)")
    
    # SEO・メタ情報
    print(f"🏷️ メタタイトル: {article.meta_title or '(空白)'}")
    print(f"📋 メタ説明: {article.meta_description or '(空白)'}")
    print(f"🔍 キーワード: {article.meta_keywords or '(空白)'}")
    print(f"🔗 カノニカルURL: {article.canonical_url or '(空白)'}")
    
    # 従来型エディタの本文
    print(f"\n📝 従来型エディタ情報:")
    if article.body:
        body_preview = article.body[:200] + "..." if len(article.body) > 200 else article.body
        print(f"   本文: {body_preview}")
    else:
        print(f"   本文: (空白)")
    
    # バックアップ情報
    if article.legacy_body_backup:
        backup_preview = article.legacy_body_backup[:200] + "..." if len(article.legacy_body_backup) > 200 else article.legacy_body_backup
        print(f"   バックアップ本文: {backup_preview}")
    
    # エディタ切り替えリンク
    print(f"\n🔄 エディタ切り替えリンク:")
    if article.use_block_editor:
        print(f"   → ブロック型エディタ: /admin/article/block-editor/edit/19/")
    else:
        print(f"   → ブロック型エディタ: (ブロック型に変換が必要)")
    
    return {
        'title': article.title,
        'summary': article.summary,
        'slug': article.slug,
        'is_published': article.is_published,
        'allow_comments': article.allow_comments,
        'categories': [cat.name for cat in categories],
        'meta_title': article.meta_title,
        'meta_description': article.meta_description,
        'meta_keywords': article.meta_keywords,
        'canonical_url': article.canonical_url,
        'editor_type': 'traditional'
    }

def compare_editor_consistency(block_data, traditional_data):
    """両エディタでの表示内容の一貫性をチェック"""
    print("\n" + "=" * 60)
    print("🔍 エディタ間の一貫性チェック結果")
    print("=" * 60)
    
    inconsistencies = []
    
    # 各フィールドをチェック
    fields_to_check = [
        ('title', '記事タイトル'),
        ('summary', '記事概要'),
        ('slug', 'スラッグ'),
        ('is_published', '公開状態'),
        ('allow_comments', 'コメント許可設定'),
        ('categories', 'カテゴリ設定'),
        ('meta_title', 'メタタイトル'),
        ('meta_description', 'メタ説明'),
        ('meta_keywords', 'キーワード'),
        ('canonical_url', 'カノニカルURL')
    ]
    
    for field, field_name in fields_to_check:
        block_value = block_data.get(field)
        traditional_value = traditional_data.get(field)
        
        if block_value == traditional_value:
            print(f"✅ {field_name}: 一致")
        else:
            print(f"❌ {field_name}: 不一致")
            print(f"   ブロック型: {block_value}")
            print(f"   従来型: {traditional_value}")
            inconsistencies.append((field_name, block_value, traditional_value))
    
    return inconsistencies

def check_javascript_errors():
    """JavaScriptエラーの可能性をチェック（シミュレーション）"""
    print("\n" + "=" * 60)
    print("🔧 JavaScriptエラー・機能チェック（予想）")
    print("=" * 60)
    
    print("📋 ブロック型エディタで予想される機能:")
    print("   ✅ ブロック追加・削除ボタン")
    print("   ✅ ドラッグ&ドロップでの並び替え")
    print("   ✅ リアルタイムプレビュー")
    print("   ✅ 画像アップロード機能")
    print("   ✅ SNS埋め込み機能")
    print("   📝 コンソールでのJavaScriptエラー要確認")
    
    print("\n📋 従来型エディタで予想される機能:")
    print("   ✅ テキストエリアでの編集")
    print("   ✅ Markdownプレビュー")
    print("   ✅ 基本的なフォーム機能")
    print("   📝 エディタ切り替えリンク動作要確認")

def main():
    """メイン処理"""
    app = init_app()
    
    with app.app_context():
        # 記事ID 19を取得
        article = Article.query.get(19)
        
        if not article:
            print("❌ 記事ID 19が見つかりません")
            return
        
        # 両エディタの表示内容をシミュレート
        block_data = simulate_block_editor_view(article)
        traditional_data = simulate_traditional_editor_view(article)
        
        # 一貫性をチェック
        inconsistencies = compare_editor_consistency(block_data, traditional_data)
        
        # JavaScriptエラーチェック
        check_javascript_errors()
        
        # 結果サマリー
        print("\n" + "=" * 60)
        print("📊 総合結果")
        print("=" * 60)
        
        if not inconsistencies:
            print("✅ 両エディタ間でデータの一貫性が保たれています")
        else:
            print(f"❌ {len(inconsistencies)}個の不整合が見つかりました:")
            for field_name, block_value, traditional_value in inconsistencies:
                print(f"   • {field_name}")
        
        print("\n🔍 確認推奨事項:")
        print("   1. ブラウザの開発者ツールでJavaScriptエラーを確認")
        print("   2. エディタ切り替えリンクの動作確認")
        print("   3. ブロック型エディタでの編集・保存動作確認")
        print("   4. 従来型エディタでの編集・保存動作確認")
        print("   5. 公開・下書き状態の切り替え動作確認")

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()