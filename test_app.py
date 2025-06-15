#!/usr/bin/env python3
"""アプリケーションテストスクリプト"""

import requests
import sys
from time import sleep
import subprocess
import os
import signal

def start_app():
    """アプリケーションを起動"""
    print("Flask アプリケーションを起動中...")
    proc = subprocess.Popen(['python', 'app.py'], 
                          stdout=subprocess.PIPE, 
                          stderr=subprocess.PIPE)
    sleep(3)  # アプリケーションの起動を待つ
    return proc

def test_homepage():
    """ホームページのテスト"""
    try:
        response = requests.get('http://localhost:5000/')
        print(f"ホームページ: HTTP {response.status_code}")
        
        # セキュリティヘッダーの確認
        headers_to_check = [
            'X-Content-Type-Options',
            'X-Frame-Options', 
            'X-XSS-Protection',
            'Content-Security-Policy'
        ]
        
        print("セキュリティヘッダー:")
        for header in headers_to_check:
            value = response.headers.get(header, 'なし')
            print(f"  {header}: {value}")
            
        return response.status_code == 200
    except Exception as e:
        print(f"ホームページテストエラー: {e}")
        return False

def test_login_page():
    """ログインページのテスト"""
    try:
        response = requests.get('http://localhost:5000/login/')
        print(f"ログインページ: HTTP {response.status_code}")
        
        # CSRFトークンの確認
        csrf_present = 'csrf_token' in response.text
        print(f"CSRF保護: {'有効' if csrf_present else '無効'}")
        
        return response.status_code == 200 and csrf_present
    except Exception as e:
        print(f"ログインページテストエラー: {e}")
        return False

def test_admin_access():
    """管理画面アクセステスト（認証なし）"""
    try:
        response = requests.get('http://localhost:5000/admin/', allow_redirects=False)
        print(f"管理画面（未認証）: HTTP {response.status_code}")
        
        # 認証が必要であることを確認（リダイレクトされるべき）
        if response.status_code == 302:
            location = response.headers.get('Location', '')
            redirect_to_login = '/login' in location
            print(f"認証保護: {'有効 (ログインページにリダイレクト)' if redirect_to_login else '無効'}")
            return redirect_to_login
        else:
            print(f"認証保護: 無効 (直接アクセス可能)")
            return False
    except Exception as e:
        print(f"管理画面テストエラー: {e}")
        return False

def main():
    """メインテスト関数"""
    print("=== Flask ミニブログ セキュリティテスト ===\n")
    
    # アプリケーション起動
    proc = start_app()
    
    try:
        # テスト実行
        tests = [
            ("ホームページ", test_homepage),
            ("ログインページ", test_login_page), 
            ("管理画面保護", test_admin_access)
        ]
        
        results = []
        for test_name, test_func in tests:
            print(f"\n--- {test_name} テスト ---")
            result = test_func()
            results.append((test_name, result))
            print(f"結果: {'✅ 成功' if result else '❌ 失敗'}")
        
        # 結果サマリー
        print("\n=== テスト結果サマリー ===")
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✅ 成功" if result else "❌ 失敗"
            print(f"{test_name}: {status}")
            
        print(f"\n合計: {passed}/{total} テストが成功")
        
        if passed == total:
            print("🎉 全てのテストが成功しました！")
            return 0
        else:
            print("⚠️  一部のテストが失敗しました。")
            return 1
            
    finally:
        # アプリケーション停止
        print("\nアプリケーションを停止中...")
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()

if __name__ == '__main__':
    sys.exit(main())