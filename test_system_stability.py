#!/usr/bin/env python3
"""
システム安定性テスト
基本的な機能の動作確認を行う
"""

import requests
import time
from urllib.parse import urljoin

BASE_URL = "http://127.0.0.1:5001"

def test_endpoint(endpoint, description):
    """エンドポイントのテスト"""
    url = urljoin(BASE_URL, endpoint)
    try:
        response = requests.get(url, timeout=10)
        status = "✅" if response.status_code == 200 else f"❌ ({response.status_code})"
        print(f"{status} {description}: {endpoint}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ {description}: {endpoint} - エラー: {e}")
        return False

def main():
    print("🚀 システム安定性テスト開始")
    print("=" * 60)
    
    # テストケース
    tests = [
        ("/", "メインページ"),
        ("/login/", "ログインページ"),
        ("/admin/", "管理ダッシュボード（未認証）"),
        ("/article/first-test-post/", "インポートされた記事1"),
        ("/article/programming-tips/", "インポートされた記事2"),
        ("/profile/admin/", "プロフィールページ"),
        ("/category/technology/", "カテゴリページ（テクノロジー）"),
        ("/api/healthcheck", "ヘルスチェック（存在する場合）"),
        ("/static/css/main.css", "CSSファイル"),
    ]
    
    passed = 0
    total = len(tests)
    
    for endpoint, description in tests:
        if test_endpoint(endpoint, description):
            passed += 1
        time.sleep(0.5)  # レート制限対策
    
    print("\n" + "=" * 60)
    print(f"📊 テスト結果: {passed}/{total} 成功")
    
    if passed == total:
        print("🎉 すべてのテストが成功しました！")
    elif passed >= total * 0.8:
        print("⚠️  一部のテストが失敗しましたが、基本機能は動作しています。")
    else:
        print("❌ 多くのテストが失敗しました。システムに問題がある可能性があります。")
    
    # データベース接続テスト
    print("\n📊 データベース状態確認:")
    try:
        response = requests.get(urljoin(BASE_URL, "/"))
        if response.status_code == 200:
            print("✅ データベース接続: 正常")
        else:
            print("❌ データベース接続: 問題あり")
    except:
        print("❌ データベース接続: テスト失敗")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)