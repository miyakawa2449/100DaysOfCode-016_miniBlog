# データベース設計

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
| description      | ディスクリプション | TEXT         |                             |
| eyecatch_image   | アイキャッチ画像   | TEXT         | ファイルパス等              |
| status           | 公開ステータス     | TEXT         | draft/published/scheduled/承認待ち |
| published_at     | 公開日時           | DATETIME     |                             |
| author_id        | 著者ユーザID       | INTEGER      | users.id (FK)               |
| created_at       | 作成日時           | DATETIME     |                             |
| updated_at       | 更新日時           | DATETIME     |                             |
| meta_keywords    | メタキーワード     | TEXT         | カンマ区切り,またはJSON     |
| canonical_url    | カノニカルURL      | TEXT         | NULL可、自動生成が基本      |
| json_ld          | 構造化データ(JSON-LD) | TEXT      | JSON-LD形式で保存（必要に応じて）|
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

## categories（カテゴリ）

| カラム名         | 日本語名           | 型           | 制約・備考                  |
|------------------|--------------------|--------------|-----------------------------|
| id               | カテゴリID         | INTEGER      | PRIMARY KEY, AUTOINCREMENT  |
| name             | カテゴリ名         | TEXT         | NOT NULL                    |
| slug             | スラッグ           | TEXT         | UNIQUE, NOT NULL            |
| description      | 紹介文             | TEXT         |                             |
| parent_id        | 親カテゴリID       | INTEGER      | categories.id (FK)          |
| ogp_image        | OGP画像            | TEXT         |                             |
| meta_keywords    | メタキーワード     | TEXT         | カンマ区切り,またはJSON     |
| canonical_url    | カノニカルURL      | TEXT         | NULL可、自動生成が基本      |
| json_ld          | 構造化データ(JSON-LD) | TEXT      | JSON-LD形式で保存（必要に応じて）|
| ext_json         | 拡張用JSON         | JSON/TEXT    | 拡張用                      |

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

## comments（コメント）

| カラム名         | 日本語名           | 型           | 制約・備考                  |
|------------------|--------------------|--------------|-----------------------------|
| id               | コメントID         | INTEGER      | PRIMARY KEY, AUTOINCREMENT  |
| article_id       | 記事ID             | INTEGER      | articles.id (FK)            |
| user_id          | ユーザID           | INTEGER      | users.id (FK), NULL可       |
| name             | 投稿者名           | TEXT         | 未ログイン時用              |
| body             | コメント本文       | TEXT         |                             |
| status           | ステータス         | TEXT         | 公開/非公開/承認待ち        |
| notify           | 通知フラグ         | BOOLEAN      |                             |
| created_at       | 作成日時           | DATETIME     |                             |

---

## E-R図（テキスト表現）

- users 1 --- * articles
- articles 1 --- * article_blocks
- articles * --- * categories（article_categoriesで多対多）
- categories（親子関係：parent_idで自己参照）
- articles 1 --- * comments
- users 1 --- * comments

---