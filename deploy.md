# AWSデプロイ手順書 (Flask + Nginx + Gunicorn + PostgreSQL)

このドキュメントは、ローカルで開発したPython/FlaskプロジェクトをAWS（Amazon Web Services）上に公開（デプロイ）するための手順をまとめたものです。

## 1. デプロイ構成図

ユーザーからのリクエストは、以下の流れで処理されます。この構成は、Webアプリケーションを公開する際の標準的なベストプラクティスです。

```
[ユーザー] <--> [インターネット] <--> [Route 53 (DNS)]
                                           |
                                           v
[Nginx (Webサーバー)] <--> [Gunicorn (Appサーバー)] <--> [Flaskアプリ]
    (HTTPS/静的ファイル処理)      (UNIXソケット経由)           |
                                                               v
                                                      [PostgreSQL (RDS)]
```

## 2. デプロイへのロードマップ

デプロイ作業は、大きく分けて5つのフェーズで進めます。

1.  **Phase 1: ローカル環境の準備**
    *   本番環境で動作するように、データベースやWebサーバーを切り替えます。**このフェーズが最も重要です。**
2.  **Phase 2: AWSインフラの構築**
    *   サーバー（EC2）、データベース（RDS）、ネットワーク（VPC）など、アプリが動く土台をAWS上に構築します。
3.  **Phase 3: サーバー環境の構築**
    *   作成したEC2サーバーに、NginxやPythonなどの必要なソフトウェアをインストールします。
4.  **Phase 4: アプリケーションのデプロイ**
    *   Gitを使ってサーバーにソースコードを配置し、設定を行います。
5.  **Phase 5: アプリケーションの公開**
    *   GunicornとNginxを連携させ、外部からアクセスできるように設定します。

---

## Phase 1: ローカル環境の準備

### 1. データベースをPostgreSQLに変更
**理由**: 開発用のSQLiteは手軽ですが、複数アクセスの信頼性が低いため、本番環境では堅牢なPostgreSQLを使用します。

```bash
# PostgreSQLを操作するためのライブラリをインストール
pip install psycopg2-binary
```

`config.py`を修正し、環境変数からデータベースURLを読み込むように変更します。

```python
// filepath: config.py
import os

class Config:
    # ...
    # 環境変数 'DATABASE_URL' があればそれを使用し、なければローカルのSQLiteをフォールバックとして使用
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'blog.db')
    # ...
```

### 2. 本番用Webサーバー Gunicorn を導入
**理由**: Flask標準の開発サーバーはデバッグ用です。本番環境では、パフォーマンスと安定性に優れたGunicornを使用します。

```bash
pip install gunicorn
```

### 3. 依存関係ファイル `requirements.txt` を作成
サーバーにインストールするPythonライブラリの一覧を作成します。

```bash
pip freeze > requirements.txt
```
※このコマンドは、今後ライブラリを追加・更新するたびに実行してください。

### 4. WSGIエントリーポイント `wsgi.py` を作成
GunicornがFlaskアプリケーションを起動するための「入口」となるファイルです。

```python
// filepath: wsgi.py
from app import create_app

# create_app ファクトリ関数を呼び出して app インスタンスを生成
app = create_app()

if __name__ == "__main__":
    app.run()
```

### 5. 環境変数ファイル `.env` の準備
データベースのパスワードなどの秘密情報を、コードと分離して安全に管理します。

```bash
# .envファイルをバージョン管理から除外する
echo ".env" >> .gitignore
```

プロジェクトのルートに `.env` ファイルを作成します。

```
# filepath: .env
FLASK_APP=wsgi.py
FLASK_ENV=production
SECRET_KEY=openssl rand -hex 32などで生成した非常に強力なキー
DATABASE_URL=postgresql://user:password@host:port/dbname
```
※`DATABASE_URL`はPhase 2で作成するRDSの情報を後で設定します。

---

## Phase 2: AWSインフラの構築 (EC2 + RDS)

AWS資格取得を目指すため、VPCやRDSを組み合わせた本格的な構成で構築します。

1.  **VPCの作成**:
    *   AWSコンソールで「VPC」を検索し、「VPCを作成」を選択。
    *   「VPCなど」を選択すると、パブリックサブネットとプライベートサブネットが自動で作成され便利です。

2.  **RDS for PostgreSQLの作成**:
    *   「RDS」を検索し、「データベースの作成」を選択。
    *   「標準作成」で「PostgreSQL」を選択。
    *   **接続**: 作成したVPCを選択し、サブネットグループで**プライベートサブネット**を指定します。
    *   **パブリックアクセス**: 「なし」を選択します。
    *   データベース名、マスターユーザー名、パスワードを設定します。

3.  **EC2インスタンスの起動**:
    *   「EC2」を検索し、「インスタンスを起動」を選択。
    *   **AMI**: 「Ubuntu Server 22.04 LTS」を選択。
    *   **インスタンスタイプ**: 「t2.micro」など無料利用枠の対象を選択。
    *   **キーペア**: 新しいキーペアを作成し、`.pem`ファイルをダウンロードします（サーバー接続に必須）。
    *   **ネットワーク設定**: 作成したVPCと**パブリックサブネット**を選択します。
    *   **セキュリティグループ**: 新しいセキュリティグループを作成し、以下のルールを設定します。
        *   `SSH` (ポート 22) / ソース: マイIP
        *   `HTTP` (ポート 80) / ソース: すべての場所 (Anywhere)
        *   `HTTPS` (ポート 443) / ソース: すべての場所 (Anywhere)

4.  **RDSのセキュリティグループ設定**:
    *   RDSインスタンスに紐づくセキュリティグループを編集します。
    *   インバウンドルールに、タイプ「PostgreSQL」、ソース「EC2インスタンスのセキュリティグループID」を追加します。これにより、EC2からのみDBへのアクセスが許可されます。

---

## Phase 3: サーバー環境の構築

ダウンロードしたキーペアを使って、EC2インスタンスにSSH接続します。

```bash
# .pemファイルに適切な権限を与える
chmod 400 your-key-pair.pem

# SSH接続
ssh -i "your-key-pair.pem" ubuntu@your_ec2_public_ip
```

サーバーに接続後、必要なソフトウェアをインストールします。

```bash
# パッケージリストを更新
sudo apt update && sudo apt upgrade -y

# 必須ソフトウェアをインストール
sudo apt install -y python3-pip python3-venv nginx git
```

---

## Phase 4: アプリケーションのデプロイ

1.  **Gitからソースコードをクローン**
    ```bash
    git clone https://github.com/your_username/100DaysOfCode-016_miniBlog.git
    cd 100DaysOfCode-016_miniBlog
    ```

2.  **Python仮想環境のセットアップ**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **依存関係のインストール**
    ```bash
    pip install -r requirements.txt
    ```

4.  **環境変数ファイル `.env` の設定**
    ```bash
    # nanoエディタで.envファイルを作成
    nano .env
    ```
    ローカルで準備した`.env`の内容を貼り付けます。`DATABASE_URL`には、Phase 2で作成したRDSのエンドポイント、ユーザー名、パスワードを設定します。

5.  **データベースマイグレーションの実行**
    ```bash
    # Flask-Migrateでデータベースにテーブルを作成
    flask db upgrade
    ```

---

## Phase 5: アプリケーションの公開

### 1. Gunicornのサービス化 (Systemd)
サーバーが再起動してもアプリが自動で立ち上がるように、Gunicornをサービスとして登録します。

`sudo nano /etc/systemd/system/miniblog.service` を実行し、以下の内容を記述します。

```ini
# filepath: /etc/systemd/system/miniblog.service
[Unit]
Description=Gunicorn instance to serve miniblog
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/100DaysOfCode-016_miniBlog
EnvironmentFile=/home/ubuntu/100DaysOfCode-016_miniBlog/.env
ExecStart=/home/ubuntu/100DaysOfCode-016_miniBlog/venv/bin/gunicorn --workers 3 --bind unix:miniblog.sock -m 007 wsgi:app

[Install]
WantedBy=multi-user.target
```

サービスを起動・有効化します。
```bash
sudo systemctl start miniblog
sudo systemctl enable miniblog
```

### 2. Nginxの設定
外部からのHTTPリクエストをGunicornに中継するようにNginxを設定します。

`sudo nano /etc/nginx/sites-available/miniblog` を実行し、以下の内容を記述します。

```nginx
# filepath: /etc/nginx/sites-available/miniblog
server {
    listen 80;
    server_name your_domain.com www.your_domain.com; # またはEC2のパブリックIP

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/ubuntu/100DaysOfCode-016_miniBlog/miniblog.sock;
    }

    location /static {
        alias /home/ubuntu/100DaysOfCode-016_miniBlog/static;
    }
}
```

設定を有効化し、Nginxを再起動します。
```bash
sudo ln -s /etc/nginx/sites-available/miniblog /etc/nginx/sites-enabled
sudo nginx -t  # 設定ファイルに文法エラーがないかテスト
sudo systemctl restart nginx
```
この時点で、`http://<EC2のIPアドレス>` にアクセスすると、アプリケーションが表示されるはずです。

### 3. ドメインとHTTPS化
1.  **ドメインの取得**: お名前.comなどで独自ドメインを取得します。
2.  **Route 53**: AWSのDNSサービスRoute 53にドメインを登録し、EC2のIPアドレスに紐付けます。
3.  **HTTPS化 (Let's Encrypt)**: 無料のSSL証明書を発行し、通信を暗号化します。
    ```bash
    # Certbotをインストール
    sudo apt install certbot python3-certbot-nginx

    # SSL証明書を取得し、Nginxに自動設定
    sudo certbot --nginx -d your_domain.com -d www.your_domain.com
    ```

以上で、本番環境へのデプロイは完了です。
```// filepath: deploy.md
# AWSデプロイ手順書 (Flask + Nginx + Gunicorn + PostgreSQL)

このドキュメントは、ローカルで開発したPython/FlaskプロジェクトをAWS（Amazon Web Services）上に公開（デプロイ）するための手順をまとめたものです。

## 1. デプロイ構成図

ユーザーからのリクエストは、以下の流れで処理されます。この構成は、Webアプリケーションを公開する際の標準的なベストプラクティスです。

```
[ユーザー] <--> [インターネット] <--> [Route 53 (DNS)]
                                           |
                                           v
[Nginx (Webサーバー)] <--> [Gunicorn (Appサーバー)] <--> [Flaskアプリ]
    (HTTPS/静的ファイル処理)      (UNIXソケット経由)           |
                                                               v
                                                      [PostgreSQL (RDS)]
```

## 2. デプロイへのロードマップ

デプロイ作業は、大きく分けて5つのフェーズで進めます。

1.  **Phase 1: ローカル環境の準備**
    *   本番環境で動作するように、データベースやWebサーバーを切り替えます。**このフェーズが最も重要です。**
2.  **Phase 2: AWSインフラの構築**
    *   サーバー（EC2）、データベース（RDS）、ネットワーク（VPC）など、アプリが動く土台をAWS上に構築します。
3.  **Phase 3: サーバー環境の構築**
    *   作成したEC2サーバーに、NginxやPythonなどの必要なソフトウェアをインストールします。
4.  **Phase 4: アプリケーションのデプロイ**
    *   Gitを使ってサーバーにソースコードを配置し、設定を行います。
5.  **Phase 5: アプリケーションの公開**
    *   GunicornとNginxを連携させ、外部からアクセスできるように設定します。

---

## Phase 1: ローカル環境の準備

### 1. データベースをPostgreSQLに変更
**理由**: 開発用のSQLiteは手軽ですが、複数アクセスの信頼性が低いため、本番環境では堅牢なPostgreSQLを使用します。

```bash
# PostgreSQLを操作するためのライブラリをインストール
pip install psycopg2-binary
```

`config.py`を修正し、環境変数からデータベースURLを読み込むように変更します。

```python
// filepath: config.py
import os

class Config:
    # ...
    # 環境変数 'DATABASE_URL' があればそれを使用し、なければローカルのSQLiteをフォールバックとして使用
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'blog.db')
    # ...
```

### 2. 本番用Webサーバー Gunicorn を導入
**理由**: Flask標準の開発サーバーはデバッグ用です。本番環境では、パフォーマンスと安定性に優れたGunicornを使用します。

```bash
pip install gunicorn
```

### 3. 依存関係ファイル `requirements.txt` を作成
サーバーにインストールするPythonライブラリの一覧を作成します。

```bash
pip freeze > requirements.txt
```
※このコマンドは、今後ライブラリを追加・更新するたびに実行してください。

### 4. WSGIエントリーポイント `wsgi.py` を作成
GunicornがFlaskアプリケーションを起動するための「入口」となるファイルです。

```python
// filepath: wsgi.py
from app import create_app

# create_app ファクトリ関数を呼び出して app インスタンスを生成
app = create_app()

if __name__ == "__main__":
    app.run()
```

### 5. 環境変数ファイル `.env` の準備
データベースのパスワードなどの秘密情報を、コードと分離して安全に管理します。

```bash
# .envファイルをバージョン管理から除外する
echo ".env" >> .gitignore
```

プロジェクトのルートに `.env` ファイルを作成します。

```
# filepath: .env
FLASK_APP=wsgi.py
FLASK_ENV=production
SECRET_KEY=openssl rand -hex 32などで生成した非常に強力なキー
DATABASE_URL=postgresql://user:password@host:port/dbname
```
※`DATABASE_URL`はPhase 2で作成するRDSの情報を後で設定します。

---

## Phase 2: AWSインフラの構築 (EC2 + RDS)

AWS資格取得を目指すため、VPCやRDSを組み合わせた本格的な構成で構築します。

1.  **VPCの作成**:
    *   AWSコンソールで「VPC」を検索し、「VPCを作成」を選択。
    *   「VPCなど」を選択すると、パブリックサブネットとプライベートサブネットが自動で作成され便利です。

2.  **RDS for PostgreSQLの作成**:
    *   「RDS」を検索し、「データベースの作成」を選択。
    *   「標準作成」で「PostgreSQL」を選択。
    *   **接続**: 作成したVPCを選択し、サブネットグループで**プライベートサブネット**を指定します。
    *   **パブリックアクセス**: 「なし」を選択します。
    *   データベース名、マスターユーザー名、パスワードを設定します。

3.  **EC2インスタンスの起動**:
    *   「EC2」を検索し、「インスタンスを起動」を選択。
    *   **AMI**: 「Ubuntu Server 22.04 LTS」を選択。
    *   **インスタンスタイプ**: 「t2.micro」など無料利用枠の対象を選択。
    *   **キーペア**: 新しいキーペアを作成し、`.pem`ファイルをダウンロードします（サーバー接続に必須）。
    *   **ネットワーク設定**: 作成したVPCと**パブリックサブネット**を選択します。
    *   **セキュリティグループ**: 新しいセキュリティグループを作成し、以下のルールを設定します。
        *   `SSH` (ポート 22) / ソース: マイIP
        *   `HTTP` (ポート 80) / ソース: すべての場所 (Anywhere)
        *   `HTTPS` (ポート 443) / ソース: すべての場所 (Anywhere)

4.  **RDSのセキュリティグループ設定**:
    *   RDSインスタンスに紐づくセキュリティグループを編集します。
    *   インバウンドルールに、タイプ「PostgreSQL」、ソース「EC2インスタンスのセキュリティグループID」を追加します。これにより、EC2からのみDBへのアクセスが許可されます。

---

## Phase 3: サーバー環境の構築

ダウンロードしたキーペアを使って、EC2インスタンスにSSH接続します。

```bash
# .pemファイルに適切な権限を与える
chmod 400 your-key-pair.pem

# SSH接続
ssh -i "your-key-pair.pem" ubuntu@your_ec2_public_ip
```

サーバーに接続後、必要なソフトウェアをインストールします。

```bash
# パッケージリストを更新
sudo apt update && sudo apt upgrade -y

# 必須ソフトウェアをインストール
sudo apt install -y python3-pip python3-venv nginx git
```

---

## Phase 4: アプリケーションのデプロイ

1.  **Gitからソースコードをクローン**
    ```bash
    git clone https://github.com/your_username/100DaysOfCode-016_miniBlog.git
    cd 100DaysOfCode-016_miniBlog
    ```

2.  **Python仮想環境のセットアップ**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **依存関係のインストール**
    ```bash
    pip install -r requirements.txt
    ```

4.  **環境変数ファイル `.env` の設定**
    ```bash
    # nanoエディタで.envファイルを作成
    nano .env
    ```
    ローカルで準備した`.env`の内容を貼り付けます。`DATABASE_URL`には、Phase 2で作成したRDSのエンドポイント、ユーザー名、パスワードを設定します。

5.  **データベースマイグレーションの実行**
    ```bash
    # Flask-Migrateでデータベースにテーブルを作成
    flask db upgrade
    ```

---

## Phase 5: アプリケーションの公開

### 1. Gunicornのサービス化 (Systemd)
サーバーが再起動してもアプリが自動で立ち上がるように、Gunicornをサービスとして登録します。

`sudo nano /etc/systemd/system/miniblog.service` を実行し、以下の内容を記述します。

```ini
# filepath: /etc/systemd/system/miniblog.service
[Unit]
Description=Gunicorn instance to serve miniblog
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/100DaysOfCode-016_miniBlog
EnvironmentFile=/home/ubuntu/100DaysOfCode-016_miniBlog/.env
ExecStart=/home/ubuntu/100DaysOfCode-016_miniBlog/venv/bin/gunicorn --workers 3 --bind unix:miniblog.sock -m 007 wsgi:app

[Install]
WantedBy=multi-user.target
```

サービスを起動・有効化します。
```bash
sudo systemctl start miniblog
sudo systemctl enable miniblog
```

### 2. Nginxの設定
外部からのHTTPリクエストをGunicornに中継するようにNginxを設定します。

`sudo nano /etc/nginx/sites-available/miniblog` を実行し、以下の内容を記述します。

```nginx
# filepath: /etc/nginx/sites-available/miniblog
server {
    listen 80;
    server_name your_domain.com www.your_domain.com; # またはEC2のパブリックIP

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/ubuntu/100DaysOfCode-016_miniBlog/miniblog.sock;
    }

    location /static {
        alias /home/ubuntu/100DaysOfCode-016_miniBlog/static;
    }
}
```

設定を有効化し、Nginxを再起動します。
```bash
sudo ln -s /etc/nginx/sites-available/miniblog /etc/nginx/sites-enabled
sudo nginx -t  # 設定ファイルに文法エラーがないかテスト
sudo systemctl restart nginx
```
この時点で、`http://<EC2のIPアドレス>` にアクセスすると、アプリケーションが表示されるはずです。

### 3. ドメインとHTTPS化
1.  **ドメインの取得**: お名前.comなどで独自ドメインを取得します。
2.  **Route 53**: AWSのDNSサービスRoute 53にドメインを登録し、EC2のIPアドレスに紐付けます。
3.  **HTTPS化 (Let's Encrypt)**: 無料のSSL証明書を発行し、通信を暗号化します。
    ```bash
    # Certbotをインストール
    sudo apt install certbot python3-certbot-nginx

    # SSL証明書を取得し、Nginxに自動設定
    sudo certbot --nginx -d your_domain.com -d www.your_domain.com
    ```

以上で、本番環境