# ミニブログ（MiniBlog）

## 概要

このプロジェクトは、Python FlaskとSQLAlchemyを使ったシンプルなミニブログシステムです。
ユーザ管理、記事投稿、カテゴリ管理、コメント、画像アップロード、SEO/OGP対応など、基本的なCMS機能を備えています。

---

## 主な機能

- ユーザ登録・ログイン（2段階認証対応）
- 記事の作成・編集・削除（ブロック型エディタ）
- カテゴリ管理（階層対応）
- コメント機能（承認制・通知対応）
- 画像アップロード（ファイルサイズ・拡張子制限あり）
- SEO/OGPメタ情報・構造化データ対応
- 管理画面（ダッシュボード、ユーザ・記事・カテゴリ・コメント管理）
- エクスポート（CSV/JSON）
- 通知メール送信
- 拡張用JSONによる柔軟な拡張性

---

## セットアップ手順

1.  **リポジトリをクローン**
    ```bash
    git clone <このリポジトリのURL>
    cd miniblog
    ```

2.  **仮想環境の作成と有効化**
    ```bash
    python -m venv venv
    venv\Scripts\activate  # Windows
    # source venv/bin/activate  # Mac/Linux
    ```

3.  **必要なパッケージのインストール**
    ```bash
    pip install -r requirements.txt
    ```

4.  **初期化**
    ```bash
    python app.py
    ```
    初回実行時にDBファイルが作成されます（通常は `instance` フォルダ内）。

5.  **管理者ユーザの追加**
    -   `add_admin.py` を実行して管理者ユーザを追加してください。
        ```bash
        python add_admin.py
        ```

6.  **アプリの起動**
    ```bash
    python app.py
    ```
    ブラウザで [http://localhost:5000](http://localhost:5000) にアクセス。

---

## ディレクトリ構成例

```
miniblog/
├── app.py              # Flaskアプリケーション本体、主要なルーティング
├── admin.py            # 管理画面用Blueprint、ルーティング
├── models.py           # SQLAlchemyデータベースモデル定義
├── add_admin.py        # 管理者ユーザー追加スクリプト
├── requirements.txt    # 必要なPythonパッケージリスト
├── templates/          # Jinja2テンプレート
│   ├── home.html
│   ├── login.html
│   └── admin/          # 管理画面用テンプレート
│       ├── dashboard.html
│       ├── users.html
│       ├── edit_user.html
│       ├── articles.html
│       ├── create_article.html
│       └── edit_article.html
│       # (categories.html, comments.html, site_settings.html などもここに追加)
├── static/             # 静的ファイル (CSS, JavaScript, 画像など)
│   └── css/
│       └── style.css   # (例: スタイルシート)
├── uploads/            # アップロードされたファイル（画像など）
│   └── images/
├── instance/           # インスタンス固有のファイル（例: miniblog.db）
├── .gitignore          # Gitで無視するファイル・ディレクトリ指定
└── README.md           # このファイル
```

---

## 注意事項

- 画像アップロードは `/uploads/images/` ディレクトリに保存されます。
- セキュリティのため、`app.secret_key` は本番運用時に必ずランダムで複雑な文字列に変更してください。
- このプロジェクトは開発学習用です。実運用時には、エラーハンドリングの強化、セキュリティ対策の追加（入力バリデーション、SQLインジェクション対策の再確認など）、適切なバックアップ運用を必ず行ってください。

---

## ライセンス

MIT License

---