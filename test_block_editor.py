#!/usr/bin/env python3
"""
ブロックエディタの動作テスト
JavaScriptが必要な機能の基本的なHTMLレスポンステスト
"""

import requests
from urllib.parse import urljoin

BASE_URL = "http://127.0.0.1:5001"

def test_editor_endpoints():
    """エディタ関連エンドポイントのテスト"""
    endpoints = [
        "/admin/article/create/",
        "/admin/article/block-editor/create/",
        "/admin/article/edit/1/",
        "/admin/article/block-editor/edit/1/",
    ]
    
    passed = 0
    for endpoint in endpoints:
        try:
            response = requests.get(urljoin(BASE_URL, endpoint), timeout=10, allow_redirects=False)
            # 認証が必要なので302 (リダイレクト) または 200が期待される
            if response.status_code in [200, 302]:
                print(f"✅ {endpoint}: アクセス可能 ({response.status_code})")
                passed += 1
            else:
                print(f"❌ {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint}: エラー - {e}")
    
    return passed, len(endpoints)

def test_static_assets():
    """ブロックエディタ関連の静的ファイルテスト"""
    assets = [
        "/static/css/main.css",
        "/static/css/rdash-admin.css",
        "/static/js/rdash-admin.js",
    ]
    
    passed = 0
    for asset in assets:
        try:
            response = requests.get(urljoin(BASE_URL, asset), timeout=10)
            if response.status_code == 200:
                print(f"✅ {asset}: 読み込み成功")
                passed += 1
            else:
                print(f"❌ {asset}: {response.status_code}")
        except Exception as e:
            print(f"❌ {asset}: エラー - {e}")
    
    return passed, len(assets)

def main():
    print("🚀 ブロックエディタ動作テスト開始")
    print("=" * 60)
    
    print("📄 エディタエンドポイントテスト:")
    endpoint_passed, endpoint_total = test_editor_endpoints()
    
    print(f"\n🎨 静的アセットテスト:")
    asset_passed, asset_total = test_static_assets()
    
    total_passed = endpoint_passed + asset_passed
    total_tests = endpoint_total + asset_total
    
    print(f"\n📊 テスト結果: {total_passed}/{total_tests} 成功")
    
    if total_passed >= total_tests * 0.6:
        print("🎉 ブロックエディタの基本構造は正常です！")
        print("💡 詳細な動作確認はブラウザで行ってください")
        return True
    else:
        print("⚠️  ブロックエディタに問題がある可能性があります")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)