# Mini Blog 手動デプロイ手順

自動スクリプト実行後の手動設定手順です。

## 🔧 1. 環境変数設定

```bash
# 本番用設定をコピー
cd /opt/miniblog
sudo cp .env.production .env

# 設定ファイル編集
sudo nano .env
```

### 必須変更項目:
- `YOUR_SECURE_PASSWORD` → 強力なMySQLパスワード
- `YOUR_PRODUCTION_SECRET_KEY_64_CHARACTERS_LONG_SECURE_STRING` → 64文字の秘密鍵
- `YOUR_AWS_ACCESS_KEY` → AWS アクセスキー
- `YOUR_AWS_SECRET_KEY` → AWS シークレットキー
- `yourdomain.com` → 実際のドメイン名

## 🗄️ 2. MySQL データベース設定

```bash
# MySQL にログイン
sudo mysql -u root -p

# データベース・ユーザー作成
CREATE DATABASE miniblog_prod CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'miniblog_user'@'localhost' IDENTIFIED BY 'YOUR_SECURE_PASSWORD';
GRANT ALL PRIVILEGES ON miniblog_prod.* TO 'miniblog_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

## 📊 3. データベースマイグレーション

```bash
cd /opt/miniblog
sudo -u www-data /opt/miniblog/venv/bin/flask db upgrade
```

## 🔐 4. SSL証明書取得

```bash
# ドメイン名を実際のものに変更
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

## 🚀 5. サービス開始

```bash
# サービス開始
sudo systemctl start miniblog
sudo systemctl start nginx

# 状態確認
sudo systemctl status miniblog
sudo systemctl status nginx

# ログ確認
sudo journalctl -u miniblog -f
```

## 🔍 6. 動作確認

```bash
# アプリケーション動作確認
curl -I https://yourdomain.com

# SSL証明書確認
curl -I https://yourdomain.com | grep -i ssl
```

## 📝 7. 初期管理者作成

ブラウザでサイトにアクセスし、管理者アカウントを作成してください。

## 🔒 8. セキュリティ設定強化

### SSH設定
```bash
sudo nano /etc/ssh/sshd_config
# PasswordAuthentication no
# PermitRootLogin no
sudo systemctl restart ssh
```

### fail2ban設定
```bash
sudo nano /etc/fail2ban/jail.local
# [sshd]
# enabled = true
# port = ssh
# filter = sshd
# logpath = /var/log/auth.log
# maxretry = 3
# bantime = 3600

sudo systemctl restart fail2ban
```

## 📊 9. ログローテーション設定

```bash
sudo nano /etc/logrotate.d/miniblog
```

内容:
```
/var/log/gunicorn/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
    postrotate
        systemctl reload miniblog
    endscript
}
```

## 🔄 10. 自動バックアップ設定

```bash
# バックアップスクリプト作成
sudo nano /opt/backup_miniblog.sh
```

内容:
```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
mysqldump -u miniblog_user -p miniblog_prod > /opt/backup/db_$DATE.sql
tar -czf /opt/backup/files_$DATE.tar.gz /opt/miniblog/static/uploads/
```

```bash
# 実行権限付与
sudo chmod +x /opt/backup_miniblog.sh

# cron設定（毎日午前3時）
echo "0 3 * * * /opt/backup_miniblog.sh" | sudo crontab -
```

## ✅ 完了チェックリスト

- [ ] MySQL データベース・ユーザー作成完了
- [ ] .env ファイル設定完了
- [ ] データベースマイグレーション完了
- [ ] SSL証明書取得完了
- [ ] miniblog サービス起動完了
- [ ] nginx サービス起動完了
- [ ] ドメインでのアクセス確認完了
- [ ] 管理者アカウント作成完了
- [ ] セキュリティ設定完了
- [ ] バックアップ設定完了

## 🆘 トラブルシューティング

### サービス起動エラー
```bash
sudo journalctl -u miniblog --no-pager -l
```

### nginx設定エラー
```bash
sudo nginx -t
sudo tail -f /var/log/nginx/error.log
```

### データベース接続エラー
```bash
mysql -u miniblog_user -p miniblog_prod
```

### SSL証明書エラー
```bash
sudo certbot certificates
sudo certbot renew --dry-run
```