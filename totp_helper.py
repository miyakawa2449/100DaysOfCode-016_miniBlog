#!/usr/bin/env python3
"""TOTP認証コード生成ヘルパー"""

import pyotp
import time

def generate_totp_codes(secret="HNAKAP6S2L7XZ7RVY5E73OZLUFKFOUMB"):
    """TOTPコードを生成して表示"""
    totp = pyotp.TOTP(secret)
    
    print("=== TOTP認証コード生成ヘルパー ===")
    print(f"シークレットキー: {secret}")
    print(f"現在のコード: {totp.now()}")
    print(f"有効期限まで: {30 - int(time.time()) % 30}秒")
    
    print("\n次の5つのコード:")
    for i in range(5):
        future_time = int(time.time()) + (i * 30)
        code = totp.at(future_time)
        remaining = (future_time % 30) if i == 0 else 30
        print(f"  {code} (有効期限: {remaining}秒後)")

def verify_code(secret, code):
    """コードを検証"""
    totp = pyotp.TOTP(secret)
    is_valid = totp.verify(code, valid_window=1)
    print(f"コード {code} の検証結果: {'✅ 有効' if is_valid else '❌ 無効'}")
    return is_valid

def get_current_user_totp():
    """現在のユーザーのTOTP情報を取得"""
    try:
        from app import app
        from models import User
        
        with app.app_context():
            admin = User.query.filter_by(role='admin').first()
            if admin and admin.totp_secret:
                print(f"管理者ユーザー: {admin.email}")
                print(f"TOTPシークレット: {admin.totp_secret}")
                print(f"2段階認証有効: {admin.totp_enabled}")
                
                if admin.totp_secret:
                    generate_totp_codes(admin.totp_secret)
                    return admin.totp_secret
            else:
                print("管理者のTOTPシークレットが設定されていません")
                return None
    except Exception as e:
        print(f"エラー: {e}")
        return None

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'user':
            # データベースから実際のユーザー情報を取得
            get_current_user_totp()
        elif sys.argv[1] == 'verify' and len(sys.argv) > 2:
            # コード検証
            secret = get_current_user_totp()
            if secret:
                verify_code(secret, sys.argv[2])
        else:
            # 指定されたシークレットでコード生成
            generate_totp_codes(sys.argv[1])
    else:
        # デフォルトシークレットでコード生成
        print("使用方法:")
        print("  python totp_helper.py                    # デフォルトシークレットでコード生成")
        print("  python totp_helper.py user               # データベースからユーザー情報取得")
        print("  python totp_helper.py verify <code>      # コード検証")
        print("  python totp_helper.py <secret>           # 指定シークレットでコード生成")
        print()
        generate_totp_codes()