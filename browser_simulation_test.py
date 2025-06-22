#!/usr/bin/env python3
"""
ブラウザシミュレーションテスト
記事ID 19のブロック型・従来型エディタの実際のブラウザアクセスをシミュレート
"""

import requests
from bs4 import BeautifulSoup
import re
import json
from urllib.parse import urljoin

class BrowserSimulator:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def get_csrf_token(self, response_text):
        """レスポンスからCSRFトークンを抽出"""
        soup = BeautifulSoup(response_text, 'html.parser')
        csrf_input = soup.find('input', {'name': 'csrf_token'})
        if csrf_input:
            return csrf_input.get('value')
        return None
        
    def login(self, email="admin@example.com", password="admin123"):
        """管理者ログイン"""
        print("🔐 管理者ログイン試行...")
        
        # Step 1: ログインページを取得
        login_url = f"{self.base_url}/login/"
        response = self.session.get(login_url)
        print(f"   ログインページ取得: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ ログインページにアクセスできません")
            return False
            
        # Step 2: CSRFトークンを取得
        csrf_token = self.get_csrf_token(response.text)
        if not csrf_token:
            print(f"❌ CSRFトークンが見つかりません")
            return False
            
        print(f"   CSRFトークン取得: {csrf_token[:20]}...")
        
        # Step 3: ログイン実行
        login_data = {
            'email': email,
            'password': password,
            'csrf_token': csrf_token
        }
        
        response = self.session.post(login_url, data=login_data, allow_redirects=True)
        print(f"   ログイン送信: {response.status_code}")
        print(f"   最終URL: {response.url}")
        
        # Step 4: ログイン成功判定
        soup = BeautifulSoup(response.text, 'html.parser')
        alerts = soup.find_all(class_=re.compile(r'alert'))
        
        # 成功メッセージをチェック
        success_message = False
        error_message = False
        
        for alert in alerts:
            alert_text = alert.get_text().strip()
            print(f"   アラート: {alert_text}")
            if 'ログインしました' in alert_text:
                success_message = True
            elif 'パスワードが正しくありません' in alert_text or 'メールアドレスまたはパスワードが正しくありません' in alert_text:
                error_message = True
        
        # URLやページタイトルでも判定
        page_title = soup.find('title')
        page_title_text = page_title.text.strip() if page_title else ''
        
        if success_message or ('ログイン' not in page_title_text and response.url != f"{self.base_url}/login/"):
            print("✅ ログイン成功")
            return True
        elif error_message:
            print("❌ ログイン失敗 - 認証エラー")
            return False
        else:
            print("❌ ログイン状態不明")
            print(f"   最終URL: {response.url}")
            print(f"   ページタイトル: {page_title_text}")
            return False
    
    def access_block_editor(self, article_id=19):
        """ブロック型エディタにアクセス"""
        url = f"{self.base_url}/admin/article/block-editor/edit/{article_id}/"
        print(f"\n🧱 ブロック型エディタアクセス: {url}")
        
        response = self.session.get(url)
        print(f"   ステータス: {response.status_code}")
        print(f"   最終URL: {response.url}")
        
        if response.status_code == 200:
            return self.parse_editor_page(response.text, "block")
        else:
            print(f"❌ アクセス失敗")
            return None
    
    def access_traditional_editor(self, article_id=19):
        """従来型エディタにアクセス"""
        url = f"{self.base_url}/admin/article/edit/{article_id}/"
        print(f"\n📝 従来型エディタアクセス: {url}")
        
        response = self.session.get(url)
        print(f"   ステータス: {response.status_code}")
        print(f"   最終URL: {response.url}")
        
        if response.status_code == 200:
            return self.parse_editor_page(response.text, "traditional")
        else:
            print(f"❌ アクセス失敗")
            return None
    
    def parse_editor_page(self, html_content, editor_type):
        """エディタページを解析"""
        soup = BeautifulSoup(html_content, 'html.parser')
        result = {'editor_type': editor_type}
        
        # ページタイトル
        title_tag = soup.find('title')
        if title_tag:
            result['page_title'] = title_tag.text.strip()
            print(f"   ページタイトル: {result['page_title']}")
        
        # ログインページかどうかチェック
        if 'ログイン' in result.get('page_title', ''):
            print("❌ ログインページにリダイレクトされました")
            result['error'] = 'redirect_to_login'
            return result
        
        # フォーム要素をチェック
        form = soup.find('form')
        if not form:
            print("❌ フォーム要素が見つかりません")
            result['error'] = 'no_form'
            return result
        
        print("✅ フォーム要素が見つかりました")
        
        # 記事タイトル
        title_input = soup.find('input', {'name': 'title'}) or soup.find('input', {'id': 'title'})
        if title_input:
            result['title'] = title_input.get('value', '')
            print(f"   📰 記事タイトル: {result['title']}")
        
        # 記事概要
        summary_input = soup.find('textarea', {'name': 'summary'}) or soup.find('textarea', {'id': 'summary'})
        if summary_input:
            result['summary'] = summary_input.text.strip()
            print(f"   📝 記事概要: {result['summary']}")
        
        # スラッグ
        slug_input = soup.find('input', {'name': 'slug'}) or soup.find('input', {'id': 'slug'})
        if slug_input:
            result['slug'] = slug_input.get('value', '')
            print(f"   🔗 スラッグ: {result['slug']}")
        
        # 公開状態
        is_published_input = soup.find('input', {'name': 'is_published', 'type': 'checkbox'})
        if is_published_input:
            result['is_published'] = 'checked' in is_published_input.attrs
            print(f"   ✅ 公開状態: {'公開' if result['is_published'] else '下書き'}")
        
        # コメント許可
        allow_comments_input = soup.find('input', {'name': 'allow_comments', 'type': 'checkbox'})
        if allow_comments_input:
            result['allow_comments'] = 'checked' in allow_comments_input.attrs
            print(f"   💬 コメント許可: {'許可' if result['allow_comments'] else '許可しない'}")
        
        # カテゴリ
        category_select = soup.find('select', {'name': 'category_id'}) or soup.find('select', {'id': 'category_id'})
        if category_select:
            selected_option = category_select.find('option', selected=True)
            if selected_option:
                result['category'] = selected_option.text.strip()
                print(f"   📂 カテゴリ: {result['category']}")
        
        # SEO・メタ情報
        meta_title_input = soup.find('input', {'name': 'meta_title'}) or soup.find('input', {'id': 'meta_title'})
        if meta_title_input:
            result['meta_title'] = meta_title_input.get('value', '')
            
        meta_description_input = soup.find('textarea', {'name': 'meta_description'}) or soup.find('textarea', {'id': 'meta_description'})
        if meta_description_input:
            result['meta_description'] = meta_description_input.text.strip()
        
        # 従来型エディタの本文
        if editor_type == 'traditional':
            body_input = soup.find('textarea', {'name': 'body'}) or soup.find('textarea', {'id': 'body'})
            if body_input:
                result['body'] = body_input.text.strip()
                if result['body']:
                    body_preview = result['body'][:100] + "..." if len(result['body']) > 100 else result['body']
                    print(f"   📄 本文: {body_preview}")
                else:
                    print(f"   📄 本文: (空白)")
        
        # ブロック型エディタのブロック情報
        if editor_type == 'block':
            blocks = soup.find_all(class_=re.compile(r'block-item'))
            result['block_count'] = len(blocks)
            print(f"   🧱 ブロック数: {result['block_count']}")
            
            result['blocks'] = []
            for i, block in enumerate(blocks, 1):
                block_info = {'index': i}
                # ブロックタイプ
                block_type_elem = block.find(class_=re.compile(r'block-type'))
                if block_type_elem:
                    block_info['type'] = block_type_elem.text.strip()
                
                # ブロックタイトル
                block_title_elem = block.find('input', {'name': re.compile(r'.*title.*')})
                if block_title_elem:
                    block_info['title'] = block_title_elem.get('value', '')
                
                result['blocks'].append(block_info)
                print(f"     {i}. {block_info.get('type', 'Unknown')} - {block_info.get('title', '')}")
        
        # エディタ切り替えリンク
        if editor_type == 'block':
            traditional_link = soup.find('a', href=re.compile(r'/admin/article/edit/\d+/'))
            if traditional_link:
                result['switch_link'] = traditional_link.get('href')
                print(f"   🔄 従来型エディタリンク: {result['switch_link']}")
            else:
                print("   ❌ 従来型エディタリンクが見つかりません")
        else:
            block_link = soup.find('a', href=re.compile(r'/admin/article/block-editor/edit/\d+/'))
            if block_link:
                result['switch_link'] = block_link.get('href')
                print(f"   🔄 ブロック型エディタリンク: {result['switch_link']}")
            else:
                print("   ❌ ブロック型エディタリンクが見つかりません")
        
        # JavaScript要素のチェック
        scripts = soup.find_all('script')
        result['script_count'] = len(scripts)
        print(f"   📜 JavaScript要素数: {result['script_count']}")
        
        # エラー表示のチェック
        error_elements = soup.find_all(class_=re.compile(r'alert-danger|error'))
        if error_elements:
            result['errors'] = []
            for error in error_elements:
                error_text = error.get_text().strip()
                result['errors'].append(error_text)
                print(f"   ⚠️ エラー: {error_text}")
        
        return result
    
    def compare_editors(self, block_result, traditional_result):
        """両エディタの比較"""
        print("\n" + "=" * 60)
        print("🔍 ブロック型エディタ vs 従来型エディタ 比較結果")
        print("=" * 60)
        
        if not block_result or not traditional_result:
            print("❌ 比較に必要なデータが不足しています")
            return
        
        if block_result.get('error') or traditional_result.get('error'):
            print("❌ どちらかのエディタでエラーが発生しています")
            if block_result.get('error'):
                print(f"   ブロック型エディタエラー: {block_result['error']}")
            if traditional_result.get('error'):
                print(f"   従来型エディタエラー: {traditional_result['error']}")
            return
        
        # 比較項目
        comparison_fields = [
            ('title', '記事タイトル'),
            ('summary', '記事概要'),
            ('slug', 'スラッグ'),
            ('is_published', '公開状態'),
            ('allow_comments', 'コメント許可'),
            ('category', 'カテゴリ'),
            ('meta_title', 'メタタイトル'),
            ('meta_description', 'メタ説明'),
        ]
        
        inconsistencies = []
        
        for field, field_name in comparison_fields:
            block_value = block_result.get(field)
            traditional_value = traditional_result.get(field)
            
            if block_value == traditional_value:
                print(f"✅ {field_name}: 一致")
            else:
                print(f"❌ {field_name}: 不一致")
                print(f"   ブロック型: {block_value}")
                print(f"   従来型: {traditional_value}")
                inconsistencies.append((field_name, block_value, traditional_value))
        
        # 追加情報
        print(f"\n📊 追加情報:")
        print(f"   ブロック型 - ブロック数: {block_result.get('block_count', 0)}")
        print(f"   従来型 - 本文: {'あり' if traditional_result.get('body') else 'なし'}")
        print(f"   ブロック型 - JavaScript要素: {block_result.get('script_count', 0)}")
        print(f"   従来型 - JavaScript要素: {traditional_result.get('script_count', 0)}")
        
        # エディタ切り替えリンク
        print(f"\n🔄 エディタ切り替えリンク:")
        if block_result.get('switch_link'):
            print(f"   ブロック型→従来型: あり")
        else:
            print(f"   ブロック型→従来型: なし")
            
        if traditional_result.get('switch_link'):
            print(f"   従来型→ブロック型: あり")
        else:
            print(f"   従来型→ブロック型: なし")
        
        return inconsistencies

def main():
    """メインテスト実行"""
    print("🚀 記事ID 19のエディタ比較テスト開始")
    print("=" * 60)
    
    simulator = BrowserSimulator()
    
    # ログイン
    if not simulator.login():
        print("❌ ログインに失敗しました。テストを中断します。")
        return
    
    # 両エディタにアクセス
    block_result = simulator.access_block_editor(19)
    traditional_result = simulator.access_traditional_editor(19)
    
    # 比較実行
    inconsistencies = simulator.compare_editors(block_result, traditional_result)
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("📋 テスト結果サマリー")
    print("=" * 60)
    
    if inconsistencies:
        print(f"❌ {len(inconsistencies)}個の不整合が発見されました:")
        for field_name, block_value, traditional_value in inconsistencies:
            print(f"   • {field_name}")
    else:
        print("✅ 両エディタ間でデータの一貫性が保たれています")
    
    print("\n💡 推奨事項:")
    print("   1. 実際のブラウザで開発者ツールを開いてアクセス")
    print("   2. JavaScriptエラーがないかコンソールを確認")
    print("   3. エディタ切り替えリンクの動作確認")
    print("   4. 各エディタでの編集・保存動作確認")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 テストが中断されました")
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        import traceback
        traceback.print_exc()