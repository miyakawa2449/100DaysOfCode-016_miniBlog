from flask import Flask, render_template, redirect, url_for, flash, session, request
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
import os
from datetime import datetime
from admin import admin_bp

# models.py から db インスタンスとモデルクラスをインポートします
from models import db, User, Article, Category, Comment

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_default_secret_key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///miniblog.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads' # staticフォルダ内のuploadsを基本とする
app.config['CATEGORY_OGP_UPLOAD_FOLDER'] = os.path.join(app.config['UPLOAD_FOLDER'], 'category_ogp')
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

migrate = Migrate()  # Migrate インスタンスの作成はここでもOK

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.login_message = "このページにアクセスするにはログインが必要です。"
login_manager.login_message_category = "info"

# models.py からインポートした db をアプリケーションに登録します
db.init_app(app)
# migrate も同様に、インポートした db を使用します
migrate.init_app(app, db)
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))  # User.query は models.py からインポートした db に紐づく

app.register_blueprint(admin_bp, url_prefix='/admin')

@app.route('/')
def home():
    articles = Article.query.order_by(Article.created_at.desc()).all()
    return render_template('home.html', articles=articles)

@app.route('/login/', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            session['user_id'] = user.id
            flash('ログインしました。', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('home'))
        else:
            flash('メールアドレスまたはパスワードが正しくありません。', 'danger')
    return render_template('login.html')

@app.route('/logout/')
@login_required
def logout():
    logout_user()
    session.pop('user_id', None)
    flash('ログアウトしました。', 'info')
    return redirect(url_for('login'))

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
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/category/<slug>/')
def category_page(slug):
    category = Category.query.filter_by(slug=slug).first_or_404()
    
    if hasattr(category, 'articles') and category.articles is not None:
        page = request.args.get('page', 1, type=int)
        per_page = 10
        articles_pagination = category.articles.order_by(Article.created_at.desc()).paginate(page=page, per_page=per_page)
    else:
        from flask_sqlalchemy.pagination import Pagination
        articles_pagination = Pagination(query=None, page=1, per_page=per_page, total=0, items=[])

    return render_template('category_page.html', category=category, articles_pagination=articles_pagination)

@app.route('/article/<slug>/')
def article_detail(slug):
    article = Article.query.filter_by(slug=slug).first_or_404()
    return render_template('article_detail.html', article=article)

if __name__ == '__main__':
    app.run(debug=True)

