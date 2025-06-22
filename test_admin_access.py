#!/usr/bin/env python3
"""
管理画面アクセステスト
記事ID 19の両エディタURLに実際にアクセスしてレスポンスを確認
"""

import requests
import re
from bs4 import BeautifulSoup
import sys

class AdminAccessTester:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.logged_in = False
    
    def login(self, email="admin@example.com", password="AdminPass123!"):
        """管理者としてログイン"""
        print("🔐 管理者ログインを試行中...")
        
        # ログインページにアクセスしてCSRFトークンを取得
        login_url = f"{self.base_url}/login/"
        response = self.session.get(login_url)
        
        if response.status_code != 200:
            print(f"❌ ログインページにアクセスできません: {response.status_code}")
            return False
        
        # CSRFトークンを抽出
        soup = BeautifulSoup(response.text, 'html.parser')
        csrf_token = None
        csrf_input = soup.find('input', {'name': 'csrf_token'})
        if csrf_input:
            csrf_token = csrf_input.get('value')
        
        if not csrf_token:
            print("❌ CSRFトークンが見つかりません")
            return False
        
        # ログイン情報を送信
        login_data = {
            'email': email,
            'password': password,
            'csrf_token': csrf_token
        }
        
        response = self.session.post(login_url, data=login_data, allow_redirects=False)
        
        if response.status_code in [302, 200]:
            # リダイレクト先を確認
            if response.status_code == 302:
                redirect_url = response.headers.get('Location', '/')
                print(f"✅ ログイン成功 (リダイレクト先: {redirect_url})")
            else:
                print("✅ ログイン成功")
            self.logged_in = True
            return True
        else:
            print(f"❌ ログイン失敗: {response.status_code}")
            return False
    
    def test_block_editor_access(self, article_id=19):
        """ブロック型エディタページのアクセステスト"""
        if not self.logged_in:
            print("❌ ログインが必要です")
            return None
        
        url = f"{self.base_url}/admin/article/block-editor/edit/{article_id}/"
        print(f"\n🧱 ブロック型エディタアクセステスト: {url}")
        
        try:
            response = self.session.get(url)
            print(f"   ステータスコード: {response.status_code}")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # ページタイトルを確認
                title = soup.find('title')
                if title:
                    print(f"   ページタイトル: {title.text.strip()}")
                
                # フォーム要素を確認
                form = soup.find('form')
                if form:
                    print("   ✅ フォーム要素が見つかりました")
                    
                    # 主要な入力フィールドを確認
                    title_input = soup.find('input', {'name': 'title'}) or soup.find('input', {'id': 'title'})
                    summary_input = soup.find('textarea', {'name': 'summary'}) or soup.find('textarea', {'id': 'summary'})
                    
                    if title_input:
                        title_value = title_input.get('value', '')
                        print(f"   📰 記事タイトル: {title_value}")
                    
                    if summary_input:
                        summary_value = summary_input.text.strip()
                        print(f"   📝 記事概要: {summary_value}")
                    
                    # 公開状態チェックボックス
                    is_published = soup.find('input', {'name': 'is_published', 'type': 'checkbox'})
                    if is_published:
                        checked = 'checked' in is_published.attrs
                        print(f"   ✅ 公開状態: {'公開' if checked else '下書き'}")
                    
                    # コメント許可チェックボックス
                    allow_comments = soup.find('input', {'name': 'allow_comments', 'type': 'checkbox'})
                    if allow_comments:
                        checked = 'checked' in allow_comments.attrs
                        print(f"   💬 コメント許可: {'許可' if checked else '許可しない'}")
                
                # エディタ切り替えリンクを確認
                editor_switch_link = soup.find('a', href=re.compile(r'/admin/article/edit/\d+/'))
                if editor_switch_link:
                    print(f"   🔄 従来型エディタリンク: {editor_switch_link.get('href')}")
                else:
                    print("   ❌ 従来型エディタリンクが見つかりません")
                
                # JavaScriptエラーチェック（静的）
                scripts = soup.find_all('script')
                print(f"   📜 JavaScriptファイル数: {len(scripts)}")
                
                return {
                    'status': 'success',
                    'status_code': response.status_code,
                    'has_form': form is not None,
                    'title': title_value if 'title_value' in locals() else None,
                    'summary': summary_value if 'summary_value' in locals() else None,
                }
            
            elif response.status_code == 302:
                redirect_url = response.headers.get('Location', '')
                print(f"   🔄 リダイレクト: {redirect_url}")
                return {'status': 'redirect', 'redirect_url': redirect_url}
            
            else:
                print(f"   ❌ アクセス失敗: {response.status_code}")
                return {'status': 'error', 'status_code': response.status_code}
                
        except Exception as e:
            print(f"   ❌ エラー: {e}")
            return {'status': 'exception', 'error': str(e)}
    
    def test_traditional_editor_access(self, article_id=19):
        """従来型エディタページのアクセステスト"""
        if not self.logged_in:
            print("❌ ログインが必要です")
            return None
        
        url = f"{self.base_url}/admin/article/edit/{article_id}/"
        print(f"\n📝 従来型エディタアクセステスト: {url}")
        
        try:
            response = self.session.get(url)
            print(f"   ステータスコード: {response.status_code}")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # ページタイトルを確認
                title = soup.find('title')
                if title:
                    print(f"   ページタイトル: {title.text.strip()}")
                
                # フォーム要素を確認
                form = soup.find('form')
                if form:
                    print("   ✅ フォーム要素が見つかりました")
                    
                    # 主要な入力フィールドを確認
                    title_input = soup.find('input', {'name': 'title'}) or soup.find('input', {'id': 'title'})
                    summary_input = soup.find('textarea', {'name': 'summary'}) or soup.find('textarea', {'id': 'summary'})
                    body_input = soup.find('textarea', {'name': 'body'}) or soup.find('textarea', {'id': 'body'})
                    
                    if title_input:
                        title_value = title_input.get('value', '')
                        print(f"   📰 記事タイトル: {title_value}")
                    
                    if summary_input:
                        summary_value = summary_input.text.strip()
                        print(f"   📝 記事概要: {summary_value}")
                    
                    if body_input:
                        body_value = body_input.text.strip()
                        body_preview = body_value[:100] + "..." if len(body_value) > 100 else body_value
                        print(f"   📄 本文: {body_preview}")
                    
                    # 公開状態チェックボックス
                    is_published = soup.find('input', {'name': 'is_published', 'type': 'checkbox'})
                    if is_published:
                        checked = 'checked' in is_published.attrs
                        print(f"   ✅ 公開状態: {'公開' if checked else '下書き'}")
                    
                    # コメント許可チェックボックス
                    allow_comments = soup.find('input', {'name': 'allow_comments', 'type': 'checkbox'})
                    if allow_comments:
                        checked = 'checked' in allow_comments.attrs
                        print(f"   💬 コメント許可: {'許可' if checked else '許可しない'}")
                
                # エディタ切り替えリンクを確認
                editor_switch_link = soup.find('a', href=re.compile(r'/admin/article/block-editor/edit/\d+/'))
                if editor_switch_link:
                    print(f"   🔄 ブロック型エディタリンク: {editor_switch_link.get('href')}")
                else:
                    print("   ❌ ブロック型エディタリンクが見つかりません")
                    
                return {
                    'status': 'success',
                    'status_code': response.status_code,
                    'has_form': form is not None,
                    'title': title_value if 'title_value' in locals() else None,
                    'summary': summary_value if 'summary_value' in locals() else None,
                    'body': body_value if 'body_value' in locals() else None,
                }
            
            elif response.status_code == 302:
                redirect_url = response.headers.get('Location', '')
                print(f"   🔄 リダイレクト: {redirect_url}")
                return {'status': 'redirect', 'redirect_url': redirect_url}
            
            else:
                print(f"   ❌ アクセス失敗: {response.status_code}")
                return {'status': 'error', 'status_code': response.status_code}
                
        except Exception as e:
            print(f"   ❌ エラー: {e}")
            return {'status': 'exception', 'error': str(e)}
    
    def compare_results(self, block_result, traditional_result):
        """両エディタの結果を比較"""
        print("\n" + "=" * 60)
        print("🔍 両エディタアクセス結果の比較")
        print("=" * 60)
        
        if not block_result or not traditional_result:
            print("❌ 比較に必要なデータが不足しています")
            return
        
        # 基本的なアクセス状況
        print(f"ブロック型エディタ: {block_result['status']}")
        print(f"従来型エディタ: {traditional_result['status']}")
        
        # 両方成功した場合の詳細比較
        if (block_result['status'] == 'success' and 
            traditional_result['status'] == 'success'):
            
            print("\n📊 フォームデータ比較:")
            
            # タイトル比較
            block_title = block_result.get('title')
            trad_title = traditional_result.get('title')
            if block_title == trad_title:
                print(f"✅ タイトル: 一致 ({block_title})")
            else:
                print(f"❌ タイトル: 不一致")
                print(f"   ブロック型: {block_title}")
                print(f"   従来型: {trad_title}")
            
            # 概要比較
            block_summary = block_result.get('summary')
            trad_summary = traditional_result.get('summary')
            if block_summary == trad_summary:
                print(f"✅ 概要: 一致")
            else:
                print(f"❌ 概要: 不一致")
                print(f"   ブロック型: {block_summary}")
                print(f"   従来型: {trad_summary}")

def main():
    """メインテスト実行"""
    print("🚀 記事ID 19の管理画面アクセステスト開始")
    print("=" * 60)
    
    tester = AdminAccessTester()
    
    # ログイン
    if not tester.login():
        print("❌ ログインに失敗しました。テストを中断します。")
        sys.exit(1)
    
    # 両エディタにアクセス
    block_result = tester.test_block_editor_access(19)
    traditional_result = tester.test_traditional_editor_access(19)
    
    # 結果比較
    tester.compare_results(block_result, traditional_result)
    
    print("\n✅ テスト完了")
    print("\n💡 追加確認事項:")
    print("   - ブラウザの開発者ツールでJavaScriptエラーを確認")
    print("   - エディタ切り替えリンクの実際の動作")
    print("   - 各エディタでの編集・保存動作")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 テストが中断されました")
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        import traceback
        traceback.print_exc()