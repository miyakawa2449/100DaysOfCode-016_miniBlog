# ルーティング仕様書

**最終更新日**: 2025年7月7日  
**対応システム**: Mini Blog System v2.0.0  
**Framework**: Flask 2.x + Blueprint

## 📋 ルーティング概要

### Blueprint構成
- **Main App** (`app.py`): 公開ページ・認証
- **Admin Blueprint** (`admin.py`): 管理画面 (`/admin` prefix)

### 認証レベル
- **Public**: 誰でもアクセス可能
- **Auth Required**: ログイン必須
- **Admin Required**: 管理者権限必須 + 2FA認証

## 🌐 公開ページルート

### ホーム・記事表示

#### `GET /`
- **機能**: ホームページ (記事一覧)
- **認証**: Public
- **処理**: 公開済み記事を新着順で表示
- **テンプレート**: `home.html`
- **SQLAlchemy**: `select(Article).where(Article.is_published.is_(True))`

#### `GET /article/<slug>/`
- **機能**: 記事詳細表示
- **認証**: Public (下書きは管理者のみ)
- **パラメータ**: `slug` (記事スラッグ)
- **処理**: 
  - 記事取得・404チェック
  - コメント許可時は承認済みコメント取得
  - 下書きの場合は管理者権限チェック
- **テンプレート**: `article_detail.html`
- **関連機能**: コメント表示・返信表示

#### `GET /category/<slug>/`
- **機能**: カテゴリページ
- **認証**: Public
- **パラメータ**: `slug` (カテゴリスラッグ)
- **処理**: カテゴリ記事をページネーション表示
- **テンプレート**: `category_page.html`

#### `GET /profile/<handle_name>/`
- **機能**: ユーザープロフィールページ
- **認証**: Public
- **パラメータ**: `handle_name` (ユーザーハンドル名 or name)
- **処理**: ユーザー情報・公開記事一覧表示
- **テンプレート**: `profile.html`

### コメント機能

#### `POST /add_comment/<int:article_id>`
- **機能**: コメント投稿
- **認証**: Public
- **パラメータ**: `article_id` (記事ID)
- **フォームデータ**: 
  - `author_name` (投稿者名)
  - `author_email` (メールアドレス)
  - `content` (コメント内容)
  - `parent_id` (返信先コメントID, optional)
- **処理**: 
  - 記事存在チェック
  - コメント許可チェック
  - 承認待ちとして保存
- **CSRF**: Required
- **リダイレクト**: 記事詳細ページ

## 🔐 認証ルート

### ログイン・ログアウト

#### `GET|POST /login/`
- **機能**: ログイン
- **認証**: Public
- **GET処理**: ログインフォーム表示
- **POST処理**: 
  - メール・パスワード認証
  - 2FA有効時はTOTP画面へリダイレクト
  - 無効時は直接ログイン完了
- **フォーム**: `LoginForm` (email, password)
- **テンプレート**: `login.html`
- **リダイレクト**: ダッシュボードまたはTOTP認証

#### `GET /logout/`
- **機能**: ログアウト
- **認証**: Auth Required
- **処理**: セッション削除・ログアウト
- **リダイレクト**: ホームページ

### 2段階認証

#### `GET|POST /totp_setup/`
- **機能**: 2FA初期設定
- **認証**: Auth Required
- **GET処理**: QRコード生成・表示
- **POST処理**: TOTP検証・有効化
- **フォーム**: `TOTPSetupForm` (totp_code)
- **テンプレート**: `totp_setup.html`

#### `GET|POST /totp_verify/`
- **機能**: 2FA認証
- **認証**: Pre-Auth (temp_user_id in session)
- **処理**: TOTP コード検証・ログイン完了
- **フォーム**: `TOTPVerificationForm` (totp_code)
- **テンプレート**: `totp_verify.html`

### パスワードリセット

#### `GET|POST /password_reset_request/`
- **機能**: パスワードリセット要求
- **認証**: Public
- **処理**: メールアドレス確認・リセットメール送信
- **フォーム**: `PasswordResetRequestForm` (email)
- **テンプレート**: `password_reset_request.html`

#### `GET|POST /password_reset/<token>/`
- **機能**: パスワードリセット実行
- **認証**: Public (valid token required)
- **パラメータ**: `token` (リセットトークン)
- **処理**: トークン検証・新パスワード設定
- **フォーム**: `PasswordResetForm` (password, confirm_password)
- **テンプレート**: `password_reset.html`

## 👑 管理画面ルート (`/admin`)

### ダッシュボード

#### `GET /admin/`
- **機能**: 管理者ダッシュボード
- **認証**: Admin Required
- **処理**: 
  - 基本統計 (ユーザー・記事・カテゴリ・コメント数)
  - 月次統計 (今月の作成数)
  - 承認待ちコメント数
  - 最新記事一覧
- **テンプレート**: `admin/dashboard.html`
- **データ**: `stats`, `monthly_stats`, `recent_data`

### プロフィール管理

#### `GET|POST /admin/profile/`
- **機能**: プロフィール設定
- **認証**: Admin Required  
- **処理**: ユーザー情報編集・SNSアカウント設定
- **テンプレート**: `admin/profile.html`

## 📝 記事管理

### 記事一覧・統計

#### `GET /admin/articles/`
- **機能**: 記事一覧
- **認証**: Admin Required
- **クエリパラメータ**: 
  - `page` (ページ番号)
  - `per_page` (1ページあたり件数)
- **処理**: 
  - 記事一覧をページネーション
  - 統計情報計算 (総記事・公開・下書き・今月記事数)
- **テンプレート**: `admin/articles.html`
- **Pagination**: `db.paginate(select(Article))`

### 記事作成・編集

#### `GET|POST /admin/article/create/`
- **機能**: 記事作成
- **認証**: Admin Required
- **GET処理**: 作成フォーム表示
- **POST処理**: 
  - バリデーション (タイトル重複チェック等)
  - スラッグ自動生成
  - アイキャッチ画像処理
  - カテゴリ関連付け
- **フォーム**: `ArticleForm`
- **テンプレート**: `admin/article_form.html`
- **Service**: `ArticleService.create_article()`

#### `GET|POST /admin/article/edit/<int:article_id>/`
- **機能**: 記事編集
- **認証**: Admin Required
- **パラメータ**: `article_id` (記事ID)
- **処理**: 記事情報更新・カテゴリ関連付け変更
- **テンプレート**: `admin/article_form.html` (共通)
- **Service**: `ArticleService.update_article()`

### 記事削除・一括操作

#### `POST /admin/article/delete/<int:article_id>`
- **機能**: 記事削除
- **認証**: Admin Required
- **パラメータ**: `article_id`
- **処理**: 記事・関連データ削除
- **CSRF**: Required

#### `POST /admin/articles/bulk_action/`
- **機能**: 記事一括操作
- **認証**: Admin Required
- **フォームデータ**: 
  - `action` (publish/unpublish/delete)
  - `article_ids[]` (対象記事ID配列)
- **処理**: 選択記事への一括処理
- **CSRF**: Required

## 🏷️ カテゴリ管理

### カテゴリ一覧

#### `GET /admin/categories/`
- **機能**: カテゴリ一覧
- **認証**: Admin Required
- **クエリパラメータ**: `page`
- **処理**: 
  - カテゴリ一覧をページネーション
  - 統計情報 (総カテゴリ数・記事数・空カテゴリ数)
- **テンプレート**: `admin/categories.html`
- **Pagination**: `db.paginate(select(Category).order_by(Category.name))`

### カテゴリ作成・編集

#### `GET|POST /admin/category/create/`
- **機能**: カテゴリ作成
- **認証**: Admin Required
- **フォーム**: `CategoryForm`
- **処理**: 
  - スラッグ自動生成・重複チェック
  - 親カテゴリ設定
  - OGP画像処理
- **テンプレート**: `admin/category_form.html`
- **Service**: `CategoryService.create_category()`

#### `GET|POST /admin/category/edit/<int:category_id>/`
- **機能**: カテゴリ編集
- **認証**: Admin Required
- **パラメータ**: `category_id`
- **処理**: カテゴリ情報更新・OGP画像更新
- **テンプレート**: `admin/edit_category.html`
- **Service**: `CategoryService.update_category()`

### カテゴリ削除

#### `POST /admin/category/delete/<int:category_id>`
- **機能**: カテゴリ削除
- **認証**: Admin Required
- **処理**: 
  - 関連記事チェック
  - 子カテゴリ存在チェック
  - 安全削除実行
- **CSRF**: Required

## 👥 ユーザー管理

### ユーザー一覧

#### `GET /admin/users/`
- **機能**: ユーザー一覧
- **認証**: Admin Required
- **処理**: 全ユーザー表示・役割別統計
- **テンプレート**: `admin/users.html`

### ユーザー作成・編集

#### `GET|POST /admin/user/create/`
- **機能**: ユーザー作成
- **認証**: Admin Required
- **フォームデータ**: 
  - `email`, `name`, `password`
  - `role` (admin/author)
- **処理**: 
  - メール重複チェック
  - パスワードハッシュ化
  - 初期設定
- **テンプレート**: `admin/create_user.html`

#### `GET|POST /admin/user/edit/<int:user_id>/`
- **機能**: ユーザー編集
- **認証**: Admin Required
- **パラメータ**: `user_id`
- **処理**: ユーザー情報更新・権限変更
- **テンプレート**: `admin/edit_user.html`
- **Service**: `UserService.update_user()`

### ユーザー削除

#### `POST /admin/user/delete/<int:user_id>`
- **機能**: ユーザー削除
- **認証**: Admin Required
- **処理**: 
  - 管理者数チェック (最後の管理者削除防止)
  - 関連記事の処理
  - 安全削除実行
- **CSRF**: Required

## 💬 コメント管理

### コメント一覧

#### `GET /admin/comments/`
- **機能**: コメント一覧・管理
- **認証**: Admin Required
- **クエリパラメータ**: 
  - `page`
  - `status` (all/approved/pending)
- **処理**: 
  - ステータス別フィルタリング
  - 統計情報 (総数・承認済み・承認待ち)
- **テンプレート**: `admin/comments.html`
- **Pagination**: `db.paginate(select(Comment).where(...))`

### コメント操作

#### `POST /admin/comment/approve/<int:comment_id>`
- **機能**: コメント承認
- **認証**: Admin Required
- **パラメータ**: `comment_id`
- **処理**: `is_approved = True`
- **CSRF**: Required

#### `POST /admin/comment/reject/<int:comment_id>`
- **機能**: コメント拒否
- **認証**: Admin Required
- **処理**: `is_approved = False`
- **CSRF**: Required

#### `POST /admin/comment/delete/<int:comment_id>`
- **機能**: コメント削除
- **認証**: Admin Required
- **処理**: コメント・子コメント削除
- **CSRF**: Required

#### `POST /admin/comments/bulk_action/`
- **機能**: コメント一括操作
- **認証**: Admin Required
- **フォームデータ**: 
  - `action` (approve/reject/delete)
  - `comment_ids[]`
- **処理**: 選択コメントへの一括処理
- **CSRF**: Required

## 🖼️ 画像管理

### 画像一覧・ギャラリー

#### `GET /admin/images/`
- **機能**: 画像管理一覧
- **認証**: Admin Required
- **クエリパラメータ**: 
  - `page`, `per_page`
  - `search` (ファイル名検索)
- **処理**: 
  - 画像一覧表示
  - 検索フィルタリング
  - 統計情報 (総容量・ファイル数)
- **テンプレート**: `admin/images.html`

#### `GET /admin/images/gallery/`
- **機能**: 画像ギャラリー
- **認証**: Admin Required
- **処理**: グリッド表示での画像選択インターフェース
- **テンプレート**: `admin/image_gallery.html`

### 画像アップロード・処理

#### `POST /admin/upload_image/`
- **機能**: 汎用画像アップロード
- **認証**: Admin Required
- **ファイル**: `image` (multipart/form-data)
- **処理**: 
  - ファイル検証 (拡張子・サイズ・MIMEタイプ)
  - 自動リサイズ・最適化
  - データベース登録
- **戻り値**: JSON (success/error, file_path)

#### `POST /admin/upload_featured_image/`
- **機能**: アイキャッチ画像アップロード
- **認証**: Admin Required
- **処理**: 
  - 16:9比率チェック
  - クロッピング処理
  - 最適化・保存
- **戻り値**: JSON

#### `POST /admin/process_image/`
- **機能**: 画像処理 (クロップ・リサイズ)
- **認証**: Admin Required
- **フォームデータ**: 
  - `image_file`
  - `crop_data` (JSON: x, y, width, height)
  - `target_width`, `target_height`
- **処理**: Cropper.js連携での画像処理

### 画像削除

#### `POST /admin/image/delete/<int:image_id>`
- **機能**: 画像削除
- **認証**: Admin Required
- **パラメータ**: `image_id`
- **処理**: 
  - ファイル削除
  - データベース削除 (論理削除)
- **CSRF**: Required

## ⚙️ サイト設定

#### `GET|POST /admin/site_settings/`
- **機能**: サイト設定管理
- **認証**: Admin Required
- **処理**: 
  - 設定一覧表示
  - 設定値更新
  - カテゴリ別設定管理
- **テンプレート**: `admin/site_settings.html`

## 🔧 API・ユーティリティ

### データ取得API

#### `GET /admin/get_categories/`
- **機能**: カテゴリ一覧API
- **認証**: Admin Required
- **戻り値**: JSON (id, name, parent_id)
- **用途**: 動的フォーム生成

### デバッグ・開発

#### `GET /admin/debug/template/`
- **機能**: テンプレート描画テスト
- **認証**: Admin Required
- **用途**: 開発時のデバッグ
- **戻り値**: ダッシュボード (フォールバックデータ)

## 🔒 認証・認可仕様

### デコレータ

#### `@admin_required`
- **機能**: 管理者権限チェック
- **条件**: 
  1. ログイン済み (`current_user.is_authenticated`)
  2. 管理者権限 (`current_user.role == 'admin'`)
  3. 2FA認証済み (2FA有効時)
- **リダイレクト**: 未認証時は `/login/`

#### `@login_required`
- **機能**: ログインチェック
- **提供元**: Flask-Login
- **リダイレクト**: 未認証時は `/login/`

### セッション管理

#### セッションキー
- `user_id`: ログインユーザーID
- `temp_user_id`: 2FA認証前の一時ユーザーID
- `_csrf_token`: CSRF保護トークン

#### セッション有効期限
- **一般**: 24時間 (remember_me 無効時)
- **Remember Me**: 30日間
- **CSRF Token**: セッション有効期間中

## 📊 エラーハンドリング

### HTTPエラー
- **404**: 記事・カテゴリ・ユーザーが見つからない場合
- **403**: 権限不足 (下書き記事への非管理者アクセス等)
- **401**: 認証必須ページへの未認証アクセス

### フォームエラー
- **バリデーションエラー**: フラッシュメッセージでユーザー通知
- **CSRF エラー**: 自動リダイレクト・再試行促進
- **ファイルアップロードエラー**: 詳細なエラーメッセージ

### データベースエラー
- **IntegrityError**: 重複データ・制約違反時の適切な処理
- **トランザクション**: 失敗時の自動ロールバック
- **接続エラー**: フォールバック処理・エラーログ

## 🚀 パフォーマンス考慮

### クエリ最適化
- **Pagination**: 大量データでの効率的な表示
- **Index Usage**: 主要フィールドでのインデックス活用
- **N+1 Problem**: relationshipの適切な読み込み

### キャッシュ戦略
- **Static Files**: ブラウザキャッシュ活用
- **Database Query**: 統計データの適切なキャッシュ
- **Image Processing**: 処理済み画像の再利用

### セキュリティ最適化
- **CSRF Protection**: 全POST/PUT/DELETE リクエストで必須
- **File Upload**: 厳密な検証・制限
- **SQL Injection**: SQLAlchemy ORM による自動防御

---

**ルーティング総数**: 50+ routes  
**認証レベル**: 3段階 (Public, Auth Required, Admin Required)  
**Blueprint構成**: Main + Admin  
**最終更新**: 2025年7月7日