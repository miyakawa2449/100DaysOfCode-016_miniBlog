# Gunicorn設定ファイル
import multiprocessing
import os

# サーバーソケット
bind = "127.0.0.1:5000"
backlog = 2048

# ワーカープロセス
workers = multiprocessing.cpu_count() * 2 + 1  # 推奨式: (2 x CPU cores) + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# 最大リクエスト数（メモリリーク対策）
max_requests = 1000
max_requests_jitter = 50

# プロセス管理
preload_app = True
daemon = False
pidfile = "/var/run/gunicorn/miniblog.pid"
user = "www-data"
group = "www-data"
tmp_upload_dir = None

# ログ設定
accesslog = "/var/log/gunicorn/miniblog_access.log"
errorlog = "/var/log/gunicorn/miniblog_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# セキュリティ
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# パフォーマンス
enable_stdio_inheritance = True