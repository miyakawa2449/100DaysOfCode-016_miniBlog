import requests
import re

try:
    response = requests.get('http://localhost:5000/article/kanazawarbmeetup154/', timeout=5)
    if response.status_code == 200:
        print(f"Response status: {response.status_code}")
        print(f"Response length: {len(response.text)}")
        
        # YouTube埋込部分を詳細に抽出
        youtube_sections = re.findall(r'<div class="sns-embed-container sns-youtube">.*?</div>\s*</div>', response.text, re.DOTALL)
        print(f'\nFound {len(youtube_sections)} YouTube embed sections:')
        for i, section in enumerate(youtube_sections):
            print(f'\n--- YouTube Embed {i+1} ---')
            print(section)
        
        # iframeを直接確認
        iframes = re.findall(r'<iframe[^>]*youtube[^>]*>.*?</iframe>', response.text, re.DOTALL | re.IGNORECASE)
        print(f'\n\nFound {len(iframes)} YouTube iframes:')
        for i, iframe in enumerate(iframes):
            print(f'\n--- YouTube iframe {i+1} ---')
            print(iframe)

        # エラーメッセージを確認
        if 'ブロックの表示でエラーが発生しました' in response.text:
            print('\n⚠️ Block rendering error found!')
            
        # CSPエラー関連を確認
        if 'Content-Security-Policy' in response.text:
            print('\n⚠️ CSP related content found in HTML')
            
except Exception as e:
    print(f'Error: {e}')