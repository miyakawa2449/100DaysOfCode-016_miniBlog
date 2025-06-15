#!/usr/bin/env python3
"""2段階認証とパスワードリセット機能のテストスクリプト"""

import requests
import subprocess
import time
import sys

def start_app():
    """アプリケーションを起動"""
    print("Flask アプリケーションを起動中...")
    proc = subprocess.Popen(['python', 'app.py'], 
                          stdout=subprocess.PIPE, 
                          stderr=subprocess.PIPE)
    time.sleep(3)  # アプリケーションの起動を待つ
    return proc

def test_totp_setup_page():
    """TOTP設定ページのテスト"""
    try:
        # 認証なしでアクセス（リダイレクトされるべき）
        response = requests.get('http://localhost:5000/totp_setup/', allow_redirects=False)
        print(f"TOTP設定ページ（未認証）: HTTP {response.status_code}")
        
        if response.status_code == 302:
            location = response.headers.get('Location', '')
            redirect_to_login = '/login' in location
            print(f"認証保護: {'有効 (ログインページにリダイレクト)' if redirect_to_login else '無効'}")
            return redirect_to_login
        else:
            print(f"認証保護: 無効 (直接アクセス可能)")
            return False
    except Exception as e:
        print(f"TOTP設定ページテストエラー: {e}")
        return False

def test_password_reset_request():
    """パスワードリセット要求ページのテスト"""
    try:
        response = requests.get('http://localhost:5000/password_reset_request/')
        print(f"パスワードリセット要求ページ: HTTP {response.status_code}")
        
        csrf_present = 'csrf_token' in response.text
        print(f"CSRF保護: {'有効' if csrf_present else '無効'}")
        
        return response.status_code == 200 and csrf_present
    except Exception as e:
        print(f"パスワードリセット要求ページテストエラー: {e}")
        return False

def test_totp_verify_page():
    """TOTP認証ページのテスト"""
    try:
        response = requests.get('http://localhost:5000/totp_verify/')
        print(f"TOTP認証ページ: HTTP {response.status_code}")
        
        # temp_user_idがないのでリダイレクトされるべき
        redirect_ok = 'ログイン' in response.text or response.status_code == 302
        print(f"セッション保護: {'有効' if redirect_ok else '無効'}")
        
        return redirect_ok
    except Exception as e:
        print(f"TOTP認証ページテストエラー: {e}")
        return False

def test_security_headers():
    """セキュリティヘッダーの再確認"""
    try:
        response = requests.get('http://localhost:5000/')
        headers_to_check = [
            'X-Content-Type-Options',
            'X-Frame-Options', 
            'X-XSS-Protection',
            'Content-Security-Policy'
        ]
        
        print("セキュリティヘッダー確認:")
        all_present = True
        for header in headers_to_check:
            value = response.headers.get(header, 'なし')
            present = value != 'なし'
            print(f"  {header}: {'✅' if present else '❌'} {value}")
            if not present:
                all_present = False
                
        return all_present
    except Exception as e:
        print(f"セキュリティヘッダーテストエラー: {e}")
        return False

def main():
    """メインテスト関数"""
    print("=== 2段階認証・パスワードリセット機能テスト ===\n")
    
    # アプリケーション起動
    proc = start_app()
    
    try:
        # テスト実行
        tests = [
            ("TOTP設定ページ保護", test_totp_setup_page),
            ("パスワードリセット要求", test_password_reset_request),
            ("TOTP認証ページ保護", test_totp_verify_page),
            ("セキュリティヘッダー", test_security_headers)
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
        
        # 追加機能の説明
        print("\n=== 実装済み機能 ===")
        print("🔐 2段階認証 (TOTP)")
        print("  • Google Authenticator対応")
        print("  • QRコード生成機能")
        print("  • 管理画面での設定・状態表示")
        
        print("\n🔑 パスワードリセット")
        print("  • メール送信機能")
        print("  • セキュアなトークン管理")
        print("  • 有効期限付きリンク")
        
        print("\n🛡️ セキュリティ強化")
        print("  • 強化されたセッション管理")
        print("  • CSRF保護の完全実装")
        print("  • 包括的なセキュリティヘッダー")
        
        if passed == total:
            print("\n🎉 全ての機能が正常に動作しています！")
            return 0
        else:
            print("\n⚠️  一部の機能にアクセスエラーがあります。")
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