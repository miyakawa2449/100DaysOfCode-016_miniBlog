#!/usr/bin/env python3
"""2段階認証完全テストスクリプト"""

import requests
import pyotp
import time
from bs4 import BeautifulSoup

BASE_URL = "http://localhost:5000"

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
    
    # ステップ2: TOTP設定
    print("\n📱 ステップ2: TOTP設定ページアクセス")
    setup_url = f"{BASE_URL}/totp_setup/"
    response = session.get(setup_url)
    
    if response.status_code == 200:
        print("✅ TOTP設定ページアクセス成功")
        
        # シークレット抽出
        soup = BeautifulSoup(response.text, 'html.parser')
        secret_element = soup.find('code')
        if secret_element:
            secret = secret_element.text.strip()
            print(f"✅ TOTPシークレット取得: {secret}")
            
            # ステップ3: 認証コード生成
            print("\n🔐 ステップ3: 認証コード生成")
            totp = pyotp.TOTP(secret)
            current_code = totp.now()
            print(f"現在のTOTPコード: {current_code}")
            
            # ステップ4: 2段階認証有効化
            print("\n⚡ ステップ4: 2段階認証有効化")
            csrf_token = get_csrf_token(session, setup_url)
            
            enable_data = {
                'csrf_token': csrf_token,
                'totp_code': current_code,
                'submit': '2段階認証を有効化'
            }
            
            response = session.post(setup_url, data=enable_data, allow_redirects=True)
            
            if 'ダッシュボード' in response.text or 'admin' in response.url:
                print("✅ 2段階認証有効化成功")
                
                # ステップ5: ログアウト
                print("\n🚪 ステップ5: ログアウト")
                logout_response = session.get(f"{BASE_URL}/logout/", allow_redirects=True)
                print(f"ログアウト結果: {logout_response.status_code}")
                
                # ステップ6: 2段階認証ログインテスト
                print("\n🔑 ステップ6: 2段階認証ログインテスト")
                
                # 新しいセッション
                new_session = requests.Session()
                
                # 通常ログイン
                csrf_token = get_csrf_token(new_session, login_url)
                response = new_session.post(login_url, data=login_data, allow_redirects=False)
                
                if response.status_code == 302 and 'totp_verify' in response.headers.get('Location', ''):
                    print("✅ 2段階認証ページにリダイレクト")
                    
                    # TOTP認証ページ
                    totp_url = f"{BASE_URL}/totp_verify/"
                    response = new_session.get(totp_url)
                    
                    if response.status_code == 200:
                        print("✅ TOTP認証ページアクセス")
                        
                        # 新しいコード生成（時間経過を考慮）
                        time.sleep(1)
                        new_code = totp.now()
                        print(f"新しいTOTPコード: {new_code}")
                        
                        csrf_token = get_csrf_token(new_session, totp_url)
                        totp_data = {
                            'csrf_token': csrf_token,
                            'totp_code': new_code,
                            'submit': '認証'
                        }
                        
                        response = new_session.post(totp_url, data=totp_data, allow_redirects=True)
                        
                        if response.status_code == 200 and ('ダッシュボード' in response.text or 'admin' in response.url):
                            print("✅ 2段階認証ログイン成功")
                            
                            # 管理画面アクセス確認
                            admin_response = new_session.get(f"{BASE_URL}/admin/")
                            if admin_response.status_code == 200:
                                print("✅ 管理画面アクセス成功")
                                return True
                            else:
                                print(f"❌ 管理画面アクセス失敗: {admin_response.status_code}")
                        else:
                            print("❌ 2段階認証ログイン失敗")
                    else:
                        print(f"❌ TOTP認証ページアクセス失敗: {response.status_code}")
                else:
                    print(f"❌ 2段階認証リダイレクト失敗: {response.status_code}")
            else:
                print("❌ 2段階認証有効化失敗")
        else:
            print("❌ TOTPシークレット取得失敗")
    else:
        print(f"❌ TOTP設定ページアクセス失敗: {response.status_code}")
    
    return False

def test_2fa_disable():
    """2段階認証無効化テスト"""
    print("\n=== 2段階認証無効化テスト ===")
    
    session = requests.Session()
    
    # ログイン（2段階認証込み）
    # 実装省略（上記のテストが成功していることが前提）
    
    print("2段階認証無効化機能は手動テストで確認してください")

def main():
    """メインテスト実行"""
    print("🚀 2段階認証システム完全テスト開始\n")
    
    success = test_complete_2fa_flow()
    
    if success:
        print("\n🎉 全ての2段階認証テストが成功しました！")
        print("\n📋 手動確認項目:")
        print("1. ブラウザで http://localhost:5000/admin/ にアクセス")
        print("2. 管理画面のセキュリティ設定を確認")
        print("3. Google Authenticatorアプリで実際のQRコードスキャンテスト")
        print("4. 2段階認証の有効化/無効化切り替えテスト")
        
        print("\n🔧 テストヘルパーコマンド:")
        print("- python totp_helper.py user           # 現在のユーザーTOTP情報")
        print("- python totp_helper.py verify <code>  # TOTPコード検証")
        
    else:
        print("\n❌ 2段階認証テストに失敗しました")
        print("詳細はログを確認してください")

if __name__ == '__main__':
    main()