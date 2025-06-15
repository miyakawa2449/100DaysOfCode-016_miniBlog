#!/usr/bin/env python3
"""2段階認証手動テストガイド"""

import requests
import time
from bs4 import BeautifulSoup

BASE_URL = "http://localhost:5000"

def get_csrf_token(session, url):
    """CSRFトークンを取得"""
    response = session.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    csrf_input = soup.find('input', {'name': 'csrf_token'})
    return csrf_input['value'] if csrf_input else None

def login_admin(session):
    """管理者でログイン"""
    print("🔑 管理者ログインを実行中...")
    
    # ログインページを取得
    login_url = f"{BASE_URL}/login/"
    csrf_token = get_csrf_token(session, login_url)
    
    if not csrf_token:
        print("❌ CSRFトークンの取得に失敗")
        return False
    
    # ログイン実行
    login_data = {
        'csrf_token': csrf_token,
        'email': 'admin@example.com',
        'password': 'AdminPass123!',
        'submit': 'ログイン'
    }
    
    response = session.post(login_url, data=login_data, allow_redirects=True)
    
    # ログイン成功確認
    if 'ダッシュボード' in response.text or 'dashboard' in response.url:
        print("✅ 管理者ログイン成功")
        return True
    elif 'totp_verify' in response.url:
        print("✅ 2段階認証ページにリダイレクト")
        return True
    elif response.url.endswith('/') and 'ログアウト' not in response.text:
        # ホームページにリダイレクトされた場合、管理画面にアクセスしてみる
        print("📍 ホームページにリダイレクト、管理画面アクセスを試行中...")
        admin_response = session.get(f"{BASE_URL}/admin/")
        if 'ダッシュボード' in admin_response.text or admin_response.status_code == 200:
            print("✅ 管理者ログイン成功（管理画面アクセス確認）")
            return True
        else:
            print(f"❌ 管理画面アクセス失敗 - Status: {admin_response.status_code}")
            return False
    else:
        print(f"❌ ログイン失敗 - URL: {response.url}")
        print(f"レスポンス内容の一部: {response.text[:200]}...")
        return False

def access_totp_setup(session):
    """TOTP設定ページにアクセス"""
    print("\n🔐 2段階認証設定ページにアクセス中...")
    
    setup_url = f"{BASE_URL}/totp_setup/"
    response = session.get(setup_url)
    
    if response.status_code == 200 and 'QRコード' in response.text:
        print("✅ TOTP設定ページアクセス成功")
        
        # QRコードが生成されているか確認
        if 'data:image/png;base64,' in response.text:
            print("✅ QRコード生成確認")
            
            # シークレットキーも表示されているか確認
            soup = BeautifulSoup(response.text, 'html.parser')
            secret_element = soup.find('code')
            if secret_element:
                secret = secret_element.text.strip()
                print(f"✅ TOTPシークレット: {secret}")
                return True, secret
            else:
                print("❌ TOTPシークレットが見つかりません")
                return False, None
        else:
            print("❌ QRコードが生成されていません")
            return False, None
    else:
        print(f"❌ TOTP設定ページアクセス失敗 - Status: {response.status_code}")
        return False, None

def test_password_reset_flow():
    """パスワードリセットフローのテスト"""
    print("\n🔑 パスワードリセット機能テスト...")
    
    session = requests.Session()
    
    # パスワードリセット要求ページアクセス
    reset_url = f"{BASE_URL}/password_reset_request/"
    csrf_token = get_csrf_token(session, reset_url)
    
    if not csrf_token:
        print("❌ CSRFトークンの取得に失敗")
        return False
    
    # パスワードリセット要求
    reset_data = {
        'csrf_token': csrf_token,
        'email': 'admin@example.com',
        'submit': 'パスワードリセット要求'
    }
    
    response = session.post(reset_url, data=reset_data, allow_redirects=True)
    
    if 'ログイン' in response.text and response.status_code == 200:
        print("✅ パスワードリセット要求送信成功")
        print("💡 開発環境ではコンソールログでリセットURLを確認してください")
        return True
    else:
        print(f"❌ パスワードリセット要求失敗")
        return False

def main():
    """メインテスト実行"""
    print("=== Flask MiniBlog 2段階認証 手動テストガイド ===\n")
    
    print("📋 テスト手順:")
    print("1. 管理者ログイン")
    print("2. TOTP設定ページアクセス")
    print("3. QRコード生成確認")
    print("4. 手動でGoogle Authenticator設定")
    print("5. 2段階認証有効化")
    print("6. ログアウト→ログインで2段階認証テスト")
    print("7. パスワードリセット機能テスト")
    
    print("\n" + "="*50)
    
    # セッション開始
    session = requests.Session()
    
    # Step 1: 管理者ログイン
    if not login_admin(session):
        print("❌ 管理者ログインに失敗したため、テストを中止します")
        return
    
    # Step 2 & 3: TOTP設定ページアクセス
    success, secret = access_totp_setup(session)
    if not success:
        print("❌ TOTP設定ページアクセスに失敗")
        return
    
    # Step 4: 手動設定手順の表示
    print("\n" + "="*50)
    print("📱 Google Authenticatorでの手動設定手順:")
    print("1. スマートフォンでGoogle Authenticatorアプリを開く")
    print("2. 「+」ボタンをタップ")
    print("3. 「QRコードをスキャン」を選択")
    print("4. ブラウザで以下のURLにアクセス:")
    print(f"   {BASE_URL}/totp_setup/")
    print("5. 表示されたQRコードをスキャン")
    print(f"6. または手動で以下のキーを入力: {secret}")
    print("7. アプリに表示される6桁のコードを確認")
    print("8. ブラウザの設定画面でそのコードを入力")
    print("9. '2段階認証を有効化'ボタンをクリック")
    
    # Step 7: パスワードリセット機能テスト
    test_password_reset_flow()
    
    print("\n" + "="*50)
    print("🎯 次のステップ:")
    print("1. ブラウザでログアウト")
    print("2. 再度ログイン（admin@example.com / AdminPass123!）")
    print("3. 2段階認証画面でGoogle Authenticatorのコードを入力")
    print("4. 正常にログインできることを確認")
    
    print("\n📊 アクセス情報:")
    print(f"ログインURL: {BASE_URL}/login/")
    print(f"TOTP設定URL: {BASE_URL}/totp_setup/")
    print(f"管理画面URL: {BASE_URL}/admin/")
    print(f"パスワードリセットURL: {BASE_URL}/password_reset_request/")
    
    print("\n✅ 自動テスト部分は完了しました!")
    print("📱 続いてGoogle Authenticatorアプリでの手動設定を行ってください。")

if __name__ == '__main__':
    try:
        import bs4
    except ImportError:
        print("beautifulsoup4が必要です: pip install beautifulsoup4")
        exit(1)
    
    main()