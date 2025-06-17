# 管理者パスワードリセットスクリプト
from app import app, User, db
from werkzeug.security import generate_password_hash

def reset_admin_password(new_password):
    with app.app_context():
        admin_user = User.query.filter_by(email='admin@example.com').first()
        if admin_user:
            admin_user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            print(f"管理者パスワードが正常に更新されました: {admin_user.email}")
        else:
            print("admin@example.com のユーザーが見つかりません")

if __name__ == '__main__':
    new_password = input("新しいパスワードを入力してください: ")
    reset_admin_password(new_password)