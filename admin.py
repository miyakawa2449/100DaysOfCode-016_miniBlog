from flask import Blueprint, render_template, redirect, url_for, request, flash, session, current_app
from models import db, User, Article, Category, Comment  # CategoryとCommentをインポート
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os
from PIL import Image
import time
from forms import CategoryForm # CategoryFormをインポート

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# 管理者認証デコレータ
def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        user = User.query.get(user_id) if user_id else None
        if not user or user.role != 'admin':
            flash('管理者権限が必要です')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

# ダッシュボード
@admin_bp.route('/')
@admin_required
def dashboard():
    user_count = User.query.count()
    article_count = Article.query.count()
    category_count = Category.query.count() # カテゴリ数を取得
    comment_count = Comment.query.count()   # コメント数を取得
    
    # 最近の投稿5件を取得
    recent_articles = Article.query.order_by(Article.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html', 
                        user_count=user_count, 
                        article_count=article_count,
                        category_count=category_count,
                        comment_count=comment_count,
                        recent_articles=recent_articles)

# ユーザ管理
@admin_bp.route('/users/')
@admin_required
def users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

# ユーザ編集
@admin_bp.route('/user/edit/<int:user_id>/', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        user.name = request.form['name']
        user.handle_name = request.form['handle_name']
        user.role = request.form['role']
        db.session.commit()
        flash('ユーザ情報を更新しました')
        return redirect(url_for('admin.users'))
    return render_template('admin/edit_user.html', user=user)

# 記事管理
@admin_bp.route('/articles/')
@admin_required
def articles():
    page = request.args.get('page', 1, type=int)
    # 記事を作成日時の降順で取得し、ページネーションを適用
    articles_pagination = Article.query.order_by(Article.created_at.desc()).paginate(page=page, per_page=10) # 1ページあたり10件表示
    # テンプレートには paginate オブジェクトを渡す (テンプレート側で .items でリストにアクセス)
    return render_template('admin/articles.html', articles_list=articles_pagination)

# 記事作成
@admin_bp.route('/article/create/', methods=['GET', 'POST'])
@admin_required
def create_article():
    if request.method == 'POST':
        title = request.form.get('title')
        slug = request.form.get('slug')
        body = request.form.get('body')
        author_id = session.get('user_id')
        category_ids = request.form.getlist('categories') # 選択されたカテゴリIDのリストを取得

        if not title or not slug:
            flash('タイトルとスラッグは必須です。', 'danger')
        else:
            # スラッグの重複チェック
            existing_article = Article.query.filter_by(slug=slug).first()
            if existing_article:
                flash('そのスラッグは既に使用されています。', 'danger')
            else:
                new_article = Article(title=title, slug=slug, body=body, author_id=author_id)
                
                # 選択されたカテゴリを記事に関連付ける
                if category_ids:
                    for cat_id in category_ids:
                        category = Category.query.get(cat_id)
                        if category:
                            new_article.categories.append(category) # リレーションシップに追加
                
                db.session.add(new_article)
                db.session.commit()
                flash('記事が作成されました。', 'success')
                return redirect(url_for('admin.articles'))
    
    all_categories = Category.query.order_by(Category.name).all() # カテゴリ一覧をテンプレートに渡す
    return render_template('admin/create_article.html', all_categories=all_categories)

# 記事編集
@admin_bp.route('/article/edit/<int:article_id>/', methods=['GET', 'POST'])
@admin_required
def edit_article(article_id):
    article = Article.query.get_or_404(article_id)
    if request.method == 'POST':
        title = request.form.get('title')
        slug = request.form.get('slug')
        body = request.form.get('body')
        category_ids = request.form.getlist('categories')

        if not title or not slug:
            flash('タイトルとスラッグは必須です。', 'danger')
        else:
            # スラッグの重複チェック (自分自身を除く)
            existing_article = Article.query.filter(Article.id != article_id, Article.slug == slug).first()
            if existing_article:
                flash('そのスラッグは既に使用されています。', 'danger')
            else:
                article.title = title
                article.slug = slug
                article.body = body
                
                # カテゴリの関連付けを更新
                article.categories = [] # 一旦クリア
                if category_ids:
                    for cat_id in category_ids:
                        category = Category.query.get(cat_id)
                        if category:
                            article.categories.append(category)
                            
                db.session.commit()
                flash('記事が更新されました。', 'success')
                return redirect(url_for('admin.articles'))

    all_categories = Category.query.order_by(Category.name).all()
    # 記事が既に持っているカテゴリIDのリストを作成 (テンプレートでの選択状態復元用)
    article_category_ids = [cat.id for cat in article.categories]
    return render_template('admin/edit_article.html', article=article, all_categories=all_categories, article_category_ids=article_category_ids)

# カテゴリ管理
@admin_bp.route('/categories/')
@admin_required
def categories():
    page = request.args.get('page', 1, type=int)
    categories_list = Category.query.order_by(Category.name).paginate(page=page, per_page=10)
    return render_template('admin/categories.html', categories_list=categories_list)

@admin_bp.route('/category/create/', methods=['GET', 'POST'])
@admin_required
def create_category():
    if request.method == 'POST':
        name = request.form.get('name')
        slug = request.form.get('slug')
        description = request.form.get('description')
        parent_id = request.form.get('parent_id')
        # --- 追加フィールドの取得 ---
        ogp_image = request.form.get('ogp_image')
        meta_keywords = request.form.get('meta_keywords')
        canonical_url = request.form.get('canonical_url')
        json_ld = request.form.get('json_ld')
        ext_json = request.form.get('ext_json')
        # --- ここまで ---
        
        if not name or not slug:
            flash('カテゴリ名とスラッグは必須です。', 'danger')
        else:
            existing_category_slug = Category.query.filter_by(slug=slug).first()
            existing_category_name = Category.query.filter_by(name=name).first()
            if existing_category_slug:
                flash('そのスラッグは既に使用されています。', 'danger')
            elif existing_category_name:
                flash('そのカテゴリ名は既に使用されています。', 'danger')
            else:
                new_category = Category(
                    name=name, 
                    slug=slug, 
                    description=description,
                    parent_id=int(parent_id) if parent_id else None,
                    # --- 追加フィールドの保存 ---
                    ogp_image=ogp_image,
                    meta_keywords=meta_keywords,
                    canonical_url=canonical_url,
                    json_ld=json_ld,
                    ext_json=ext_json
                    # --- ここまで ---
                )
                db.session.add(new_category)
                db.session.commit()
                flash('カテゴリが作成されました。', 'success')
                return redirect(url_for('admin.categories'))
                
    parent_categories = Category.query.order_by(Category.name).all()
    return render_template('admin/create_category.html', parent_categories=parent_categories)

@admin_bp.route('/category/edit/<int:category_id>/', methods=['GET', 'POST'])
@admin_required
def edit_category(category_id):
    category = Category.query.get_or_404(category_id)
    form = CategoryForm(obj=category)
    print(f"--- Request method: {request.method} ---")
    print(f"--- Initial category.ogp_image: {category.ogp_image} ---")

    if request.method == 'POST': # validate_on_submit の前にPOSTかどうか確認
        print("--- POST request received ---")
        print(f"--- form.ogp_image_file.data: {form.ogp_image_file.data} ---")
        print(f"--- form.ogp_crop_x.data: {form.ogp_crop_x.data} ---")
        # 他のトリミングデータも同様にprint

        if form.validate_on_submit():
            print("--- Form IS valid ---")
            ogp_image_file = form.ogp_image_file.data
            old_ogp_image_path = category.ogp_image # 更新前のOGP画像パスを保持

            if ogp_image_file:
                current_app.logger.debug(f"New OGP image file provided: {ogp_image_file.filename}")
                try:
                    timestamp = int(time.time())
                    filename_base, file_ext = os.path.splitext(secure_filename(ogp_image_file.filename))
                    new_ogp_filename = f"category_ogp_{category.id}_{timestamp}{file_ext}"
                    current_app.logger.debug(f"Generated new OGP filename: {new_ogp_filename}")
                    
                    upload_folder = current_app.config['CATEGORY_OGP_UPLOAD_FOLDER'] # ★★★ 修正後 ★★★
                    current_app.logger.debug(f"Upload folder from config: {upload_folder}")


                    if not os.path.exists(upload_folder):
                        os.makedirs(upload_folder)
                        current_app.logger.info(f"Created upload folder: {upload_folder}")
                    ogp_image_save_path = os.path.join(upload_folder, new_ogp_filename)
                    current_app.logger.debug(f"OGP image save path: {ogp_image_save_path}")

                    temp_image_path = os.path.join(upload_folder, f"temp_{new_ogp_filename}")
                    ogp_image_file.save(temp_image_path)

                    img = Image.open(temp_image_path)

                    try:
                        crop_x_str = form.ogp_crop_x.data
                        crop_y_str = form.ogp_crop_y.data
                        crop_width_str = form.ogp_crop_width.data
                        crop_height_str = form.ogp_crop_height.data
                        current_app.logger.debug(f"Crop data strings from form: x='{crop_x_str}', y='{crop_y_str}', width='{crop_width_str}', height='{crop_height_str}'")

                        # 文字列から整数への変換を試みる
                        crop_x = int(crop_x_str) if crop_x_str else None
                        crop_y = int(crop_y_str) if crop_y_str else None
                        crop_width = int(crop_width_str) if crop_width_str else None
                        crop_height = int(crop_height_str) if crop_height_str else None

                    except (ValueError, TypeError) as e:
                        current_app.logger.warning(f"Could not convert crop data to int: {e}. Setting to None.")
                        crop_x, crop_y, crop_width, crop_height = None, None, None, None

                    current_app.logger.debug(f"Converted crop data: x={type(crop_x).__name__}:{crop_x}, y={type(crop_y).__name__}:{crop_y}, width={type(crop_width).__name__}:{crop_width}, height={type(crop_height).__name__}:{crop_height}")

                    if crop_x is not None and crop_y is not None and \
                        crop_width is not None and crop_height is not None and \
                        crop_width > 0 and crop_height > 0:
                        current_app.logger.debug("Applying crop to image.")
                        # Pillow の crop メソッドは (left, upper, right, lower) のタプルを期待する
                        cropped_img = img.crop((crop_x, crop_y, crop_x + crop_width, crop_y + crop_height))
                        
                        # --- ★★★ クロップした画像をリサイズ ★★★ ---
                        target_width = 1200
                        target_height = 630
                        current_app.logger.debug(f"Resizing cropped image to {target_width}x{target_height}")
                        resized_img = cropped_img.resize((target_width, target_height), Image.Resampling.LANCZOS) # 高画質なリサイズ方法
                        # --- ★★★ ここまで追加 ★★★ ---

                        resized_img.save(ogp_image_save_path) # リサイズされた画像を保存
                        category.ogp_image = os.path.join('uploads/category_ogp', new_ogp_filename).replace("\\", "/")
                    else:
                        current_app.logger.warning(f"Crop conditions not met or data invalid after conversion. Saving original image. Crop data: x={crop_x}, y={crop_y}, w={crop_width}, h={crop_height}")
                        # トリミング条件を満たさない場合、オリジナル画像をリサイズするかどうかを検討
                        # もしオリジナル画像も特定のサイズにしたい場合は、ここでもリサイズ処理を入れる
                        # 例: target_width = 1200
                        #     target_height = 630
                        #     resized_original_img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
                        #     resized_original_img.save(ogp_image_save_path)
                        # 現状はオリジナルをそのまま保存
                        img.save(ogp_image_save_path)
                        category.ogp_image = os.path.join('uploads/category_ogp', new_ogp_filename).replace("\\", "/")

                    if os.path.exists(temp_image_path):
                        os.remove(temp_image_path)

                    if old_ogp_image_path and old_ogp_image_path != category.ogp_image:
                        try:
                            full_old_path = os.path.join(current_app.static_folder, old_ogp_image_path)
                            if os.path.exists(full_old_path):
                                os.remove(full_old_path)
                                flash(f'古いOGP画像 {old_ogp_image_path} を削除しました。', 'info')
                        except Exception as e:
                            current_app.logger.error(f"古いOGP画像の削除に失敗: {e}")
                            flash(f'古いOGP画像の削除に失敗しました: {old_ogp_image_path}', 'warning')
                
                except Exception as e:
                    current_app.logger.error(f"OGP画像のアップロードまたは処理に失敗: {e}")
                    flash('OGP画像のアップロードまたは処理中にエラーが発生しました。', 'danger')
            
            category.name = form.name.data
            category.slug = form.slug.data
            category.meta_title = form.meta_title.data
            category.meta_description = form.meta_description.data
            category.meta_keywords = form.meta_keywords.data
            category.canonical_url = form.canonical_url.data
            category.json_ld = form.json_ld.data
            category.ext_json = form.ext_json.data
            
            try:
                db.session.commit()
                flash('カテゴリが正常に更新されました。', 'success')
                return redirect(url_for('admin.categories'))
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"カテゴリ更新時のデータベースコミット失敗: {e}")
                flash('カテゴリの更新中にエラーが発生しました。', 'danger')
        else:
            print("--- Form IS NOT valid ---")
            print(f"--- Form errors: {form.errors} ---") # ★重要: バリデーションエラー内容を確認

    elif request.method == 'GET':
        form.name.data = category.name
        form.slug.data = category.slug
        form.meta_title.data = form.meta_title.data
        form.meta_description.data = form.meta_description.data
        form.meta_keywords.data = form.meta_keywords.data
        form.canonical_url.data = form.canonical_url.data
        form.json_ld.data = form.json_ld.data
        form.ext_json.data = form.ext_json.data

    print(f"--- Rendering template with category.ogp_image: {category.ogp_image} ---")
    return render_template('admin/edit_category.html', form=form, category=category)

@admin_bp.route('/category/delete/<int:category_id>/', methods=['POST']) # 安全のためPOST推奨
@admin_required
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)
    # TODO: 子カテゴリが存在する場合の処理、記事が紐づいている場合の処理を検討
    db.session.delete(category)
    db.session.commit()
    flash('カテゴリが削除されました。', 'success')
    return redirect(url_for('admin.categories'))

# コメント管理
@admin_bp.route('/comments/')
@admin_required
def comments():
    flash("コメント管理ページ - 未実装")
    return "コメント管理ページ - 未実装" # 一時的に文字列を返す

# サイト管理
@admin_bp.route('/site_settings/')
@admin_required
def site_settings():
    flash("サイト管理ページ - 未実装")
    return "サイト管理ページ - 未実装" # 一時的に文字列を返す

# Blueprint登録（app.pyの末尾で）
# app.register_blueprint(admin_bp)