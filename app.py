from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Article  # ← ここをmodelsからインポート
from datetime import datetime
from admin import admin_bp  # admin.pyからインポート
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///miniblog.db'
app.config['UPLOAD_FOLDER'] = 'uploads/images'
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB

db.init_app(app)

# --- ルーティング例 ---
@app.route('/')
def home():
    articles = Article.query.order_by(Article.created_at.desc()).all()
    return render_template('home.html', articles=articles)

@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        pw = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, pw):
            session['user_id'] = user.id
            flash('ログインしました')
            return redirect(url_for('home'))
        flash('ログイン失敗')
    return render_template('login.html')

@app.route('/logout/')
def logout():
    session.pop('user_id', None)
    flash('ログアウトしました')
    return redirect(url_for('home'))

@app.route('/admin/article/upload_image/', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        flash('ファイルがありません')
        return redirect(request.referrer)
    file = request.files['image']
    if file.filename == '':
        flash('ファイルが選択されていません')
        return redirect(request.referrer)
    if file and allowed_file(file.filename):
        filename = file.filename
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(save_path)
        flash('アップロード成功')
        return redirect(request.referrer)
    else:
        flash('許可されていないファイル形式です')
        return redirect(request.referrer)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'jpg', 'jpeg', 'png', 'gif'}

# --- テンプレート例（home.html） ---
# 
# {% for article in articles %}
#   <h2><a href="{{ url_for('article_detail', slug=article.slug) }}">{{ article.title }}</a></h2>
#   <p>{{ article.body[:100] }}...</p>
# {% endfor %}

app.register_blueprint(admin_bp)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

