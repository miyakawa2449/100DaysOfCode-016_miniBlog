#!/usr/bin/env python3
"""
AI/LLM を使用したSEO対策機能
記事のSEO最適化提案、メタタグ生成、キーワード分析などを行う
"""

import re
import json
import requests
from datetime import datetime
from collections import Counter
import hashlib
from urllib.parse import urljoin

class SEOOptimizer:
    """SEO最適化クラス"""
    
    def __init__(self, api_key=None, api_provider='openai'):
        self.api_key = api_key
        self.api_provider = api_provider
        self.max_tokens = 1000
        
    def analyze_content(self, title, content, target_keywords=None):
        """コンテンツのSEO分析を実行"""
        analysis = {
            'title_analysis': self.analyze_title(title),
            'content_analysis': self.analyze_content_structure(content),
            'keyword_density': self.analyze_keyword_density(content, target_keywords),
            'readability': self.analyze_readability(content),
            'meta_suggestions': self.generate_meta_suggestions(title, content),
            'seo_score': 0,
            'recommendations': []
        }
        
        # SEOスコア計算
        analysis['seo_score'] = self.calculate_seo_score(analysis)
        
        # 改善提案生成
        analysis['recommendations'] = self.generate_recommendations(analysis)
        
        return analysis
    
    def analyze_title(self, title):
        """タイトル分析"""
        if not title:
            return {
                'length': 0,
                'word_count': 0,
                'has_numbers': False,
                'has_power_words': False,
                'score': 0,
                'issues': ['タイトルが設定されていません']
            }
        
        length = len(title)
        word_count = len(title.split())
        has_numbers = bool(re.search(r'\d', title))
        
        # パワーワード検出
        power_words = [
            '完全', '究極', '最新', '最強', '簡単', '効果的', '必見', '秘密',
            '解説', '方法', 'まとめ', '徹底', '実践', '攻略', 'ガイド'
        ]
        has_power_words = any(word in title for word in power_words)
        
        issues = []
        if length < 20:
            issues.append('タイトルが短すぎます（20文字以上推奨）')
        elif length > 60:
            issues.append('タイトルが長すぎます（60文字以内推奨）')
        
        if word_count < 3:
            issues.append('タイトルの語数が少なすぎます')
        
        if not has_numbers and not has_power_words:
            issues.append('数字やパワーワードを含めると効果的です')
        
        # スコア計算
        score = 0
        if 20 <= length <= 60:
            score += 30
        if word_count >= 3:
            score += 20
        if has_numbers:
            score += 25
        if has_power_words:
            score += 25
        
        return {
            'length': length,
            'word_count': word_count,
            'has_numbers': has_numbers,
            'has_power_words': has_power_words,
            'score': score,
            'issues': issues
        }
    
    def analyze_content_structure(self, content):
        """コンテンツ構造分析"""
        if not content:
            return {
                'word_count': 0,
                'paragraph_count': 0,
                'heading_count': 0,
                'image_count': 0,
                'link_count': 0,
                'score': 0,
                'issues': ['コンテンツが設定されていません']
            }
        
        # 基本統計
        word_count = len(content.split())
        paragraph_count = len([p for p in content.split('\n\n') if p.strip()])
        
        # HTML要素カウント
        heading_count = len(re.findall(r'<h[1-6]', content, re.IGNORECASE))
        image_count = len(re.findall(r'<img', content, re.IGNORECASE))
        link_count = len(re.findall(r'<a\s+[^>]*href', content, re.IGNORECASE))
        
        issues = []
        if word_count < 300:
            issues.append('コンテンツが短すぎます（300語以上推奨）')
        elif word_count > 3000:
            issues.append('コンテンツが長すぎる可能性があります')
        
        if heading_count == 0:
            issues.append('見出しタグ（H1-H6）を使用してください')
        
        if paragraph_count < 3:
            issues.append('段落を増やして読みやすくしてください')
        
        if image_count == 0:
            issues.append('画像を追加すると効果的です')
        
        # スコア計算
        score = 0
        if word_count >= 300:
            score += 25
        if heading_count > 0:
            score += 25
        if paragraph_count >= 3:
            score += 25
        if image_count > 0:
            score += 25
        
        return {
            'word_count': word_count,
            'paragraph_count': paragraph_count,
            'heading_count': heading_count,
            'image_count': image_count,
            'link_count': link_count,
            'score': score,
            'issues': issues
        }
    
    def analyze_keyword_density(self, content, target_keywords=None):
        """キーワード密度分析"""
        if not content:
            return {'density': {}, 'score': 0, 'issues': []}
        
        # HTMLタグを除去
        clean_content = re.sub(r'<[^>]+>', '', content)
        words = re.findall(r'\b\w+\b', clean_content.lower())
        total_words = len(words)
        
        if total_words == 0:
            return {'density': {}, 'score': 0, 'issues': ['コンテンツが空です']}
        
        word_count = Counter(words)
        density = {}
        issues = []
        
        # 目標キーワードの密度チェック
        if target_keywords:
            for keyword in target_keywords:
                count = word_count.get(keyword.lower(), 0)
                density[keyword] = {
                    'count': count,
                    'density': round(count / total_words * 100, 2)
                }
                
                if density[keyword]['density'] < 0.5:
                    issues.append(f'キーワード「{keyword}」の密度が低すぎます')
                elif density[keyword]['density'] > 3.0:
                    issues.append(f'キーワード「{keyword}」の密度が高すぎます')
        
        # 上位語句の分析
        common_words = word_count.most_common(10)
        top_density = {}
        for word, count in common_words:
            if len(word) > 2:  # 短い語句を除外
                top_density[word] = {
                    'count': count,
                    'density': round(count / total_words * 100, 2)
                }
        
        score = 50  # 基本スコア
        if target_keywords:
            for keyword in target_keywords:
                kw_density = density.get(keyword, {}).get('density', 0)
                if 0.5 <= kw_density <= 3.0:
                    score += 10
                else:
                    score -= 10
        
        return {
            'density': density,
            'top_words': top_density,
            'total_words': total_words,
            'score': max(0, score),
            'issues': issues
        }
    
    def analyze_readability(self, content):
        """読みやすさ分析"""
        if not content:
            return {'score': 0, 'level': 'なし', 'issues': []}
        
        # HTMLタグを除去
        clean_content = re.sub(r'<[^>]+>', '', content)
        
        # 基本統計
        sentences = re.split(r'[。！？]', clean_content)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return {'score': 0, 'level': 'なし', 'issues': ['文章が検出されませんでした']}
        
        words = re.findall(r'\b\w+\b', clean_content)
        avg_sentence_length = len(words) / len(sentences)
        
        # 簡易読みやすさスコア
        issues = []
        if avg_sentence_length > 25:
            issues.append('文が長すぎます（25語以下推奨）')
        
        # 漢字比率チェック
        kanji_count = len(re.findall(r'[\u4e00-\u9faf]', clean_content))
        total_chars = len(clean_content)
        kanji_ratio = kanji_count / total_chars if total_chars > 0 else 0
        
        if kanji_ratio > 0.4:
            issues.append('漢字の使用率が高すぎます（40%以下推奨）')
        
        # スコア計算
        score = 100
        if avg_sentence_length > 25:
            score -= 20
        if kanji_ratio > 0.4:
            score -= 20
        if len(sentences) < 3:
            score -= 20
        
        level = 'やや難しい'
        if score >= 80:
            level = '読みやすい'
        elif score >= 60:
            level = '普通'
        elif score >= 40:
            level = 'やや難しい'
        else:
            level = '難しい'
        
        return {
            'score': max(0, score),
            'level': level,
            'avg_sentence_length': round(avg_sentence_length, 1),
            'kanji_ratio': round(kanji_ratio * 100, 1),
            'sentence_count': len(sentences),
            'issues': issues
        }
    
    def generate_meta_suggestions(self, title, content):
        """メタタグ提案生成"""
        suggestions = {}
        
        # メタディスクリプション生成
        if content:
            # HTMLタグを除去
            clean_content = re.sub(r'<[^>]+>', '', content)
            # 最初の段落を使用
            first_paragraph = clean_content.split('\n')[0]
            
            if len(first_paragraph) > 160:
                description = first_paragraph[:157] + '...'
            else:
                description = first_paragraph
            
            suggestions['description'] = description
        
        # キーワード提案
        if content:
            clean_content = re.sub(r'<[^>]+>', '', content)
            words = re.findall(r'\b\w{3,}\b', clean_content.lower())
            word_count = Counter(words)
            
            # 上位キーワードを抽出
            keywords = [word for word, count in word_count.most_common(10) 
                       if count > 1 and len(word) > 2]
            suggestions['keywords'] = ', '.join(keywords[:5])
        
        # OGタイトル提案
        if title:
            suggestions['og_title'] = title
        
        return suggestions
    
    def calculate_seo_score(self, analysis):
        """総合SEOスコア計算"""
        scores = [
            analysis['title_analysis']['score'],
            analysis['content_analysis']['score'],
            analysis['keyword_density']['score'],
            analysis['readability']['score']
        ]
        
        return round(sum(scores) / len(scores))
    
    def generate_recommendations(self, analysis):
        """改善提案生成"""
        recommendations = []
        
        # タイトル関連
        if analysis['title_analysis']['score'] < 70:
            recommendations.extend(analysis['title_analysis']['issues'])
        
        # コンテンツ関連
        if analysis['content_analysis']['score'] < 70:
            recommendations.extend(analysis['content_analysis']['issues'])
        
        # キーワード関連
        if analysis['keyword_density']['score'] < 70:
            recommendations.extend(analysis['keyword_density']['issues'])
        
        # 読みやすさ関連
        if analysis['readability']['score'] < 70:
            recommendations.extend(analysis['readability']['issues'])
        
        # 一般的な提案
        if analysis['seo_score'] < 80:
            recommendations.append('内部リンクを追加してください')
            recommendations.append('外部の信頼できるサイトへのリンクを追加してください')
            recommendations.append('画像にalt属性を設定してください')
        
        return list(set(recommendations))  # 重複除去
    
    def generate_llm_suggestions(self, title, content, target_keywords=None):
        """LLMを使用した高度なSEO提案（モック実装）"""
        if not self.api_key:
            return {
                'title_suggestions': [
                    f'{title} - 完全ガイド',
                    f'{title}の効果的な方法',
                    f'【最新】{title}まとめ'
                ],
                'meta_description': f'{title}について詳しく解説します。初心者にも分かりやすく、実践的な内容をお届けします。',
                'content_outline': [
                    '導入部分',
                    '基本概念の説明',
                    '具体的な手順',
                    '注意点とコツ',
                    'まとめ'
                ],
                'related_keywords': [
                    '初心者向け',
                    '使い方',
                    '効果的',
                    '実践的',
                    'まとめ'
                ]
            }
        
        # 実際のLLM API呼び出し（実装例）
        try:
            prompt = f"""
            以下の記事のSEO最適化提案をしてください：
            
            タイトル: {title}
            コンテンツ: {content[:500]}...
            ターゲットキーワード: {target_keywords}
            
            以下の形式でJSONで回答してください：
            {{
                "title_suggestions": ["改善されたタイトル1", "改善されたタイトル2", "改善されたタイトル3"],
                "meta_description": "改善されたメタディスクリプション",
                "content_outline": ["項目1", "項目2", "項目3"],
                "related_keywords": ["関連キーワード1", "関連キーワード2"]
            }}
            """
            
            # OpenAI API呼び出し例（要実装）
            # response = openai.ChatCompletion.create(...)
            
            # モック応答
            return {
                'title_suggestions': [
                    f'{title} - プロが教える効果的な方法',
                    f'【2025年最新】{title}の完全ガイド',
                    f'{title}で成果を出すための実践的テクニック'
                ],
                'meta_description': f'{title}について、専門家が詳しく解説。初心者から上級者まで役立つ実践的な情報をお届けします。',
                'content_outline': [
                    f'{title}とは？基本概念の解説',
                    '始める前の準備と注意点',
                    'ステップバイステップの実践方法',
                    'よくある失敗とその対策',
                    'さらに効果を高めるコツ',
                    'まとめと次のステップ'
                ],
                'related_keywords': [
                    '初心者',
                    '効果的',
                    '方法',
                    '実践',
                    'コツ',
                    'テクニック'
                ]
            }
        except Exception as e:
            print(f"LLM API呼び出しエラー: {e}")
            return None

def main():
    """テスト実行"""
    optimizer = SEOOptimizer()
    
    # テストデータ
    title = "Pythonプログラミング入門"
    content = """
    <h1>Pythonプログラミング入門</h1>
    <p>Pythonは初心者にも学びやすいプログラミング言語です。</p>
    <p>この記事では、Pythonの基本的な使い方から実践的な応用まで解説します。</p>
    <h2>Pythonとは</h2>
    <p>Pythonは1991年に開発されたプログラミング言語で、シンプルで読みやすい構文が特徴です。</p>
    """
    target_keywords = ['Python', 'プログラミング', '入門']
    
    # SEO分析実行
    analysis = optimizer.analyze_content(title, content, target_keywords)
    
    print("=== SEO分析結果 ===")
    print(f"総合スコア: {analysis['seo_score']}/100")
    print(f"\nタイトル分析: {analysis['title_analysis']['score']}/100")
    print(f"コンテンツ分析: {analysis['content_analysis']['score']}/100")
    print(f"キーワード密度: {analysis['keyword_density']['score']}/100")
    print(f"読みやすさ: {analysis['readability']['score']}/100")
    
    print(f"\n改善提案:")
    for rec in analysis['recommendations']:
        print(f"- {rec}")
    
    print(f"\nメタタグ提案:")
    for key, value in analysis['meta_suggestions'].items():
        print(f"- {key}: {value}")

if __name__ == '__main__':
    main()