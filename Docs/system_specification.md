# ミニブログシステム完全仕様書

**最終更新日**: 2025年7月7日  
**バージョン**: 2.0.0  
**対応環境**: MySQL 9.3.0 + SQLAlchemy 2.0 + Flask 2.x

## 📋 システム概要

### プロジェクト名
高機能Markdownブログシステム (Mini Blog System)

### 技術スタック
- **Backend**: Python 3.10, Flask 2.x, SQLAlchemy 2.0.41
- **Database**: MySQL 9.3.0 (PyMySQL 1.1.1)
- **Frontend**: HTML5, CSS3, Bootstrap 5, JavaScript ES6+
- **Security**: Flask-Login, TOTP/2FA, Flask-WTF CSRF
- **Content**: Markdown processing, Bleach sanitization
- **Image**: PIL/Pillow, Cropper.js

### アーキテクチャ
- **MVC Pattern**: Flask Blueprint による機能分割
- **ORM**: SQLAlchemy 2.0 完全対応
- **Service Layer**: CRUD操作の統一化
- **Template Engine**: Jinja2
- **Session Management**: Flask-Session
- **Migration**: Flask-Migrate (Alembic)

## 🎯 機能仕様

### 1. 認証・セキュリティシステム

#### 1.1 基本認証
- **ユーザー登録**: メール・パスワード・基本情報
- **ログイン**: メール・パスワード認証
- **パスワードリセット**: メール送信によるトークンベース
- **セッション管理**: 自動ログアウト・記憶機能

#### 1.2 2段階認証 (2FA)
- **TOTP対応**: Google Authenticator / Authy 互換
- **QRコード生成**: 初回設定時の自動生成
- **バックアップコード**: 緊急時アクセス用
- **強制有効化**: 管理者権限には2FA必須

#### 1.3 権限管理
- **役割**: admin (管理者) / author (投稿者)
- **権限制御**: ルートレベルでの認証チェック
- **アクセス制御**: 機能別権限分離

#### 1.4 セキュリティ対策
- **CSRF保護**: 全フォームでトークン検証
- **XSS対策**: Bleach による HTML サニタイゼーション
- **SQLインジェクション対策**: SQLAlchemy ORM使用
- **セキュリティヘッダー**: CSP, X-Frame-Options等
- **ファイルアップロード制限**: 拡張子・サイズ・MIMEタイプ検証

### 2. コンテンツ管理システム

#### 2.1 記事管理
- **作成・編集**: 統一されたMarkdownエディタ
- **ステータス管理**: 公開 / 下書き
- **SEO対応**: メタタイトル・ディスクリプション・キーワード
- **スラッグ管理**: 自動生成・手動設定・重複チェック
- **公開日設定**: 即時・予約公開
- **アイキャッチ画像**: 16:9比率、自動リサイズ・トリミング

#### 2.2 Markdownエディタ
- **フルMarkdown対応**: 見出し・リスト・リンク・画像・コードブロック
- **リアルタイムプレビュー**: タブ切り替え式
- **ツールバー**: 直感的なMarkdown挿入
- **キーボードショートカット**: Ctrl+B/I/K等
- **SNS自動埋込**: URL貼り付けで自動変換
- **画像アップロード**: ドラッグ&ドロップ対応

#### 2.3 SNS自動埋込機能
- **対応プラットフォーム**: YouTube, X(Twitter), Instagram, Facebook, Threads
- **自動検出**: URL パターンマッチング
- **表示形式**: ネイティブ埋込 / OGPカード
- **フォールバック**: 制限時のカード表示

#### 2.4 カテゴリ管理
- **階層構造**: 親子関係による多階層対応
- **SEO対応**: スラッグ・メタタグ・OGP画像
- **自動スラッグ生成**: 名前からの自動変換
- **記事関連付け**: 多対多関係

### 3. ユーザー管理システム

#### 3.1 プロフィール管理
- **基本情報**: 名前・ハンドル名・メール・役割
- **詳細情報**: 紹介文・出身地・誕生日
- **SNSアカウント**: X, Facebook, Instagram, Threads, YouTube
- **通知設定**: 記事公開・コメント通知のON/OFF

#### 3.2 公開プロフィール
- **プロフィールページ**: 美しいレイアウトでの情報表示
- **投稿記事一覧**: ユーザー別記事表示
- **SNSリンク**: 設定済みアカウントへのリンク

### 4. コメントシステム

#### 4.1 コメント機能
- **投稿**: 記事詳細ページでの投稿
- **承認制**: 管理者承認後の公開
- **返信機能**: 階層コメント対応
- **投稿者情報**: 名前・メール・投稿日時

#### 4.2 コメント管理
- **一括操作**: 承認・拒否・削除
- **フィルタリング**: 承認済み・承認待ち
- **統計**: コメント数・承認率

### 5. 管理画面システム

#### 5.1 ダッシュボード
- **統計情報**: ユーザー・記事・カテゴリ・コメント数
- **月次統計**: 今月の作成数
- **承認待ち**: 未承認コメント数
- **最新記事**: 最近の投稿一覧

#### 5.2 記事管理
- **一覧表示**: ページネーション対応
- **ステータス管理**: 公開/下書き一括変更
- **検索・フィルタ**: タイトル・カテゴリ・ステータス別
- **統計**: 公開・下書き・今月の記事数

#### 5.3 カテゴリ管理
- **階層表示**: 親子関係の視覚化
- **記事数表示**: カテゴリ別記事数
- **OGP画像管理**: カテゴリ専用画像設定

#### 5.4 ユーザー管理
- **権限管理**: admin/author切り替え
- **2FA設定**: 強制有効化・リセット
- **削除保護**: admin数チェック

#### 5.5 サイト設定
- **基本設定**: サイト名・説明・キーワード
- **SEO設定**: メタタグ・OGP設定
- **画像設定**: ロゴ・ファビコン

### 6. 画像管理システム

#### 6.1 アップロード機能
- **ドラッグ&ドロップ**: 直感的なファイル選択
- **形式制限**: JPEG, PNG, GIF, WebP
- **サイズ制限**: 最大10MB
- **自動リサイズ**: 設定可能な最大サイズ

#### 6.2 画像処理
- **リアルタイムトリミング**: Cropper.js統合
- **アスペクト比固定**: 16:9 (アイキャッチ), 1:1 (OGP)等
- **自動最適化**: JPEG品質・ファイルサイズ最適化
- **Alt属性**: アクセシビリティ対応

#### 6.3 画像管理
- **一覧表示**: グリッド・リスト表示切り替え
- **検索機能**: ファイル名・Alt属性での検索
- **統計情報**: 総容量・ファイル数

## 🗄️ データベース仕様

### 主要テーブル

#### users (ユーザー)
- **主キー**: id (INTEGER)
- **認証**: email (UNIQUE), password_hash, role
- **プロフィール**: name, handle_name, bio, location, birthday
- **SNS**: x_username, facebook_url, instagram_url, threads_url, youtube_url
- **2FA**: totp_secret, totp_enabled, backup_codes
- **設定**: notification_settings (JSON)
- **システム**: created_at, last_login, reset_token

#### articles (記事)
- **主キー**: id (INTEGER)
- **基本**: title, slug (UNIQUE), summary, body
- **SEO**: meta_title, meta_description, keywords, canonical_url
- **ステータス**: is_published, allow_comments
- **画像**: featured_image
- **関連**: author_id (FK), publication_date
- **システム**: created_at, updated_at

#### categories (カテゴリ)
- **主キー**: id (INTEGER)  
- **基本**: name, slug (UNIQUE), description
- **階層**: parent_id (Self FK)
- **SEO**: meta_title, meta_description, keywords
- **画像**: ogp_image
- **システム**: created_at, updated_at

#### comments (コメント)
- **主キー**: id (INTEGER)
- **基本**: content, author_name, author_email
- **関連**: article_id (FK), parent_id (Self FK)
- **管理**: is_approved
- **システム**: created_at, ip_address

#### article_categories (記事-カテゴリ関連)
- **複合主キー**: article_id (FK), category_id (FK)

#### site_settings (サイト設定)
- **主キー**: id (INTEGER)
- **設定**: key (UNIQUE), value, description
- **メタ**: setting_type, is_public
- **システム**: updated_at

#### uploaded_images (アップロード画像)
- **主キー**: id (INTEGER)
- **ファイル**: filename, file_path, file_size, mime_type
- **メタ**: alt_text, caption, description
- **関連**: uploader_id (FK)
- **システム**: upload_date, is_active

### リレーション
- **users → articles**: 1:N (author_id)
- **articles ↔ categories**: N:M (article_categories)
- **articles → comments**: 1:N (article_id)
- **comments → comments**: 1:N (parent_id, 返信)
- **categories → categories**: 1:N (parent_id, 階層)
- **users → uploaded_images**: 1:N (uploader_id)

## 🛣️ ルーティング仕様

### 公開ページ
- `GET /` - ホームページ (記事一覧)
- `GET /article/<slug>/` - 記事詳細
- `POST /add_comment/<int:article_id>` - コメント投稿
- `GET /category/<slug>/` - カテゴリページ
- `GET /profile/<handle_name>/` - ユーザープロフィール

### 認証
- `GET|POST /login/` - ログイン
- `GET|POST /register/` - ユーザー登録  
- `GET /logout/` - ログアウト
- `GET|POST /totp_setup/` - 2FA設定
- `GET|POST /totp_verify/` - 2FA認証
- `GET|POST /password_reset_request/` - パスワードリセット要求
- `GET|POST /password_reset/<token>/` - パスワードリセット

### 管理画面 (/admin)

#### ダッシュボード・基本
- `GET /admin/` - ダッシュボード
- `GET /admin/profile/` - プロフィール設定

#### 記事管理
- `GET /admin/articles/` - 記事一覧
- `GET|POST /admin/article/create/` - 記事作成
- `GET|POST /admin/article/edit/<int:article_id>/` - 記事編集
- `POST /admin/article/delete/<int:article_id>` - 記事削除
- `POST /admin/articles/bulk_action/` - 記事一括操作

#### カテゴリ管理
- `GET /admin/categories/` - カテゴリ一覧
- `GET|POST /admin/category/create/` - カテゴリ作成
- `GET|POST /admin/category/edit/<int:category_id>/` - カテゴリ編集
- `POST /admin/category/delete/<int:category_id>` - カテゴリ削除

#### ユーザー管理
- `GET /admin/users/` - ユーザー一覧
- `GET|POST /admin/user/create/` - ユーザー作成
- `GET|POST /admin/user/edit/<int:user_id>/` - ユーザー編集
- `POST /admin/user/delete/<int:user_id>` - ユーザー削除

#### コメント管理
- `GET /admin/comments/` - コメント一覧
- `POST /admin/comment/approve/<int:comment_id>` - コメント承認
- `POST /admin/comment/reject/<int:comment_id>` - コメント拒否
- `POST /admin/comment/delete/<int:comment_id>` - コメント削除
- `POST /admin/comments/bulk_action/` - コメント一括操作

#### 画像管理
- `GET /admin/images/` - 画像一覧
- `POST /admin/upload_image/` - 画像アップロード
- `GET /admin/images/gallery/` - 画像ギャラリー
- `POST /admin/image/delete/<int:image_id>` - 画像削除

#### サイト設定
- `GET|POST /admin/site_settings/` - サイト設定

#### API・アップロード
- `POST /admin/upload_featured_image/` - アイキャッチ画像アップロード
- `POST /admin/process_image/` - 画像処理
- `GET /admin/get_categories/` - カテゴリAPI

## 🔧 技術仕様

### SQLAlchemy 2.0対応
- **Query Pattern**: `db.session.execute(select(Model).where(...)).scalars()`
- **Boolean Comparison**: `Model.field.is_(True/False)`
- **NULL Comparison**: `Model.field.is_(None)`
- **Count Query**: `db.session.execute(select(func.count(Model.id))).scalar()`
- **Pagination**: `db.paginate(select(Model), page=1, per_page=10)`

### MySQL最適化
- **Connection**: PyMySQL 1.1.1 driver
- **Charset**: utf8mb4 (絵文字対応)
- **Engine**: InnoDB (トランザクション対応)
- **Indexes**: 主要フィールドにインデックス設定

### セキュリティ実装
- **CSRF Token**: Flask-WTF による自動トークン生成
- **Password Hash**: Werkzeug Security (pbkdf2:sha256)
- **Session**: Flask-Session (server-side storage)
- **File Upload**: 拡張子・MIMEタイプ・サイズ検証

### 環境設定
```bash
# .env ファイル
DATABASE_URL=mysql+pymysql://root:password@localhost/miniblog
SECRET_KEY=random_secret_key
FLASK_DEBUG=True/False
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your_email
MAIL_PASSWORD=your_password
```

## 📊 パフォーマンス仕様

### 応答時間目標
- **ページ読み込み**: < 2秒
- **画像アップロード**: < 5秒
- **検索処理**: < 1秒
- **ダッシュボード**: < 3秒

### 容量制限
- **画像ファイル**: 最大10MB
- **記事本文**: 制限なし (実用的には1MB程度)
- **データベース**: MySQL設定に依存
- **セッション**: 24時間

### 同時接続
- **開発環境**: 10-50ユーザー
- **本番環境**: 100-500ユーザー (設定により調整)

## 🚀 デプロイメント仕様

### 本番環境要件
- **Python**: 3.10+
- **MySQL**: 8.0+ (推奨: 9.0+)
- **Memory**: 最小2GB, 推奨4GB+
- **Storage**: 最小10GB, 推奨50GB+
- **WSGI Server**: Gunicorn / uWSGI

### AWS移行対応
- **RDS**: MySQL 8.0+ 完全対応
- **EC2**: t3.medium以上推奨
- **S3**: 画像ストレージ対応準備済み
- **Load Balancer**: ALB対応
- **Auto Scaling**: 水平スケール対応

## 🔄 バージョン管理

### 現在のバージョン: 2.0.0
- SQLAlchemy 2.0完全対応
- MySQL環境完全移行
- 全機能動作確認済み
- AWS移行準備完了

### 変更履歴
- **v1.0.0**: 初期リリース (SQLite)
- **v1.5.0**: MySQL移行・機能追加
- **v2.0.0**: SQLAlchemy 2.0完全対応

---

**文書作成日**: 2025年7月7日  
**最終更新**: 2025年7月7日  
**作成者**: Claude Code  
**承認者**: システム管理者