# データベース設計

**最新更新**: 2025年7月1日 - MySQL 9.3.0移行完了・SQLAlchemy 2.0対応済み・CRUD重複実装解決

---

## 🎯 データベース環境

- **データベース**: MySQL 9.3.0 (本番・開発統一)
- **ORM**: SQLAlchemy 2.0.41 (非推奨パターン完全排除済み)
- **接続ドライバー**: PyMySQL 1.1.1 (AWS RDS対応)
- **マイグレーション**: Flask-Migrate (Alembic) 4.0.5
- **設定管理**: 環境変数ベース (開発・本番分離対応)

---

## users（ユーザ）

| カラム名             | 日本語名           | 型           | 制約・備考                  |
|----------------------|--------------------|--------------|-----------------------------|
| id                   | ユーザID           | INTEGER      | PRIMARY KEY, AUTOINCREMENT  |
| email                | メールアドレス     | TEXT         | UNIQUE, NOT NULL            |
| name                 | 本名               | TEXT         | NOT NULL                    |
| handle_name          | ハンドルネーム     | TEXT         |                             |
| password_hash        | パスワードハッシュ | TEXT         | NOT NULL                    |
| introduction         | 紹介文             | TEXT         | 250文字以内                 |
| birthplace           | 出身地             | TEXT         | 10文字以内                  |
| birthday             | 誕生日             | DATE         |                             |
| sns_accounts         | SNSアカウント      | JSON/TEXT    | X, Facebook, Instagram等    |
| totp_secret          | TOTPシークレット   | TEXT         | Google Authenticator用      |
| totp_enabled         | 2段階認証有効      | BOOLEAN      | 2段階認証有効フラグ         |
| created_at           | 作成日時           | DATETIME     |                             |
| updated_at           | 更新日時           | DATETIME     |                             |
| role                 | 権限               | TEXT         | 'admin'または'author'       |
| notify_on_publish    | 記事公開通知ON/OFF | BOOLEAN      | デフォルトOFF               |
| notify_on_comment    | コメント通知ON/OFF | BOOLEAN      | デフォルトOFF               |
| ext_json             | 拡張用JSON         | JSON/TEXT    | 拡張用                      |

---

## articles（記事）

| カラム名         | 日本語名           | 型           | 制約・備考                  |
|------------------|--------------------|--------------|-----------------------------|
| id               | 記事ID             | INTEGER      | PRIMARY KEY, AUTOINCREMENT  |
| title            | タイトル           | TEXT         | NOT NULL                    |
| slug             | スラッグ           | TEXT         | UNIQUE, NOT NULL            |
| summary          | 要約               | TEXT         |                             |
| body             | 記事本文           | TEXT         | Markdown形式                |
| featured_image   | アイキャッチ画像   | TEXT         | ファイルパス（16:9比率）    |
| status           | 公開ステータス     | TEXT         | draft/published/scheduled/承認待ち |
| published_at     | 公開日時           | DATETIME     |                             |
| author_id        | 著者ユーザID       | INTEGER      | users.id (FK)               |
| created_at       | 作成日時           | DATETIME     |                             |
| updated_at       | 更新日時           | DATETIME     |                             |
| meta_title       | SEO用メタタイトル  | TEXT         | NULL可                      |
| meta_description | SEO用メタ説明文    | TEXT         | NULL可                      |
| meta_keywords    | メタキーワード     | TEXT         | カンマ区切り,またはJSON     |
| canonical_url    | カノニカルURL      | TEXT         | NULL可、自動生成が基本      |
| is_published     | 公開フラグ         | BOOLEAN      | DEFAULT FALSE               |
| allow_comments   | コメント許可フラグ | BOOLEAN      | DEFAULT TRUE                |
| ext_json         | 拡張用JSON         | JSON/TEXT    | 拡張用                      |

---

## article_blocks（記事ブロック）

| カラム名         | 日本語名           | 型           | 制約・備考                  |
|------------------|--------------------|--------------|-----------------------------|
| id               | ブロックID         | INTEGER      | PRIMARY KEY, AUTOINCREMENT  |
| article_id       | 記事ID             | INTEGER      | articles.id (FK)            |
| block_type       | ブロック種別       | TEXT         | text/image/sns/embed        |
| content          | ブロック内容       | TEXT/JSON    | ブロック内容                |
| sort_order       | 並び順             | INTEGER      |                             |

---

## article_categories（記事-カテゴリ多対多）

| カラム名         | 日本語名           | 型           | 制約・備考                  |
|------------------|--------------------|--------------|-----------------------------|
| article_id       | 記事ID             | INTEGER      | articles.id (FK)            |
| category_id      | カテゴリID         | INTEGER      | categories.id (FK)          |

---

## site_settings（サイト設定）

| カラム名         | 日本語名           | 型           | 制約・備考                  |
|------------------|--------------------|--------------|-----------------------------|
| id               | サイト設定ID       | INTEGER      | PRIMARY KEY                 |
| title            | サイトタイトル     | TEXT         |                             |
| subtitle         | サブタイトル       | TEXT         |                             |
| url              | サイトURL          | TEXT         |                             |
| header_image     | ヘッダー画像       | TEXT         |                             |
| logo_image       | ロゴ画像           | TEXT         |                             |
| ogp_image        | OGP画像            | TEXT         |                             |
| description      | サイト紹介文       | TEXT         |                             |
| meta_keywords    | メタキーワード     | TEXT         | サイト全体用                |
| canonical_url    | カノニカルURL      | TEXT         | サイト全体用                |
| json_ld          | 構造化データ(JSON-LD) | TEXT      | サイト全体用                |
| ext_json         | 拡張用JSON         | JSON/TEXT    | 拡張用                      |

---

## comments（コメント）🆕2025年6月30日完全実装

| カラム名         | 日本語名           | 型           | 制約・備考                  |
|------------------|--------------------|--------------|-----------------------------|
| id               | コメントID         | INTEGER      | PRIMARY KEY, AUTOINCREMENT  |
| article_id       | 記事ID             | INTEGER      | articles.id (FK)            |
| user_id          | ユーザID           | INTEGER      | users.id (FK), NULL可       |
| name             | 投稿者名           | TEXT         | 未ログイン時用              |
| body             | コメント本文       | TEXT         |                             |
| is_approved      | 承認状態           | BOOLEAN      | DEFAULT FALSE（承認待ち）   |
| created_at       | 作成日時           | DATETIME     |                             |
| updated_at       | 更新日時           | DATETIME     |                             |

**実装済み機能**:
- ✅ コメント投稿機能（記事詳細ページ）
- ✅ 承認システム（管理者承認後公開）
- ✅ 管理画面（一覧・承認・拒否・削除）
- ✅ CSRFトークン対応
- ✅ 一括操作機能

---

## E-R図（テキスト表現）

- users 1 --- * articles
- articles 1 --- * article_blocks
- articles * --- * categories（article_categoriesで多対多）
- categories（親子関係：parent_idで自己参照）
- articles 1 --- * comments
- users 1 --- * comments

## uploaded_images（アップロード画像）🆕2025年6月30日実装

| カラム名         | 日本語名           | 型           | 制約・備考                  |
|------------------|--------------------|--------------|-----------------------------|
| id               | 画像ID             | INTEGER      | PRIMARY KEY, AUTOINCREMENT  |
| filename         | ファイル名         | TEXT         | 実際のファイル名            |
| url              | 画像URL            | TEXT         | アクセス用URL               |
| alt_text         | 代替テキスト       | TEXT         | アクセシビリティ用          |
| caption          | キャプション       | TEXT         | 画像説明（省略可）          |
| description      | 説明               | TEXT         | 管理用説明（省略可）        |
| file_size        | ファイルサイズ     | INTEGER      | バイト単位                  |
| width            | 幅                 | INTEGER      | ピクセル                    |
| height           | 高さ               | INTEGER      | ピクセル                    |
| uploaded_by      | アップロード者     | INTEGER      | users.id (FK)               |
| created_at       | 作成日時           | DATETIME     |                             |

**実装済み機能**:
- ✅ 4:3比率クロッピング機能
- ✅ Cropper.js統合リアルタイムトリミング
- ✅ ドラッグ&ドロップアップロード
- ✅ プレビュー表示
- ✅ エラーハンドリング・タイムアウト対応
- ✅ Markdownコピー機能

---

## 2. テーブル定義

### 2.3. Category (カテゴリ) テーブル

カテゴリ情報を格納するテーブル。

| カラム名             | データ型        | 説明                                                                 | 制約                       | 備考                                                                 |
|----------------------|-----------------|----------------------------------------------------------------------|----------------------------|----------------------------------------------------------------------|
| `id`                 | INTEGER         | カテゴリID                                                             | PRIMARY KEY, AUTOINCREMENT |                                                                      |
| `name`               | VARCHAR(100)    | カテゴリ名                                                             | NOT NULL, UNIQUE           |                                                                      |
| `slug`               | VARCHAR(100)    | スラッグ (URL用)                                                       | NOT NULL, UNIQUE           |                                                                      |
| `description`        | TEXT            | カテゴリの説明                                                         |                            |                                                                      |
| `parent_id`          | INTEGER         | 親カテゴリID (自己参照)                                                | FOREIGN KEY (`Category.id`) | NULL許容 (トップレベルカテゴリの場合)                                    |
| `created_at`         | DATETIME        | 作成日時                                                               | NOT NULL                   | DEFAULT CURRENT_TIMESTAMP                                            |
| `updated_at`         | DATETIME        | 更新日時                                                               | NOT NULL                   | DEFAULT CURRENT_TIMESTAMP, ON UPDATE CURRENT_TIMESTAMP                 |
| `meta_title`         | VARCHAR(255)    | SEO用メタタイトル                                                      |                            | NULL許容                                                               |
| `meta_description`   | TEXT            | SEO用メタディスクリプション                                              |                            | NULL許容                                                               |
| `meta_keywords`      | VARCHAR(255)    | SEO用メタキーワード (カンマ区切り)                                       |                            | NULL許容                                                               |
| `ogp_image`          | VARCHAR(255)    | OGP画像のファイルパス                                                    |                            | NULL許容。例: `uploads/category_ogp/category_ogp_1_timestamp.jpg`    |
| `canonical_url`      | VARCHAR(255)    | 正規URL                                                                |                            | NULL許容                                                               |
| `json_ld`            | TEXT            | JSON-LD形式の構造化データ                                                |                            | NULL許容                                                               |
| `ext_json`           | TEXT            | 外部連携用JSONデータ (汎用)                                            |                            | NULL許容                                                               |

---

## 🚀 **サービス層アーキテクチャ (2025年7月1日追加)**

### **CRUD重複実装の解決**

従来の問題：
- 記事作成・編集ルートに400行の重複コード
- カテゴリ作成・編集ルートに300行の重複コード  
- ユーザ作成・編集ルートに250行の重複コード
- それぞれを個別にテスト・保守する必要

### **実装されたサービスクラス**

#### **ArticleService** (`article_service.py`)
```python
class ArticleService:
    @staticmethod
    def create_article(form_data, author_id)
    def update_article(article, form_data)
    def setup_category_choices(form)
    def generate_unique_slug(title, article_id=None)
    def validate_article_data(form, article_id=None)
    def process_article_image(article, cropped_image_data)
    def assign_category(article, category_id)
    def get_article_context(article=None)
```

#### **CategoryService** (`article_service.py`)
```python
class CategoryService:
    @staticmethod
    def create_category(form_data)
    def update_category(category, form_data)
    def generate_unique_slug(name, category_id=None)
    def validate_category_data(form_data, category_id=None)
    def process_category_image(category, ogp_image_data, crop_data=None)
    def extract_crop_data(form)
    def get_category_context(category=None)
```

#### **UserService** (`article_service.py`)
```python
class UserService:
    @staticmethod
    def create_user(form_data)
    def update_user(user, form_data)
    def validate_password(password)
    def validate_user_data(form_data, user_id=None)
    def process_user_form_data(form_data)
    def get_user_context(user=None)
```

### **統一テンプレートシステム**

- **従来**: 別々のcreate/editテンプレート
- **新方式**: 統一フォームテンプレート (`article_form.html`)
- **削減効果**: 76.7%のテンプレートサイズ削減

### **データベース操作の標準化**

全サービスで以下のパターンを統一：
1. **バリデーション** → エラー配列返却
2. **データ処理** → 正規化・サニタイズ
3. **DB操作** → try/catch + rollback
4. **結果返却** → (success_object, error_message)

### **保守性向上**

- **単一責任**: 各エンティティのCRUD処理を一箇所に集約
- **再利用性**: 作成・編集ルートが共通サービスを利用
- **テスタビリティ**: サービスメソッド単位でのテスト可能
- **拡張性**: 新機能追加時は一箇所の修正で全体に反映

---