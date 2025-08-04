# Mini Blog CMS - 高機能ブログ管理システム 🚀

## 📝 プロジェクト概要
Flask・MySQL・Bootstrap5を使用した**本格的なブログCMSシステム**

**主要特徴**:
- ✍️ **高機能ブロックエディタ**: 5種類のブロック対応（テキスト、画像、SNS埋込、外部記事）
- 🔐 **2段階認証**: Google Authenticator（TOTP）対応の強固なセキュリティ
- 📧 **安全なメール機能**: AWS SES統合でメールアドレス変更機能
- 🌐 **WordPress移行**: 完全なXMLインポート機能
- 📱 **レスポンシブデザイン**: モバイルファースト設計
- 🚀 **本番環境対応**: AWS Lightsail/EC2デプロイ設定完備

## 🛠️ 技術スタック

### **バックエンド**
- **Framework**: Python 3.12, Flask 2.3.3
- **Database**: MySQL 8.0 + SQLAlchemy 2.0 ORM
- **Authentication**: Flask-Login + TOTP 2FA
- **Email**: AWS SES統合（開発・本番対応）
- **Migration**: Flask-Migrate (Alembic)

### **セキュリティ**
- **CSRF Protection**: Flask-WTF
- **XSS Prevention**: Bleach HTML Sanitization
- **Password**: Werkzeug Security (ハッシュ化)
- **Security Headers**: X-Frame-Options, CSP, HSTS等
- **URL Obfuscation**: カスタム管理画面URL

### **フロントエンド**
- **UI Framework**: Bootstrap 5
- **Image Processing**: Cropper.js + PIL
- **JavaScript**: ES6+, リアルタイムプレビュー
- **Icons**: Font Awesome

### **インフラ・デプロイ**
- **Production**: Ubuntu 24.04 LTS + Nginx + Gunicorn
- **Cloud**: AWS Lightsail/EC2対応
- **SSL**: Let's Encrypt自動化
- **Security**: fail2ban, UFW firewall

## 🎯 ブロックエディタシステム

### **5つのブロックタイプ**
1. **📝 テキスト/Markdownブロック**: フルMarkdown対応
2. **🖼️ 画像ブロック**: 1:1比率（700×700px）自動トリミング
3. **🌟 アイキャッチ画像**: 16:9比率（800×450px）記事ヘッダー
4. **📱 SNS埋込ブロック**: X(Twitter), Facebook, Instagram, Threads, YouTube
5. **🔗 外部記事ブロック**: 自動OGPデータ取得・プレビューカード

### **高度な機能**
- **ドラッグ&ドロップ並び替え**: Sortable.js統合
- **リアルタイムプレビュー**: AJAX更新
- **表示モード切替**: 埋込 vs OGPカード表示
- **自動プラットフォーム検出**: SNS URL解析
- **画像処理**: リアルタイムクロッピング・最適化

## 📊 実装完了機能

### ✅ **認証・セキュリティ（100%）**
- ユーザー登録・ログイン・2FA
- 安全なメールアドレス変更機能
- パスワードリセット機能
- 役割ベースアクセス制御

### ✅ **コンテンツ管理（100%）**
- 高機能ブロックエディタ
- カテゴリ階層管理
- コメント承認システム
- SEO・OGP最適化

### ✅ **ユーザー管理（100%）**
- プロフィール管理
- SNSアカウント統合
- 通知設定
- 権限管理

### ✅ **WordPress移行（100%）**
- 完全XMLインポート
- カテゴリ・記事・メタデータ移行
- 多対多関係処理
- エラーハンドリング・検証

### ✅ **管理画面（95%）**
- レスポンシブダッシュボード
- 統計・分析表示
- 一括操作機能
- セキュリティ設定統合

## 🚀 デプロイ情報

### **本番環境設定**
- **OS**: Ubuntu 24.04 LTS推奨
- **Webサーバー**: Nginx + Gunicorn
- **データベース**: MySQL 8.0
- **SSL**: Let's Encrypt
- **メール**: AWS SES

### **デプロイファイル**
- `deploy.sh` - 自動デプロイスクリプト
- `deploy_manual.md` - 手動設定手順書
- `gunicorn_config.py` - WSGIサーバー設定
- `nginx_miniblog.conf` - Webサーバー設定
- `miniblog.service` - systemdサービス設定
- `.env.production` - 本番環境設定テンプレート

### **セキュリティ機能**
- fail2ban侵入検知・防御
- UFW ファイアウォール
- 自動バックアップスクリプト
- ログローテーション
- セキュリティヘッダー

## 📂 プロジェクト構造

```
mini-blog/
├── 🐍 Core Application
│   ├── app.py                 # メインアプリケーション
│   ├── admin.py               # 管理画面Blueprint
│   ├── models.py              # データベースモデル
│   ├── forms.py               # WTForms
│   └── wordpress_importer.py  # WordPress移行
├── 🚀 Production Deploy
│   ├── .env.production        # 本番環境設定
│   ├── gunicorn_config.py     # WSGIサーバー
│   ├── nginx_miniblog.conf    # Webサーバー
│   ├── miniblog.service       # systemd
│   ├── deploy.sh              # 自動デプロイ
│   └── deploy_manual.md       # 手順書
├── 📁 Application Structure
│   ├── static/                # CSS/JS/画像
│   ├── templates/             # Jinja2テンプレート
│   ├── migrations/            # データベース移行
│   └── scripts/               # 運用スクリプト
└── 📄 Configuration
    ├── requirements.txt       # Python依存関係
    ├── .gitignore            # Git除外設定
    └── README.md             # このファイル
```

## 🗄️ データベース設計

### **主要テーブル**
- **users**: 認証・プロフィール・2FA設定
- **articles**: 記事・SEO・公開設定
- **categories**: 階層カテゴリ・OGP設定
- **blocks**: ブロックデータ・順序管理
- **comments**: コメント・承認システム
- **email_change_requests**: 安全なメール変更

### **関係性**
- **多対多**: Articles ↔ Categories
- **一対多**: Users → Articles → Blocks
- **階層**: Categories (parent/child)

## 🔧 ローカル開発環境

### **要件**
- Python 3.10+
- MySQL 8.0+
- Node.js（オプション）

### **セットアップ**
```bash
# リポジトリクローン
git clone https://github.com/your-username/mini-blog.git
cd mini-blog

# Python仮想環境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 依存関係インストール
pip install -r requirements.txt

# 環境設定
cp .env.production .env
# .envファイルを編集

# データベース初期化
flask db upgrade

# 開発サーバー起動
python app.py
```

## ⚙️ 本番デプロイ手順

### **1. AWS Lightsail準備**
- Ubuntu 24.04 LTSインスタンス作成
- 静的IP取得
- SSH鍵設定

### **2. 自動デプロイ実行**
```bash
# サーバーでプロジェクトクローン
git clone https://github.com/your-username/mini-blog.git
cd mini-blog

# 自動デプロイ実行
sudo ./deploy.sh
```

### **3. 手動設定完了**
- `deploy_manual.md` の手順に従って設定
- MySQL データベース・ユーザー作成
- SSL証明書取得
- AWS SES認証情報設定

## 🔒 セキュリティ機能

### **認証・認可**
- 2段階認証（TOTP）必須
- セッション管理・タイムアウト
- パスワード強度チェック
- ブルートフォース対策

### **データ保護**
- CSRF攻撃対策
- XSS攻撃対策  
- SQLインジェクション対策
- ファイルアップロード検証

### **インフラセキュリティ**
- セキュリティヘッダー
- HTTPS強制リダイレクト
- fail2ban侵入検知
- ファイアウォール設定

## 📊 プロジェクト統計

### **コードベース**
- **総行数**: ~15,000行
- **実装ファイル**: 50+
- **テンプレート**: 25+ Jinja2
- **APIエンドポイント**: 30+
- **JavaScript関数**: 100+

### **機能完成度**
- **認証システム**: 100%
- **ブロックエディタ**: 100%
- **ユーザー管理**: 100%
- **WordPress移行**: 100%
- **管理画面**: 95%
- **本番デプロイ**: 100%

## 🚀 **プロジェクト状況**

**現在の状態**: 本番デプロイ準備完了（95%完成）
**技術水準**: エンタープライズレベルのセキュリティ・機能・設計
**デプロイ対応**: AWS Lightsail/EC2 完全対応

---

## 📞 サポート・貢献

- **Issues**: 問題報告・機能要望
- **Pull Requests**: 貢献歓迎
- **Documentation**: Wiki・手順書完備

**Made with ❤️ using Flask, MySQL, and modern web technologies**