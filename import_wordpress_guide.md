# WordPress インポート ガイド

## 📋 概要

WordPressサイトの記事、カテゴリ、画像を miniBlog システムに一括インポートするツールです。

## 🛠️ 事前準備

### 1. WordPress データのエクスポート

1. WordPressの管理画面にログイン
2. **ツール** → **エクスポート** を選択
3. **すべてのコンテンツ** を選択
4. **エクスポートファイルをダウンロード** をクリック
5. XMLファイル（例：`wordpress.2024-06-22.xml`）をダウンロード

### 2. 必要なPythonパッケージのインストール

```bash
pip install requests pillow
```

### 3. 著者ユーザーの確認

インポートした記事に設定する著者のユーザーIDを確認：

```bash
# 管理者ユーザーのIDを確認
python -c "
from app import app
from models import User, db
with app.app_context():
    users = User.query.all()
    for user in users:
        print(f'ID: {user.id}, Name: {user.name}, Email: {user.email}, Role: {user.role}')
"
```

## 🚀 インポート実行

### 基本的な使用方法

```bash
# ドライラン（実際にはインポートしない）
python wordpress_importer.py --xml wordpress.2024-06-22.xml --author-id 1 --dry-run

# 実際のインポート
python wordpress_importer.py --xml wordpress.2024-06-22.xml --author-id 1
```

### パラメータ説明

- `--xml`: WordPressエクスポートXMLファイルのパス
- `--author-id`: 記事の著者として設定するユーザーID
- `--dry-run`: テスト実行（実際にはデータベースに保存しない）

## 📊 インポート対象

### ✅ インポートされるデータ

1. **カテゴリ**
   - カテゴリ名
   - スラッグ
   - 説明文
   - 親子関係

2. **記事**
   - タイトル
   - 本文
   - 要約
   - スラッグ
   - 公開日時
   - カテゴリ関連付け
   - アイキャッチ画像

3. **画像**
   - アイキャッチ画像の自動ダウンロード
   - 自動リサイズ（1200x800以下）
   - 最適化保存

### ❌ インポートされないデータ

- コメント
- 固定ページ
- メニュー設定
- ウィジェット
- テーマ設定
- プラグイン設定
- ユーザー情報

## 🔍 データマッピング

### WordPress → miniBlog

| WordPress | miniBlog | 備考 |
|-----------|----------|------|
| post_title | Article.title | HTMLタグ除去 |
| post_content | Article.content | HTMLエスケープ解除 |
| post_excerpt | Article.summary | 要約として設定 |
| post_name | Article.slug | URL用スラッグ |
| post_date | Article.published_at | 公開日時 |
| categories | Article.categories | 多対多関連 |
| featured_image | Article.featured_image | 自動ダウンロード |
| cat_name | Category.name | カテゴリ名 |
| category_nicename | Category.slug | カテゴリスラッグ |

## 🎯 実行例

### 1. ドライラン実行

```bash
$ python wordpress_importer.py --xml my-blog-export.xml --author-id 1 --dry-run

🚀 WordPress インポート開始
📁 XMLファイル: my-blog-export.xml
👤 著者ID: 1
🧪 ドライラン: 有効
--------------------------------------------------
✅ XML ファイルを読み込みました: my-blog-export.xml
📁 カテゴリを 5 個抽出しました
📝 記事を 25 個抽出しました
🔍 [DRY RUN] カテゴリ作成: プログラミング
🔍 [DRY RUN] カテゴリ作成: Python
🔍 [DRY RUN] 記事作成: FlaskでWebアプリを作ろう
...
```

### 2. 実際のインポート

```bash
$ python wordpress_importer.py --xml my-blog-export.xml --author-id 1

🚀 WordPress インポート開始
📁 XMLファイル: my-blog-export.xml
👤 著者: 管理者 (admin@example.com)
🧪 ドライラン: 無効
--------------------------------------------------
✅ XML ファイルを読み込みました: my-blog-export.xml
📁 カテゴリを 5 個抽出しました
📝 記事を 25 個抽出しました
✅ カテゴリ作成: プログラミング
✅ カテゴリ作成: Python
✅ 記事作成: FlaskでWebアプリを作ろう
✅ 記事作成: データベース設計の基礎
...

==================================================
📊 インポート結果
==================================================
✅ カテゴリ: 5 個
✅ 記事: 23 個
✅ 画像: 15 個

⚠️  エラー (2 件):
   - 画像ダウンロード失敗: https://old-site.com/wp-content/uploads/broken-image.jpg
   - 記事作成失敗: 重複タイトル記事 - UNIQUE constraint failed

🎉 インポート完了!
```

## ⚠️ 注意事項

### 1. データの重複

- 同じスラッグの記事・カテゴリは自動的にスキップされます
- 既存データは上書きされません

### 2. 画像の処理

- 外部サイトの画像は自動ダウンロードされます
- ダウンロードに失敗した画像は記録されますが、記事のインポートは継続されます
- 画像は `static/uploads/articles/` に保存されます

### 3. 文字エンコーディング

- HTMLエンティティは自動的にデコードされます
- 特殊文字や絵文字も正しく処理されます

### 4. カテゴリの階層

- 親子関係のあるカテゴリは正しく処理されます
- 親カテゴリが存在しない場合は、子カテゴリのみが作成されます

## 🔧 トラブルシューティング

### よくあるエラーと対処法

#### 1. `FileNotFoundError: [Errno 2] No such file or directory`

**原因**: XMLファイルのパスが間違っている

**対処法**: 
```bash
# ファイルの存在確認
ls -la *.xml

# 正しいパスを指定
python wordpress_importer.py --xml ./wordpress.2024-06-22.xml --author-id 1
```

#### 2. `著者ID X のユーザーが見つかりません`

**原因**: 指定したユーザーIDが存在しない

**対処法**:
```bash
# ユーザー一覧を確認
python -c "
from app import app
from models import User
with app.app_context():
    users = User.query.all()
    for user in users:
        print(f'ID: {user.id}, Name: {user.name}')
"
```

#### 3. `xml.etree.ElementTree.ParseError`

**原因**: XMLファイルが破損しているか、形式が正しくない

**対処法**:
- WordPressから再度エクスポートを実行
- ファイルサイズが0でないことを確認
- テキストエディタでXMLファイルの先頭を確認

#### 4. `画像ダウンロードエラー`

**原因**: 画像URLにアクセスできない、または画像が削除されている

**対処法**:
- エラーメッセージを確認して、必要に応じて手動で画像を修正
- インポート自体は継続されるため、後で個別に対応可能

## 📝 インポート後の確認事項

### 1. データベースの確認

```bash
# 記事数の確認
python -c "
from app import app
from models import Article, Category, db
with app.app_context():
    print(f'記事数: {Article.query.count()}')
    print(f'カテゴリ数: {Category.query.count()}')
"
```

### 2. 管理画面での確認

1. ブラウザで管理画面にアクセス
2. 記事一覧でインポートされた記事を確認
3. カテゴリ一覧で階層構造を確認
4. 画像の表示を確認

### 3. 公開ページでの確認

1. ホームページで記事一覧を確認
2. 個別記事ページで内容を確認
3. カテゴリページで関連付けを確認

## 🔄 再インポート

同じXMLファイルを再度インポートしても、既存のデータは重複しません。

- 既存のスラッグと同じ記事・カテゴリはスキップされます
- 新しいデータのみが追加されます

## 📞 サポート

インポートで問題が発生した場合は、以下の情報を含めてお問い合わせください：

1. 実行したコマンド
2. エラーメッセージの全文
3. XMLファイルのサイズ
4. WordPressのバージョン
5. 記事数・カテゴリ数の概数

---

**🎉 これで WordPress から miniBlog への移行が完了です！**