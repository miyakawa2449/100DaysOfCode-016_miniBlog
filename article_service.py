"""
記事管理サービス - CRUD操作の重複を解消する統一サービス
"""
from flask import current_app, flash
from models import db, Article, Category, User
from datetime import datetime
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
import re
import os


class ArticleService:
    """記事管理の共通処理を集約したサービスクラス"""
    
    @staticmethod
    def setup_category_choices(form):
        """カテゴリ選択肢の設定（全記事フォームで共通）"""
        all_categories = Category.query.order_by(Category.name).all()
        form.category_id.choices = [
            (0, 'カテゴリを選択してください')
        ] + [(cat.id, cat.name) for cat in all_categories]
    
    @staticmethod
    def generate_unique_slug(title, article_id=None):
        """一意なスラッグの生成"""
        slug = re.sub(r'[^\w\s-]', '', title).strip().lower()
        slug = re.sub(r'[-\s]+', '-', slug)
        
        # 重複チェック
        query = Article.query.filter(Article.slug == slug)
        if article_id:
            query = query.filter(Article.id != article_id)
        
        if query.first():
            counter = 1
            original_slug = slug
            while query.filter(Article.slug == f"{original_slug}-{counter}").first():
                counter += 1
            slug = f"{original_slug}-{counter}"
        
        return slug
    
    @staticmethod
    def validate_article_data(form, article_id=None):
        """記事データのバリデーション"""
        errors = []
        
        # タイトル重複チェック
        existing_article = Article.query.filter(Article.title == form.title.data)
        if article_id:
            existing_article = existing_article.filter(Article.id != article_id)
        
        if existing_article.first():
            errors.append('同じタイトルの記事が既に存在します')
        
        # スラッグ重複チェック（自動生成の場合）
        if form.slug.data:
            existing_slug = Article.query.filter(Article.slug == form.slug.data)
            if article_id:
                existing_slug = existing_slug.filter(Article.id != article_id)
            
            if existing_slug.first():
                errors.append('同じスラッグが既に存在します')
        
        return errors
    
    @staticmethod
    def process_article_image(article, cropped_image_data):
        """アイキャッチ画像の処理（作成・編集共通）"""
        if not cropped_image_data:
            return None
        
        try:
            from admin import process_cropped_image
            featured_image = process_cropped_image(cropped_image_data, article.id)
            if featured_image:
                return featured_image
            else:
                current_app.logger.error("Failed to process cropped featured image")
                flash('画像の処理中にエラーが発生しました', 'warning')
                return None
        except Exception as img_error:
            current_app.logger.error(f"Image processing error: {img_error}")
            flash('画像の処理中にエラーが発生しました', 'warning')
            return None
    
    @staticmethod
    def assign_category(article, category_id):
        """カテゴリの割り当て（作成・編集共通）"""
        if not category_id or category_id == 0:
            return
        
        # 既存カテゴリを削除
        if hasattr(article, 'categories'):
            current_category_ids = [cat.id for cat in article.categories.all()]
            for cat_id in current_category_ids:
                category_to_remove = db.session.get(Category, cat_id)
                if category_to_remove:
                    article.categories.remove(category_to_remove)
        
        # 新しいカテゴリを割り当て
        category = db.session.get(Category, category_id)
        if category:
            article.categories.append(category)
    
    @staticmethod
    def create_article(form_data, author_id):
        """新規記事の作成"""
        try:
            # スラッグ生成
            slug = form_data.get('slug') or ArticleService.generate_unique_slug(form_data['title'])
            
            # 記事オブジェクト作成
            article = Article(
                title=form_data['title'],
                slug=slug,
                summary=form_data.get('summary', ''),
                body=form_data.get('body', ''),
                author_id=author_id,
                is_published=form_data.get('is_published', False),
                allow_comments=form_data.get('allow_comments', True),
                meta_title=form_data.get('meta_title', ''),
                meta_description=form_data.get('meta_description', ''),
                meta_keywords=form_data.get('meta_keywords', ''),
                canonical_url=form_data.get('canonical_url', '')
            )
            
            # 公開設定
            if article.is_published:
                article.published_at = datetime.utcnow()
            
            db.session.add(article)
            db.session.flush()  # IDを取得
            
            # カテゴリ割り当て
            ArticleService.assign_category(article, form_data.get('category_id'))
            
            # アイキャッチ画像処理
            if form_data.get('cropped_image_data'):
                featured_image = ArticleService.process_article_image(
                    article, form_data['cropped_image_data']
                )
                if featured_image:
                    article.featured_image = featured_image
            
            db.session.commit()
            return article, None
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Article creation error: {e}")
            return None, str(e)
    
    @staticmethod
    def update_article(article, form_data):
        """既存記事の更新"""
        try:
            # 基本情報更新
            article.title = form_data['title']
            article.summary = form_data.get('summary', '')
            article.body = form_data.get('body', '')
            article.allow_comments = form_data.get('allow_comments', True)
            article.meta_title = form_data.get('meta_title', '')
            article.meta_description = form_data.get('meta_description', '')
            article.meta_keywords = form_data.get('meta_keywords', '')
            article.canonical_url = form_data.get('canonical_url', '')
            
            # スラッグ更新
            if form_data.get('slug') and form_data['slug'] != article.slug:
                article.slug = form_data['slug']
            
            # 公開設定更新
            old_published_status = article.is_published
            article.is_published = form_data.get('is_published', False)
            
            if article.is_published and not old_published_status:
                article.published_at = datetime.utcnow()
            
            # カテゴリ更新
            ArticleService.assign_category(article, form_data.get('category_id'))
            
            # アイキャッチ画像処理
            if form_data.get('cropped_image_data'):
                featured_image = ArticleService.process_article_image(
                    article, form_data['cropped_image_data']
                )
                if featured_image:
                    article.featured_image = featured_image
            
            db.session.commit()
            return article, None
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Article update error: {e}")
            return None, str(e)
    
    @staticmethod
    def get_article_context(article=None):
        """記事フォーム用のコンテキスト取得"""
        return {
            'article': article,
            'is_edit': article is not None,
            'form_title': '記事編集' if article else '記事作成',
            'submit_text': '更新' if article else '作成',
            'form_action': f'/admin/article/edit/{article.id}' if article else '/admin/article/create'
        }


class CategoryService:
    """カテゴリ管理の共通処理を集約したサービスクラス"""
    
    @staticmethod
    def generate_unique_slug(name, category_id=None):
        """一意なスラッグの生成"""
        if not name:
            return None
        
        slug = re.sub(r'[^\w\s-]', '', name).strip().lower()
        slug = re.sub(r'[-\s]+', '-', slug)
        
        # 重複チェック
        query = Category.query.filter(Category.slug == slug)
        if category_id:
            query = query.filter(Category.id != category_id)
        
        if query.first():
            counter = 1
            original_slug = slug
            while query.filter(Category.slug == f"{original_slug}-{counter}").first():
                counter += 1
            slug = f"{original_slug}-{counter}"
        
        return slug
    
    @staticmethod
    def validate_category_data(form_data, category_id=None):
        """カテゴリデータのバリデーション"""
        errors = []
        
        # 名前重複チェック
        existing_category = Category.query.filter(Category.name == form_data['name'])
        if category_id:
            existing_category = existing_category.filter(Category.id != category_id)
        
        if existing_category.first():
            errors.append('同じ名前のカテゴリが既に存在します')
        
        # スラッグ重複チェック
        if form_data.get('slug'):
            existing_slug = Category.query.filter(Category.slug == form_data['slug'])
            if category_id:
                existing_slug = existing_slug.filter(Category.id != category_id)
            
            if existing_slug.first():
                errors.append('同じスラッグが既に存在します')
        
        return errors
    
    @staticmethod
    def process_category_image(category, ogp_image_data, crop_data=None):
        """カテゴリOGP画像の処理（作成・編集共通）"""
        if not ogp_image_data:
            return None
        
        try:
            # 動的インポートによる循環参照回避
            import sys
            sys.path.append(os.path.join(os.path.dirname(__file__), 'app', 'utils'))
            from helpers import process_ogp_image, delete_old_image
            
            # 古い画像削除（編集時）
            if hasattr(category, 'ogp_image') and category.ogp_image:
                old_image_path = os.path.join(current_app.static_folder, category.ogp_image)
                delete_old_image(old_image_path)
            
            # 新しい画像処理
            ogp_image_path = process_ogp_image(ogp_image_data, category.id, crop_data)
            if ogp_image_path:
                current_app.logger.info(f"OGP image processed: {ogp_image_path}")
                return ogp_image_path
            else:
                current_app.logger.error("Failed to process OGP image")
                flash('画像の処理中にエラーが発生しました', 'warning')
                return None
                
        except Exception as e:
            current_app.logger.error(f"OGP image processing error: {e}")
            flash('画像の処理中にエラーが発生しました', 'warning')
            return None
    
    @staticmethod
    def extract_crop_data(form):
        """フォームからクロップデータを抽出"""
        if not all([
            hasattr(form, 'ogp_crop_x') and form.ogp_crop_x.data,
            hasattr(form, 'ogp_crop_y') and form.ogp_crop_y.data,
            hasattr(form, 'ogp_crop_width') and form.ogp_crop_width.data,
            hasattr(form, 'ogp_crop_height') and form.ogp_crop_height.data
        ]):
            return None
        
        return {
            'x': form.ogp_crop_x.data,
            'y': form.ogp_crop_y.data,
            'width': form.ogp_crop_width.data,
            'height': form.ogp_crop_height.data
        }
    
    @staticmethod
    def create_category(form_data):
        """新規カテゴリの作成"""
        try:
            # スラッグ生成
            slug = form_data.get('slug') or CategoryService.generate_unique_slug(form_data['name'])
            if not slug:
                return None, '有効なスラッグを生成できませんでした'
            
            # バリデーション
            validation_errors = CategoryService.validate_category_data(form_data)
            if validation_errors:
                return None, validation_errors[0]
            
            # カテゴリオブジェクト作成
            category = Category(
                name=form_data['name'],
                slug=slug,
                description=form_data.get('description', ''),
                created_at=datetime.utcnow()
            )
            
            db.session.add(category)
            db.session.flush()  # IDを取得
            
            # OGP画像処理
            if form_data.get('ogp_image'):
                crop_data = form_data.get('crop_data')
                ogp_image_path = CategoryService.process_category_image(
                    category, form_data['ogp_image'], crop_data
                )
                if ogp_image_path:
                    category.ogp_image = ogp_image_path
            
            db.session.commit()
            return category, None
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Category creation error: {e}")
            return None, str(e)
    
    @staticmethod
    def update_category(category, form_data):
        """既存カテゴリの更新"""
        try:
            # 基本情報更新
            category.name = form_data['name']
            category.slug = form_data.get('slug', category.slug)
            category.description = form_data.get('description', '')
            
            # OGP画像処理
            if form_data.get('ogp_image'):
                crop_data = form_data.get('crop_data')
                ogp_image_path = CategoryService.process_category_image(
                    category, form_data['ogp_image'], crop_data
                )
                if ogp_image_path:
                    category.ogp_image = ogp_image_path
            
            db.session.commit()
            return category, None
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Category update error: {e}")
            return None, str(e)
    
    @staticmethod
    def get_category_context(category=None):
        """カテゴリフォーム用のコンテキスト取得"""
        return {
            'category': category,
            'is_edit': category is not None,
            'form_title': 'カテゴリ編集' if category else 'カテゴリ作成',
            'submit_text': '更新' if category else '作成',
            'form_action': f'/admin/category/edit/{category.id}' if category else '/admin/category/create'
        }


class ImageProcessingService:
    """画像処理の共通機能"""
    
    @staticmethod
    def validate_image_file(file):
        """画像ファイルのバリデーション"""
        if not file or file.filename == '':
            return False, '画像ファイルが選択されていません'
        
        # 拡張子チェック
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
        if not ('.' in file.filename and 
                file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
            return False, '許可されていないファイル形式です'
        
        return True, None
    
    @staticmethod
    def secure_filename_with_timestamp(filename):
        """タイムスタンプ付きの安全なファイル名生成"""
        if not filename:
            return None
        
        name, ext = os.path.splitext(secure_filename(filename))
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{name}_{timestamp}{ext}"


class UserService:
    """ユーザ管理の共通処理を集約したサービスクラス"""
    
    @staticmethod
    def validate_password(password):
        """パスワードのバリデーション"""
        if not password:
            return False, 'パスワードが入力されていません'
        
        if len(password) < 8:
            return False, 'パスワードは8文字以上である必要があります'
        
        return True, None
    
    @staticmethod
    def validate_user_data(form_data, user_id=None):
        """ユーザデータのバリデーション"""
        errors = []
        
        # メールアドレス重複チェック
        existing_user = User.query.filter(User.email == form_data['email'])
        if user_id:
            existing_user = existing_user.filter(User.id != user_id)
        
        if existing_user.first():
            errors.append('同じメールアドレスのユーザが既に存在します')
        
        # パスワードバリデーション（新規作成時のみ必須）
        if not user_id and 'password' in form_data:
            is_valid, password_error = UserService.validate_password(form_data['password'])
            if not is_valid:
                errors.append(password_error)
        
        return errors
    
    @staticmethod
    def process_user_form_data(form_data):
        """フォームデータの処理と正規化"""
        processed_data = {
            'name': form_data.get('name', '').strip(),
            'email': form_data.get('email', '').strip().lower(),
            'handle_name': form_data.get('handle_name', '').strip(),
            'role': form_data.get('role', 'author'),
            'introduction': form_data.get('introduction', '').strip(),
            'birthplace': form_data.get('birthplace', '').strip(),
            'birthday': form_data.get('birthday'),
            'sns_x': form_data.get('sns_x', '').strip(),
            'sns_facebook': form_data.get('sns_facebook', '').strip(),
            'sns_instagram': form_data.get('sns_instagram', '').strip(),
            'sns_threads': form_data.get('sns_threads', '').strip(),
            'sns_youtube': form_data.get('sns_youtube', '').strip(),
            'notify_on_publish': form_data.get('notify_on_publish', False),
            'notify_on_comment': form_data.get('notify_on_comment', False),
        }
        
        # パスワード処理
        if 'password' in form_data and form_data['password']:
            processed_data['password_hash'] = generate_password_hash(form_data['password'])
        
        # 誕生日の処理
        if processed_data['birthday']:
            try:
                from datetime import datetime
                if isinstance(processed_data['birthday'], str):
                    processed_data['birthday'] = datetime.strptime(
                        processed_data['birthday'], '%Y-%m-%d'
                    ).date()
            except ValueError:
                processed_data['birthday'] = None
        
        return processed_data
    
    @staticmethod
    def create_user(form_data):
        """新規ユーザの作成"""
        try:
            # バリデーション
            validation_errors = UserService.validate_user_data(form_data)
            if validation_errors:
                return None, validation_errors[0]
            
            # データ処理
            user_data = UserService.process_user_form_data(form_data)
            
            # パスワード必須チェック
            if 'password_hash' not in user_data:
                return None, 'パスワードが必要です'
            
            # ユーザオブジェクト作成
            user = User(
                name=user_data['name'],
                email=user_data['email'],
                handle_name=user_data['handle_name'],
                password_hash=user_data['password_hash'],
                role=user_data['role'],
                introduction=user_data['introduction'],
                birthplace=user_data['birthplace'],
                birthday=user_data['birthday'],
                sns_x=user_data['sns_x'],
                sns_facebook=user_data['sns_facebook'],
                sns_instagram=user_data['sns_instagram'],
                sns_threads=user_data['sns_threads'],
                sns_youtube=user_data['sns_youtube'],
                notify_on_publish=user_data['notify_on_publish'],
                notify_on_comment=user_data['notify_on_comment'],
                created_at=datetime.utcnow()
            )
            
            db.session.add(user)
            db.session.commit()
            return user, None
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"User creation error: {e}")
            return None, str(e)
    
    @staticmethod
    def update_user(user, form_data):
        """既存ユーザの更新"""
        try:
            # バリデーション
            validation_errors = UserService.validate_user_data(form_data, user.id)
            if validation_errors:
                return None, validation_errors[0]
            
            # データ処理
            user_data = UserService.process_user_form_data(form_data)
            
            # 基本情報更新
            user.name = user_data['name']
            user.email = user_data['email']
            user.handle_name = user_data['handle_name']
            user.role = user_data['role']
            user.introduction = user_data['introduction']
            user.birthplace = user_data['birthplace']
            user.birthday = user_data['birthday']
            user.sns_x = user_data['sns_x']
            user.sns_facebook = user_data['sns_facebook']
            user.sns_instagram = user_data['sns_instagram']
            user.sns_threads = user_data['sns_threads']
            user.sns_youtube = user_data['sns_youtube']
            user.notify_on_publish = user_data['notify_on_publish']
            user.notify_on_comment = user_data['notify_on_comment']
            
            # パスワード更新（指定された場合のみ）
            if 'password_hash' in user_data:
                user.password_hash = user_data['password_hash']
            
            db.session.commit()
            return user, None
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"User update error: {e}")
            return None, str(e)
    
    @staticmethod
    def get_user_context(user=None):
        """ユーザフォーム用のコンテキスト取得"""
        return {
            'user': user,
            'is_edit': user is not None,
            'form_title': 'ユーザ編集' if user else 'ユーザ作成',
            'submit_text': '更新' if user else '作成',
            'form_action': f'/admin/user/edit/{user.id}' if user else '/admin/user/create',
            'password_required': user is None  # 新規作成時のみパスワード必須
        }