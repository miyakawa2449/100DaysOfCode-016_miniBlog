#!/usr/bin/env python3
"""2段階認証完全テストスクリプト（修正版）"""

import requests
import pyotp
import time
import subprocess
import sys
from bs4 import BeautifulSoup

BASE_URL = "http://localhost:5000"

def start_app():
    """アプリケーションを起動"""
    print("Flask アプリケーションを起動中...")
    proc = subprocess.Popen(['python', 'app.py'], 
                          stdout=subprocess.PIPE, 
                          stderr=subprocess.PIPE)
    time.sleep(3)  # アプリケーションの起動を待つ
    return proc

def get_csrf_token(session, url):
    """CSRFトークンを取得"""
    response = session.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    csrf_input = soup.find('input', {'name': 'csrf_token'})
    return csrf_input['value'] if csrf_input else None

def test_complete_2fa_flow():
    """完全な2段階認証フローテスト"""
    print("=== 2段階認証 完全フローテスト ===\n")
    
    session = requests.Session()
    
    # ステップ1: ログイン
    print("📝 ステップ1: 管理者ログイン")
    login_url = f"{BASE_URL}/login/"
    csrf_token = get_csrf_token(session, login_url)
    
    login_data = {
        'csrf_token': csrf_token,
        'email': 'admin@example.com',
        'password': 'AdminPass123!',
        'submit': 'ログイン'
    }
    
    response = session.post(login_url, data=login_data, allow_redirects=True)
    print(f"ログイン結果: {response.status_code}")
    
    # 2段階認証が有効な場合、TOTP認証ページにリダイレクトされる
    if 'totp_verify' in response.url:
        print("✅ 2段階認証ページにリダイレクト")
        
        # ステップ2: TOTP認証
        print("\n🔐 ステップ2: TOTP認証")
        totp_url = f"{BASE_URL}/totp_verify/"
        
        # 既知のシークレット使用
        secret = "HNAKAP6S2L7XZ7RVY5E73OZLUFKFOUMB"
        totp = pyotp.TOTP(secret)
        current_code = totp.now()
        print(f"現在のTOTPコード: {current_code}")
        
        csrf_token = get_csrf_token(session, totp_url)
        totp_data = {
            'csrf_token': csrf_token,
            'totp_code': current_code,
            'submit': '認証'
        }
        
        response = session.post(totp_url, data=totp_data, allow_redirects=True)
        
        print(f"DEBUG: TOTP認証レスポンス ステータス: {response.status_code}")
        print(f"DEBUG: TOTP認証レスポンス URL: {response.url}")
        print(f"DEBUG: TOTP認証レスポンス テキスト（最初の500文字）: {response.text[:500]}")
        
        if response.status_code == 200 and (response.url.endswith('/') or 'ホーム' in response.text or 'admin' in response.url):
            print("✅ 2段階認証ログイン成功")
            
            # ステップ3: 管理画面アクセス確認
            print("\n🎯 ステップ3: 管理画面アクセス確認")
            admin_response = session.get(f"{BASE_URL}/admin/")
            if admin_response.status_code == 200:
                print("✅ 管理画面アクセス成功")
                
                # ステップ4: ログアウト
                print("\n🚪 ステップ4: ログアウト")
                logout_response = session.get(f"{BASE_URL}/logout/", allow_redirects=True)
                print(f"ログアウト結果: {logout_response.status_code}")
                
                # ステップ5: 新規セッションでの2段階認証テスト
                print("\n🔄 ステップ5: 新規セッションで2段階認証テスト")
                return test_fresh_login()
                
            else:
                print(f"❌ 管理画面アクセス失敗: {admin_response.status_code}")
                return False
        else:
            print("❌ 2段階認証ログイン失敗")
            return False
    else:
        print("❌ 2段階認証リダイレクトなし - 2段階認証が設定されていない可能性があります")
        return False

def test_fresh_login():
    """新しいセッションでの2段階認証テスト"""
    new_session = requests.Session()
    
    # 通常ログイン
    login_url = f"{BASE_URL}/login/"
    csrf_token = get_csrf_token(new_session, login_url)
    
    login_data = {
        'csrf_token': csrf_token,
        'email': 'admin@example.com',
        'password': 'AdminPass123!',
        'submit': 'ログイン'
    }
    
    response = new_session.post(login_url, data=login_data, allow_redirects=False)
    
    if response.status_code == 302 and 'totp_verify' in response.headers.get('Location', ''):
        print("✅ 新セッションで2段階認証ページにリダイレクト")
        
        # TOTP認証ページ
        totp_url = f"{BASE_URL}/totp_verify/"
        response = new_session.get(totp_url)
        
        if response.status_code == 200:
            print("✅ TOTP認証ページアクセス成功")
            
            # 新しいコード生成
            secret = "HNAKAP6S2L7XZ7RVY5E73OZLUFKFOUMB"
            totp = pyotp.TOTP(secret)
            new_code = totp.now()
            print(f"新しいTOTPコード: {new_code}")
            
            csrf_token = get_csrf_token(new_session, totp_url)
            totp_data = {
                'csrf_token': csrf_token,
                'totp_code': new_code,
                'submit': '認証'
            }
            
            response = new_session.post(totp_url, data=totp_data, allow_redirects=True)
            
            if response.status_code == 200 and (response.url.endswith('/') or 'ホーム' in response.text or 'admin' in response.url):
                print("✅ 新セッションでの2段階認証ログイン成功")
                
                # 管理画面アクセス確認
                admin_response = new_session.get(f"{BASE_URL}/admin/")
                if admin_response.status_code == 200:
                    print("✅ 新セッションでの管理画面アクセス成功")
                    return True
                else:
                    print(f"❌ 新セッションでの管理画面アクセス失敗: {admin_response.status_code}")
                    return False
            else:
                print("❌ 新セッションでの2段階認証ログイン失敗")
                return False
        else:
            print(f"❌ TOTP認証ページアクセス失敗: {response.status_code}")
            return False
    else:
        print(f"❌ 新セッションでの2段階認証リダイレクト失敗: {response.status_code}")
        return False

def main():
    """メインテスト実行"""
    print("🚀 2段階認証システム完全テスト開始\n")
    
    # アプリケーション起動
    proc = start_app()
    
    try:
        success = test_complete_2fa_flow()
        
        if success:
            print("\n🎉 全ての2段階認証テストが成功しました！")
            print("\n📋 テスト完了項目:")
            print("1. ✅ 管理者ログイン")
            print("2. ✅ 2段階認証フロー")
            print("3. ✅ 管理画面アクセス")
            print("4. ✅ ログアウト/ログイン")
            print("5. ✅ 新セッションでの2段階認証")
            
            print("\n🔧 手動確認推奨項目:")
            print("- ブラウザで http://localhost:5000/admin/ にアクセス")
            print("- Google Authenticatorアプリでの実際のQRコードスキャンテスト")
            print("- 2段階認証の有効化/無効化切り替えテスト")
            
        else:
            print("\n❌ 2段階認証テストに失敗しました")
            print("詳細はログを確認してください")
            
    finally:
        # アプリケーション停止
        print("\nアプリケーションを停止中...")
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()

if __name__ == '__main__':
    main()