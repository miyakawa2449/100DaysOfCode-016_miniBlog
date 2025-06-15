#!/usr/bin/env python3
"""管理画面認証デバッグスクリプト"""

import requests
import subprocess
import time

# アプリケーション起動
print("Flask アプリケーションを起動中...")
proc = subprocess.Popen(['python', 'app.py'], 
                      stdout=subprocess.PIPE, 
                      stderr=subprocess.PIPE)
time.sleep(3)

try:
    # 管理画面にアクセス
    response = requests.get('http://localhost:5000/admin/')
    print(f"Status Code: {response.status_code}")
    print(f"URL after redirect: {response.url}")
    print(f"Headers: {dict(response.headers)}")
    print(f"Response content preview:")
    print(response.text[:500])
    
finally:
    # アプリケーション停止
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()