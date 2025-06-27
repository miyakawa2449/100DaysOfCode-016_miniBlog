#!/usr/bin/env python3
"""
管理パネル機能テスト
ログイン後の管理機能の動作確認
"""

import requests
import time
from urllib.parse import urljoin

BASE_URL = "http://127.0.0.1:5001"

def test_login():
    """ログインテスト"""
    login_url = urljoin(BASE_URL, "/login/")
    
    # ログインページにアクセス
    session = requests.Session()
    response = session.get(login_url)
    
    if response.status_code != 200:
        print(f"❌ ログインページアクセス失敗: {response.status_code}")
        return None
    
    print("✅ ログインページアクセス: 成功")
    
    # CSRFトークンを取得
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')
    csrf_token = soup.find('input', {'name': 'csrf_token'})
    
    if not csrf_token:
        print("❌ CSRFトークンが見つかりません")
        return None
    
    # ログイン実行
    login_data = {
        'email': 'admin@example.com',
        'password': 'admin',
        'csrf_token': csrf_token['value']
    }
    
    response = session.post(login_url, data=login_data)
    
    if response.status_code == 200 and 'ログイン' not in response.text:
        print("✅ ログイン: 成功")
        return session
    else:
        print(f"❌ ログイン失敗: {response.status_code}")
        return None

def test_admin_pages(session):
    """管理ページのテスト"""
    admin_pages = [
        ("/admin/", "管理ダッシュボード"),
        ("/admin/articles/", "記事管理"),
        ("/admin/categories/", "カテゴリ管理"),
        ("/admin/users/", "ユーザー管理"),
        ("/admin/comments/", "コメント管理"),
        ("/admin/settings/", "設定"),
    ]
    
    passed = 0
    for url, description in admin_pages:
        try:
            response = session.get(urljoin(BASE_URL, url), timeout=10)
            if response.status_code == 200:
                print(f"✅ {description}: アクセス成功")
                passed += 1
            else:
                print(f"❌ {description}: {response.status_code}")
        except Exception as e:
            print(f"❌ {description}: エラー - {e}")
        
        time.sleep(0.5)
    
    return passed, len(admin_pages)

def main():
    print("🚀 管理パネル機能テスト開始")
    print("=" * 60)
    
    # ログインテスト
    session = test_login()
    if not session:
        print("❌ ログインに失敗したため、テストを中断します")
        return False
    
    print("\n📊 管理ページアクセステスト:")
    passed, total = test_admin_pages(session)
    
    print(f"\n📊 テスト結果: {passed}/{total} 成功")
    
    if passed >= total * 0.8:
        print("🎉 管理パネルは正常に動作しています！")
        return True
    else:
        print("⚠️  一部の管理機能にアクセスできません")
        return False

if __name__ == "__main__":
    try:
        import bs4
    except ImportError:
        print("❌ beautifulsoup4が必要です: pip install beautifulsoup4")
        exit(1)
    
    success = main()
    exit(0 if success else 1)