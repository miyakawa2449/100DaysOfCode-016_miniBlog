# MiniBlog

## 目次

- [概要](#概要)
- [デモ・スクリーンショット](#デモ・スクリーンショット)
- [主な機能](#主な機能)
- [技術スタック](#技術スタック)
- [クイックスタート](#クイックスタート)
- [詳細なインストール](#詳細なインストール)
- [使用方法](#使用方法)
- [詳細機能](#詳細機能)
- [開発者向け情報](#開発者向け情報)
- [トラブルシューティング](#トラブルシューティング)
- [本番運用](#本番運用)
- [コントリビューション](#コントリビューション)
- [ライセンス](#ライセンス)

## 概要

Flask を使用したシンプルなブログアプリケーションです。記事の作成・編集・削除、カテゴリ管理、ユーザー管理機能を提供します。

2段階認証（Google Authenticator）、画像管理、SEO対応など、実用的なブログに必要な機能を備えています。

現在はまだ、実装中です。

**最新テスト結果**: ✅ 全機能正常動作確認済み (2025年6月16日)  
**セキュリティレベル**: 🛡️ 高度 (2段階認証、CSRF保護完備)  
**本番準備状況**: ✅ 準備完了

## デモ・スクリーンショット

🌐 **Live Demo**: 準備中

![ホーム画面](docs/screenshots/home.png)
![記事編集画面](docs/screenshots/editor.png)
![管理画面](docs/screenshots/admin.png)

*スクリーンショットは準備中です*

## 主な機能

- **記事管理**: 作成、編集、削除、公開設定
- **カテゴリ管理**: 階層構造対応、画像設定
- **ユーザー管理**: 2段階認証、権限管理
- **画像管理**: アップロード、トリミング、圧縮
- **SEO対応**: メタタグ、構造化データ、OGP
- **レスポンシブデザイン**: モバイル対応

## 技術スタック

- **バックエンド**: Python 3.10+, Flask, SQLAlchemy
- **フロントエンド**: HTML5, CSS3, JavaScript, Bootstrap 4.5.2
- **データベース**: SQLite (開発用), PostgreSQL/MySQL (本番推奨)
- **認証**: Flask-Login, Google Authenticator (TOTP)
- **画像処理**: Pillow
- **その他**: Cropper.js (画像トリミング), Markdown対応

## クイックスタート

```bash
# 1. リポジトリクローン
git clone https://github.com/your-username/100DaysOfCode-016_miniBlog.git
cd 100DaysOfCode-016_miniBlog

# 2. 仮想環境作成・有効化
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 依存関係インストール
pip install -r requirements.txt

# 4. データベース初期化
python init_db.py

# 5. アプリ起動
python app.py
```

📱 ブラウザで `http://localhost:5000` にアクセス

## 詳細なインストール

### 前提条件

- Python 3.10 以上
- pip

### 手順

1. **リポジトリのクローン**:
   ```bash
   git clone https://github.com/your-username/100DaysOfCode-016_miniBlog.git
   cd 100DaysOfCode-016_miniBlog
   ```

2. **仮想環境の作成と有効化**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # または
   venv\Scripts\activate  # Windows
   ```

3. **依存関係のインストール**:
   ```bash
   pip install -r requirements.txt
   ```

4. **環境設定**:
   ```bash
   # .flaskenv ファイルを作成
   FLASK_APP=app.py
   FLASK_ENV=development
   SECRET_KEY=your-secret-key-here
   MAX_CONTENT_LENGTH=16777216  # 16MB
   ```

5. **データベースの初期化**:
   ```bash
   python init_db.py
   ```

6. **アプリケーションの起動**:
   ```bash
   python app.py
   ```

7. **ブラウザでアクセス**:
   http://localhost:5000

## 使用方法

### 初期設定

1. 管理者アカウントの作成（初回起動時）
2. カテゴリの設定
3. 記事の作成

### 記事の作成

1. 管理画面にログイン
2. 「記事管理」→「新規作成」
3. タイトル、内容、カテゴリを設定
4. 「公開」ボタンで記事を公開

### カテゴリ管理

1. 「カテゴリ管理」→「新規作成」
2. カテゴリ名、説明、親カテゴリを設定
3. アイキャッチ画像を設定（任意）

## 詳細機能

### ユーザ管理
- **Google Authenticator による2段階認証**
  - QRコードによる簡単設定
  - バックアップコード生成
- **権限管理** (管理者/投稿者)
- **プロフィールページ**
- **SNSアカウント連携表示**

### 記事管理
- **ブロック型エディタ** (テキスト/画像/SNS埋込/外部記事)
- **Markdownサポート**
- **アイキャッチ画像** (16:9, 800px)
- **SEO最適化** (メタキーワード、カノニカルURL、構造化データ)
- **公開設定** (公開/非公開/予約投稿)

### カテゴリ管理
- **階層構造対応** (親子関係)
- **カテゴリ別OGP画像設定**
- **画像トリミング機能** (Cropper.js使用)

### 画像管理
- **アップロード機能** (JPEG, PNG, GIF対応)
- **自動リサイズ・圧縮**
- **トリミング機能** (アスペクト比固定可能)
- **複数画像一括アップロード**

## 開発者向け情報

### テスト実行

```bash
# 基本テスト
python test_app.py

# 2段階認証テスト
python test_2fa_features.py

# 管理機能テスト
python debug_admin.py

# 包括的テスト
python complete_2fa_test.py
```

### 手動テスト
詳細な手動テストガイドは [MANUAL_TEST_STEPS.md](MANUAL_TEST_STEPS.md) を参照

### 主要なエンドポイント

#### 公開ページ
- `/` - ホーム（記事一覧）
- `/article/<slug>` - 記事詳細
- `/category/<slug>` - カテゴリページ
- `/archives` - アーカイブ
- `/search` - 検索

#### 管理画面
- `/admin/` - ダッシュボード
- `/admin/articles` - 記事管理
- `/admin/categories` - カテゴリ管理
- `/admin/users` - ユーザ管理
- `/admin/settings` - 設定

#### API エンドポイント
- `/api/articles` - 記事API
- `/api/categories` - カテゴリAPI
- `/api/upload` - 画像アップロードAPI

### データベース構造
詳細な仕様は [database_spec.md](database_spec.md) を参照

### コーディング規約
- PEP8準拠
- 関数・クラスにはDocstring必須
- TypeHint推奨

## トラブルシューティング

### よくある問題

**画像アップロードエラー**
```
Request Entity Too Large
```
→ `app.config['MAX_CONTENT_LENGTH']` を調整

**Cropper.jsが動作しない**
- ブラウザコンソールでJavaScriptエラーを確認
- CDNの `integrity` 属性を確認

**2段階認証が設定できない**
```bash
python complete_2fa_test.py
```
でテスト実行

**データベース接続エラー**
```bash
python init_db.py
```
でデータベースを再初期化

**静的ファイルが読み込まれない**
- `static/` ディレクトリの存在確認
- ブラウザキャッシュをクリア

### ログの確認

```bash
# アプリケーションログ
tail -f app.log

# Flaskデバッグログ
export FLASK_ENV=development
python app.py
```

## 本番運用

### セキュリティ設定
- **`SECRET_KEY`** を強固なランダム文字列に変更
- **HTTPS必須**
- **CSRFトークン有効化確認**
- **SQLインジェクション対策** (SQLAlchemy使用により基本的に安全)

### パフォーマンス最適化
- **データベース最適化** (インデックス設定)
- **画像最適化** (WebP形式対応)
- **CDN利用** (静的ファイル配信)

### バックアップ
- **データベースの定期バックアップ**
  ```bash
  # SQLiteの場合
  sqlite3 instance/miniblog.db ".backup backup_$(date +%Y%m%d).db"
  ```
- **`/uploads/images/` ディレクトリのバックアップ**
- **管理画面からのCSV/JSONエクスポート機能活用**

### モニタリング
- **アクセスログ監視**
- **エラーログ監視**
- **パフォーマンス監視**

### スケーリング
- **データベース分離** (PostgreSQL/MySQL移行)
- **ロードバランサ設定**
- **ファイルストレージ外部化** (AWS S3等)

## コントリビューション

プロジェクトへの貢献を歓迎します！

### 手順

1. このリポジトリをフォーク
2. フィーチャーブランチを作成 (`git checkout -b feature/AmazingFeature`)
3. 変更をコミット (`git commit -m 'Add some AmazingFeature'`)
4. ブランチにプッシュ (`git push origin feature/AmazingFeature`)
5. プルリクエストを作成

### 開発ガイドライン

- **テスト実行**: [MANUAL_TEST_STEPS.md](MANUAL_TEST_STEPS.md) に従ってテスト実行
- **コード規約**: PEP8準拠
- **コミットメッセージ**: 明確で分かりやすい説明
- **ドキュメント**: 新機能追加時は関連ドキュメントも更新

### 報告・提案

- **バグ報告**: GitHub Issues
- **機能提案**: GitHub Issues
- **質問**: GitHub Discussions

## ライセンス

このプロジェクトは MIT ライセンスの下で公開されています。

---

**100 Days of Code** プロジェクトの一環として作成されました。  
📧 お問い合わせ: [t.miyakawa244@gmail.com](mailto:t.miyakawa244@gmail.com)  
🐙 GitHub: [https://github.com/miyakawa2449](https://github.com/miyakawa2449)

---

**最終更新日**: 2025年6月16日