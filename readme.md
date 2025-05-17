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

1. **リポジトリをクローン**
    ```bash
    git clone <このリポジトリのURL>
    cd miniblog
    ```

2. **仮想環境の作成と有効化**
    ```bash
    python -m venv venv
    venv\Scripts\activate  # Windows
    # source venv/bin/activate  # Mac/Linux
    ```

3. **必要なパッケージのインストール**
    ```bash
    pip install -r requirements.txt
    ```

4. **初期化**
    ```bash
    python app.py
    ```
    初回実行時にDBファイルが作成されます。

5. **管理者ユーザの追加**
    - `add_admin.py` などで管理者ユーザを追加してください。

6. **アプリの起動**
    ```bash
    python app.py
    ```
    ブラウザで [http://localhost:5000](http://localhost:5000) にアクセス。

---

## ディレクトリ構成例

```
miniblog/
├── app.py
├── add_admin.py
├── requirements.txt
├── templates/
│   ├── home.html
│   └── login.html
├── static/
├── uploads/
│   └── images/
├── .gitignore
└── README.md
```

---

## 注意事項

- 画像アップロードは `/uploads/images/` ディレクトリに保存されます。
- セキュリティのため、`SECRET_KEY`は本番運用時に必ず変更してください。
- 開発用のため、実運用時は追加のセキュリティ対策やバックアップ運用を推奨します。

---

## ライセンス

MIT License

---