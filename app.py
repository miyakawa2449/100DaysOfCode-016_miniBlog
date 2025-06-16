from flask import Flask, render_template, redirect, url_for, flash, session, request
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
import os
from datetime import datetime
from admin import admin_bp
import logging  # logging モジュールをインポート
import bleach  # HTMLサニタイゼーション用
import qrcode
import io
import base64

# models.py から db インスタンスとモデルクラスをインポートします
from models import db, User, Article, Category, Comment
# forms.py からフォームクラスをインポート
from forms import LoginForm, TOTPVerificationForm, TOTPSetupForm, PasswordResetRequestForm, PasswordResetForm

from flask import Flask, send_from_directory
import time

app = Flask(__name__)

# 開発時のみ：静的ファイルのキャッシュを無効化
@app.after_request
def after_request(response):
    if app.debug:
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_default_secret_key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///miniblog.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads' # staticフォルダ内のuploadsを基本とする
app.config['CATEGORY_OGP_UPLOAD_FOLDER'] = os.path.join(app.config['UPLOAD_FOLDER'], 'category_ogp')
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
app.config['WTF_CSRF_TIME_LIMIT'] = 3600  # CSRFトークンの有効期限を1時間に設定
app.config['SESSION_COOKIE_SECURE'] = False  # 開発環境用（本番ではTrue）
app.config['SESSION_COOKIE_HTTPONLY'] = True  # XSS対策でJavaScriptからのアクセスを禁止
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF対策

# メール設定
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'localhost')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@miniblog.local')

app.debug = True  # デバッグモードを有効にする

# --- ロガー設定を追加 ---
if app.debug:
    # 開発モード時は DEBUG レベル以上のログをコンソールに出力
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)
    app.logger.addHandler(stream_handler)
    app.logger.setLevel(logging.DEBUG)
else:
    # 本番モード時は INFO レベル以上 (必要に応じてファイル出力なども検討)
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    app.logger.addHandler(stream_handler)
    app.logger.setLevel(logging.INFO)
# --- ここまで追加 ---

migrate = Migrate()  # Migrate インスタンスの作成はここでもOK
csrf = CSRFProtect()  # CSRF保護の初期化
mail = Mail()  # メール機能の初期化

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.login_message = "このページにアクセスするにはログインが必要です。"
login_manager.login_message_category = "info"

# models.py からインポートした db をアプリケーションに登録します
db.init_app(app)
# migrate も同様に、インポートした db を使用します
migrate.init_app(app, db)
csrf.init_app(app)  # CSRF保護を有効化
mail.init_app(app)  # メール機能を有効化
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))  # User.query は models.py からインポートした db に紐づく

# HTMLサニタイゼーション用ヘルパー関数
def sanitize_html(content):
    """HTMLコンテンツをサニタイズ"""
    allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li', 'a', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']
    allowed_attributes = {'a': ['href', 'title']}
    return bleach.clean(content, tags=allowed_tags, attributes=allowed_attributes, strip=True)

# セキュリティヘッダーの追加
@app.after_request
def after_request(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; img-src 'self' data:; font-src 'self' https://cdnjs.cloudflare.com"
    return response

# CSRF トークンをテンプレートで利用可能にする
@app.context_processor
def inject_csrf_token():
    from flask_wtf.csrf import generate_csrf
    from markupsafe import Markup
    
    def csrf_token():
        token = generate_csrf()
        return Markup(f'<input type="hidden" name="csrf_token" value="{token}"/>')
    
    return dict(csrf_token=csrf_token)

app.register_blueprint(admin_bp, url_prefix='/admin')

@app.route('/')
def home():
    articles = Article.query.order_by(Article.created_at.desc()).all()
    return render_template('home.html', articles=articles)

@app.route('/login/', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            # 2段階認証が有効な場合はTOTP画面へ
            if user.totp_enabled:
                session['temp_user_id'] = user.id
                return redirect(url_for('totp_verify'))
            else:
                login_user(user)
                session['user_id'] = user.id
                flash('ログインしました。', 'success')
                next_page = request.args.get('next')
                return redirect(next_page or url_for('home'))
        else:
            flash('メールアドレスまたはパスワードが正しくありません。', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/totp_verify/', methods=['GET', 'POST'])
def totp_verify():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    temp_user_id = session.get('temp_user_id')
    if not temp_user_id:
        flash('不正なアクセスです。', 'danger')
        return redirect(url_for('login'))
    
    user = User.query.get(temp_user_id)
    if not user or not user.totp_enabled:
        flash('2段階認証が設定されていません。', 'danger')
        return redirect(url_for('login'))
    
    form = TOTPVerificationForm()
    if form.validate_on_submit():
        totp_code = form.totp_code.data
        if user.verify_totp(totp_code):
            login_user(user)
            session['user_id'] = user.id
            session.pop('temp_user_id', None)
            flash('ログインしました。', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('home'))
        else:
            flash('認証コードが正しくありません。', 'danger')
    
    return render_template('totp_verify.html', form=form)

@app.route('/logout/')
@login_required
def logout():
    logout_user()
    session.pop('user_id', None)
    session.pop('temp_user_id', None)
    flash('ログアウトしました。', 'info')
    return redirect(url_for('login'))

@app.route('/totp_setup/', methods=['GET', 'POST'])
@login_required
def totp_setup():
    if current_user.totp_enabled:
        flash('2段階認証は既に有効になっています。', 'info')
        return redirect(url_for('admin.dashboard'))
    
    form = TOTPSetupForm()
    
    # QRコード生成
    if not current_user.totp_secret:
        current_user.generate_totp_secret()
        db.session.commit()
    
    totp_uri = current_user.get_totp_uri()
    
    # QRコード画像をBase64エンコードで生成
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(totp_uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    
    qr_code_base64 = base64.b64encode(img_buffer.getvalue()).decode()
    
    if form.validate_on_submit():
        totp_code = form.totp_code.data
        if current_user.verify_totp(totp_code):
            current_user.totp_enabled = True
            db.session.commit()
            flash('2段階認証が有効になりました。', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('認証コードが正しくありません。', 'danger')
    
    return render_template('totp_setup.html', form=form, qr_code=qr_code_base64, secret=current_user.totp_secret)

@app.route('/totp_disable/', methods=['GET', 'POST'])
@login_required
def totp_disable():
    if not current_user.totp_enabled:
        flash('2段階認証は有効になっていません。', 'info')
        return redirect(url_for('admin.dashboard'))
    
    if request.method == 'POST':
        # 確認のためパスワード入力を要求
        password = request.form.get('password')
        if password and check_password_hash(current_user.password_hash, password):
            current_user.totp_enabled = False
            current_user.totp_secret = None
            db.session.commit()
            flash('2段階認証を無効にしました。', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('パスワードが正しくありません。', 'danger')
    
    return render_template('totp_disable.html')

@app.route('/password_reset_request/', methods=['GET', 'POST'])
def password_reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = user.generate_reset_token()
            db.session.commit()
            send_password_reset_email(user, token)
            flash('パスワードリセット用のメールを送信しました。', 'info')
        else:
            flash('そのメールアドレスは登録されていません。', 'danger')
        return redirect(url_for('login'))
    
    return render_template('password_reset_request.html', form=form)

@app.route('/password_reset/<token>/', methods=['GET', 'POST'])
def password_reset(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    user = User.query.filter_by(reset_token=token).first()
    if not user or not user.verify_reset_token(token):
        flash('無効または期限切れのトークンです。', 'danger')
        return redirect(url_for('password_reset_request'))
    
    form = PasswordResetForm()
    if form.validate_on_submit():
        user.password_hash = generate_password_hash(form.password.data)
        user.clear_reset_token()
        db.session.commit()
        flash('パスワードが変更されました。', 'success')
        return redirect(url_for('login'))
    
    return render_template('password_reset.html', form=form, token=token)

def send_password_reset_email(user, token):
    """パスワードリセットメール送信"""
    try:
        reset_url = url_for('password_reset', token=token, _external=True)
        msg = Message(
            subject='パスワードリセット - MiniBlog',
            sender=app.config['MAIL_DEFAULT_SENDER'],
            recipients=[user.email]
        )
        msg.body = f"""パスワードをリセットするには、以下のリンクをクリックしてください：

{reset_url}

このリンクは1時間で期限切れになります。

もしこのメールに心当たりがない場合は、無視してください。

MiniBlog システム
"""
        mail.send(msg)
        app.logger.info(f"Password reset email sent to {user.email}")
    except Exception as e:
        app.logger.error(f"Failed to send password reset email: {e}")
        # 開発環境ではコンソールにリンクを表示
        if app.debug:
            print(f"パスワードリセットURL (開発環境): {reset_url}")

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

