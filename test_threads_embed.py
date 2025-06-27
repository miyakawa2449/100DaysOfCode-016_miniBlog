#!/usr/bin/env python3
"""
Test script for Threads embed functionality
"""

from app import app, markdown_filter
import sys

def test_threads_embed():
    """Test the improved Threads embed functionality"""
    
    # Test markdown with Threads URL
    test_content = """
# Threads投稿のテスト

こちらはThreadsの投稿です：

https://www.threads.com/@miyakawa2449/post/DLUVx_svglN

このように表示されるはずです。新しいデザインでOGPデータが取得できない場合でも、ユーザー名や投稿IDから情報を生成します。

## その他のSNS

YouTube: https://youtu.be/dQw4w9WgXcQ

Twitter: https://twitter.com/example/status/1234567890
"""
    
    with app.app_context():
        # Markdownフィルターを使用してHTMLに変換
        html_output = markdown_filter(test_content)
        
        print("=== Test Markdown Content ===")
        print(test_content)
        print("\n=== Generated HTML Output ===")
        print(html_output)
        print("\n=== Test Complete ===")
        
        # Threads埋込部分を確認
        if 'threads-embed' in str(html_output):
            print("\n✅ Threads embed generated successfully!")
            
            # 改善された要素の確認
            if 'miyakawa2449' in str(html_output):
                print("✅ Username extracted correctly")
            if 'DLUVx_sv' in str(html_output):  # 投稿IDの最初の8文字
                print("✅ Post ID extracted correctly")
            if 'linear-gradient' in str(html_output):
                print("✅ Enhanced visual design applied")
            if '🧵' in str(html_output):
                print("✅ Threads emoji included")
            
        else:
            print("❌ Threads embed not found in output")
            
        return str(html_output)

if __name__ == "__main__":
    result = test_threads_embed()
    
    # 結果をファイルに保存
    with open('/Users/tsuyoshi/development/mini-blog/test_output.html', 'w', encoding='utf-8') as f:
        f.write(f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Threads Embed Test</title>
</head>
<body>
    <div style="max-width: 800px; margin: 0 auto; padding: 20px;">
        <h1>Threads Embed Test Result</h1>
        {result}
    </div>
</body>
</html>""")
    
    print(f"\n📄 HTML output saved to: test_output.html")
    print("🌐 You can open this file in a browser to see the visual result")