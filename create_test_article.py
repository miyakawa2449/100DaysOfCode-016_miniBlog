#!/usr/bin/env python3
"""SNS自動埋込機能のテスト記事を作成するスクリプト"""

from app import app, db
from models import Article, User, Category
from datetime import datetime

def create_test_article():
    with app.app_context():
        # 既存の記事があるかチェック
        existing = Article.query.filter_by(slug='sns-auto-embed-test').first()
        if existing:
            print(f'既存のテスト記事を更新します (ID: {existing.id})')
            article = existing
        else:
            print('新しいテスト記事を作成します')
            article = Article()
        
        # 管理者ユーザーを取得
        admin_user = User.query.filter_by(role='admin').first()
        if not admin_user:
            admin_user = User.query.first()  # 最初のユーザーを使用
            if not admin_user:
                print('ユーザーが見つかりません')
                return
        
        # テストカテゴリを取得または作成
        test_category = Category.query.filter_by(name='テスト').first()
        if not test_category:
            test_category = Category(
                name='テスト',
                slug='test',
                description='テスト用カテゴリ'
            )
            db.session.add(test_category)
            db.session.flush()
        
        # 記事内容を設定
        article.title = 'SNS自動埋込機能テスト'
        article.slug = 'sns-auto-embed-test'
        article.body = '''# SNS自動埋込機能のテスト記事

この記事では、Markdownテキストエリアに直接SNS URLを貼り付けて自動埋込される機能をテストします。

## YouTube動画の埋込

https://youtu.be/DNvGx4nAN2U

上記のURLが動画プレーヤーとして表示されるはずです。

## Twitter投稿の埋込

https://twitter.com/jack/status/20

Twitterの投稿が埋込表示されます。

## Instagram投稿の埋込

https://www.instagram.com/p/DKlxE3aRwrC/

Instagram投稿が埋込表示されます。

## Facebook動画の埋込

https://fb.watch/AtN7GyfvaS/

Facebook Watch動画が埋込表示されます。

## Threads投稿の埋込

https://www.threads.net/@zuck/post/C8FjcQBqm_k

Threadsの投稿がカスタムカード形式で表示されます。

## 通常のMarkdown書式との併用

**太字**や*斜体*、[リンク](https://example.com)なども正常に動作します。

- リスト項目1
- リスト項目2  
- リスト項目3

コードブロックも正常です：

```python
def hello():
    print("Hello, World!")
```

この記事で、SNS URLが正しく埋込表示に変換されることを確認してください。
'''
        article.summary = 'SNS URLの自動埋込機能をテストするための記事です。YouTube、Twitter、Instagram、Facebook、Threadsの各URLが正しく埋込表示されることを確認できます。'
        article.author_id = admin_user.id
        article.status = 'published'
        
        if not existing:
            article.created_at = datetime.utcnow()
            db.session.add(article)
        
        article.updated_at = datetime.utcnow()
        
        # カテゴリとの関連付け
        if test_category not in article.categories:
            article.categories.append(test_category)
        
        db.session.commit()
        
        print('SNS自動埋込テスト記事を作成/更新しました')
        print(f'記事URL: http://127.0.0.1:5001/article/{article.slug}/')
        print(f'管理画面での編集URL: http://127.0.0.1:5001/admin/articles/{article.id}/edit')
        print(f'管理画面記事一覧: http://127.0.0.1:5001/admin/articles/')

if __name__ == '__main__':
    create_test_article()