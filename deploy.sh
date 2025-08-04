#!/bin/bash
# Mini Blog デプロイスクリプト

set -e  # エラー時に停止

echo "🚀 Mini Blog デプロイ開始..."

# 基本変数設定
APP_DIR="/opt/miniblog"
APP_USER="www-data"
VENV_DIR="$APP_DIR/venv"
SERVICE_NAME="miniblog"

# 色付きメッセージ関数
function echo_info() {
    echo -e "\033[1;34m[INFO]\033[0m $1"
}

function echo_success() {
    echo -e "\033[1;32m[SUCCESS]\033[0m $1"
}

function echo_error() {
    echo -e "\033[1;31m[ERROR]\033[0m $1"
}

# 1. システム更新
echo_info "システムパッケージ更新中..."
sudo apt update && sudo apt upgrade -y

# 2. 必要パッケージインストール
echo_info "必要パッケージインストール中..."
sudo apt install -y python3-pip python3-venv python3-dev
sudo apt install -y mysql-server nginx
sudo apt install -y fail2ban logwatch ufw
sudo apt install -y git htop iotop certbot python3-certbot-nginx

# 3. アプリケーションディレクトリ作成
echo_info "アプリケーションディレクトリ準備中..."
sudo mkdir -p $APP_DIR
sudo chown $APP_USER:$APP_USER $APP_DIR

# 4. Python仮想環境作成
echo_info "Python仮想環境作成中..."
sudo -u $APP_USER python3 -m venv $VENV_DIR
sudo -u $APP_USER $VENV_DIR/bin/pip install --upgrade pip

# 5. アプリケーションファイルコピー
echo_info "アプリケーションファイルコピー中..."
sudo cp -r . $APP_DIR/
sudo chown -R $APP_USER:$APP_USER $APP_DIR

# 6. Python依存関係インストール
echo_info "Python依存関係インストール中..."
sudo -u $APP_USER $VENV_DIR/bin/pip install -r $APP_DIR/requirements.txt
sudo -u $APP_USER $VENV_DIR/bin/pip install gunicorn

# 7. ログディレクトリ作成
echo_info "ログディレクトリ作成中..."
sudo mkdir -p /var/log/gunicorn
sudo mkdir -p /var/run/gunicorn
sudo chown $APP_USER:$APP_USER /var/log/gunicorn /var/run/gunicorn

# 8. MySQL設定
echo_info "MySQL設定中..."
echo "MySQL root パスワードを設定してください"
sudo mysql_secure_installation

# 9. systemdサービス設定
echo_info "systemdサービス設定中..."
sudo cp $APP_DIR/miniblog.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME

# 10. Nginx設定
echo_info "Nginx設定中..."
sudo cp $APP_DIR/nginx_miniblog.conf /etc/nginx/sites-available/miniblog
sudo ln -sf /etc/nginx/sites-available/miniblog /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t

# 11. ファイアウォール設定
echo_info "ファイアウォール設定中..."
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
sudo ufw --force enable

# 12. fail2ban設定
echo_info "fail2ban設定中..."
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

echo_success "基本デプロイ完了！"
echo ""
echo "🔧 次の手順を手動で実行してください："
echo "1. .env.production を .env にコピーして設定を調整"
echo "2. MySQL データベース・ユーザー作成"
echo "3. flask db upgrade でマイグレーション実行"
echo "4. ドメイン名でSSL証明書取得"
echo "5. サービス開始"
echo ""
echo "詳細は deploy_manual.md を参照してください"