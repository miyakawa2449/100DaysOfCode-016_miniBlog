"""
LLMO（Large Language Model Optimization）分析機能
AI時代の検索エンジンに最適化されたコンテンツ分析
"""

import re
import json
from typing import Dict, List, Any, Tuple
from datetime import datetime
import hashlib
from markupsafe import Markup
import markdown
from bs4 import BeautifulSoup

class LLMOAnalyzer:
    """LLM向けコンテンツ最適化分析クラス"""
    
    def __init__(self):
        self.readability_weights = {
            'sentence_length': 0.3,
            'paragraph_length': 0.2,
            'heading_structure': 0.3,
            'keyword_density': 0.2
        }
        
        self.semantic_weights = {
            'heading_hierarchy': 0.4,
            'entity_density': 0.3,
            'topic_coherence': 0.3
        }
    
    def analyze_content_for_llm(self, content: str, title: str = "", keywords: List[str] = None) -> Dict[str, Any]:
        """LLM向けコンテンツ最適化分析のメイン関数"""
        if keywords is None:
            keywords = []
        
        # Markdownをプレーンテキストに変換
        plain_text = self._markdown_to_text(content)
        html_content = markdown.markdown(content)
        
        analysis_result = {
            'readability_score': self.calculate_readability(plain_text),
            'semantic_structure': self.analyze_semantic_structure(html_content, title),
            'entity_extraction': self.extract_entities(plain_text),
            'topic_coherence': self.analyze_topic_coherence(plain_text, keywords),
            'llm_friendliness_score': 0,  # 後で計算
            'word_count': len(plain_text.split()),
            'character_count': len(plain_text),
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        # LLM親和性スコアを計算
        analysis_result['llm_friendliness_score'] = self._calculate_llm_score(analysis_result)
        
        return analysis_result
    
    def calculate_readability(self, text: str) -> Dict[str, float]:
        """読みやすさスコアを計算"""
        sentences = self._split_sentences(text)
        paragraphs = text.split('\n\n')
        words = text.split()
        
        # 基本指標
        avg_sentence_length = len(words) / max(len(sentences), 1)
        avg_paragraph_length = len(sentences) / max(len(paragraphs), 1)
        
        # 文の長さスコア（15-25語が理想）
        sentence_score = max(0, 100 - abs(avg_sentence_length - 20) * 2)
        
        # 段落の長さスコア（3-5文が理想）
        paragraph_score = max(0, 100 - abs(avg_paragraph_length - 4) * 10)
        
        return {
            'sentence_score': min(sentence_score, 100),
            'paragraph_score': min(paragraph_score, 100),
            'avg_sentence_length': avg_sentence_length,
            'avg_paragraph_length': avg_paragraph_length,
            'total_score': (sentence_score + paragraph_score) / 2
        }
    
    def analyze_semantic_structure(self, html_content: str, title: str = "") -> Dict[str, Any]:
        """セマンティック構造を分析"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 見出し構造の分析
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        heading_structure = self._analyze_heading_hierarchy(headings)
        
        # リスト構造の分析
        lists = soup.find_all(['ul', 'ol'])
        list_score = min(len(lists) * 10, 100)  # リストがあると構造化スコアアップ
        
        # 強調要素の分析
        emphasis = soup.find_all(['strong', 'b', 'em', 'i'])
        emphasis_score = min(len(emphasis) * 5, 50)  # 適度な強調が重要
        
        return {
            'heading_hierarchy_score': heading_structure['score'],
            'heading_count': len(headings),
            'list_score': list_score,
            'emphasis_score': emphasis_score,
            'total_structure_score': (heading_structure['score'] + list_score + emphasis_score) / 3,
            'headings': [{'level': h.name, 'text': h.get_text().strip()} for h in headings]
        }
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """エンティティ（重要な名詞）を抽出（簡易版）"""
        # 簡易的な実装（実際のプロダクションではspaCyやNLTKを使用）
        
        # 日本語の固有名詞パターン（カタカナ、英数字混在）
        katakana_pattern = re.findall(r'[ァ-ヴー]{2,}', text)
        english_pattern = re.findall(r'[A-Z][a-zA-Z]{2,}', text)
        
        # 技術用語パターン
        tech_terms = re.findall(r'(Python|JavaScript|HTML|CSS|SQL|API|JSON|XML|HTTP|HTTPS|URL|SEO|AI|ML|LLM)', text, re.IGNORECASE)
        
        # 数値データ
        numbers = re.findall(r'\d+(?:\.\d+)?(?:%|件|個|人|回|時間|分|秒)', text)
        
        return {
            'organizations': list(set(katakana_pattern[:10])),  # 上位10件
            'persons': list(set(english_pattern[:10])),
            'technologies': list(set([t.upper() for t in tech_terms])),
            'metrics': list(set(numbers[:10])),
            'total_entities': len(set(katakana_pattern + english_pattern + tech_terms + numbers))
        }
    
    def analyze_topic_coherence(self, text: str, keywords: List[str] = None) -> Dict[str, Any]:
        """トピックの一貫性を分析"""
        if keywords is None:
            keywords = []
        
        words = text.lower().split()
        total_words = len(words)
        
        # キーワード密度計算
        keyword_density = {}
        total_keyword_mentions = 0
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            mentions = text.lower().count(keyword_lower)
            density = (mentions / max(total_words, 1)) * 100
            keyword_density[keyword] = {
                'mentions': mentions,
                'density': density
            }
            total_keyword_mentions += mentions
        
        # 理想的なキーワード密度は1-3%
        overall_density = (total_keyword_mentions / max(total_words, 1)) * 100
        density_score = max(0, 100 - abs(overall_density - 2) * 20)
        
        # 関連語の分析（簡易版）
        related_terms = self._find_related_terms(text, keywords)
        
        return {
            'keyword_density': keyword_density,
            'overall_density': overall_density,
            'density_score': min(density_score, 100),
            'related_terms': related_terms,
            'coherence_score': min((density_score + len(related_terms) * 5), 100)
        }
    
    def _calculate_llm_score(self, analysis: Dict[str, Any]) -> float:
        """LLM親和性の総合スコアを計算"""
        readability = analysis['readability_score']['total_score']
        structure = analysis['semantic_structure']['total_structure_score']
        coherence = analysis['topic_coherence']['coherence_score']
        
        # 重み付き平均
        total_score = (
            readability * self.readability_weights['sentence_length'] +
            structure * self.semantic_weights['heading_hierarchy'] +
            coherence * 0.4
        )
        
        return min(total_score, 100)
    
    def _markdown_to_text(self, markdown_content: str) -> str:
        """Markdownをプレーンテキストに変換"""
        # MarkdownをHTMLに変換
        html = markdown.markdown(markdown_content)
        # HTMLタグを除去
        soup = BeautifulSoup(html, 'html.parser')
        return soup.get_text()
    
    def _split_sentences(self, text: str) -> List[str]:
        """文章を文に分割"""
        # 日本語と英語の文末を考慮
        sentences = re.split(r'[.!?。！？]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _analyze_heading_hierarchy(self, headings: List) -> Dict[str, Any]:
        """見出し階層の適切性を分析"""
        if not headings:
            return {'score': 0, 'issues': ['見出しがありません']}
        
        hierarchy_levels = [int(h.name[1]) for h in headings]
        issues = []
        score = 100
        
        # H1の存在チェック
        if 1 not in hierarchy_levels:
            issues.append('H1見出しがありません')
            score -= 20
        
        # 階層の飛びをチェック
        for i in range(1, len(hierarchy_levels)):
            if hierarchy_levels[i] - hierarchy_levels[i-1] > 1:
                issues.append(f'見出し階層に飛びがあります (H{hierarchy_levels[i-1]} → H{hierarchy_levels[i]})')
                score -= 10
        
        # 見出しの数が適切かチェック
        if len(headings) < 2:
            issues.append('見出しが少なすぎます')
            score -= 15
        elif len(headings) > 10:
            issues.append('見出しが多すぎます')
            score -= 10
        
        return {
            'score': max(score, 0),
            'issues': issues,
            'heading_count': len(headings),
            'levels_used': sorted(set(hierarchy_levels))
        }
    
    def _find_related_terms(self, text: str, keywords: List[str]) -> List[str]:
        """関連語を抽出（簡易版）"""
        # 技術関連の関連語辞書（例）
        related_dict = {
            'python': ['プログラミング', 'コード', 'スクリプト', 'ライブラリ', 'フレームワーク'],
            'web': ['ウェブ', 'サイト', 'ブラウザ', 'HTML', 'CSS', 'JavaScript'],
            'ai': ['人工知能', '機械学習', 'ディープラーニング', 'アルゴリズム', 'データ'],
            'seo': ['検索エンジン', 'Google', 'キーワード', 'ランキング', '最適化']
        }
        
        found_terms = []
        text_lower = text.lower()
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            for key, terms in related_dict.items():
                if key in keyword_lower:
                    for term in terms:
                        if term in text_lower:
                            found_terms.append(term)
        
        return list(set(found_terms))

class AIOOptimizer:
    """AI Overview向け最適化クラス"""
    
    def __init__(self):
        self.snippet_max_length = 160
        self.qa_max_pairs = 5
        self.fact_max_count = 10
    
    def optimize_for_ai_overview(self, article_content: str, title: str = "") -> Dict[str, Any]:
        """AI Overview向け最適化のメイン関数"""
        plain_text = self._markdown_to_text(article_content)
        
        return {
            'featured_snippet_candidates': self.extract_snippets(plain_text),
            'qa_pairs': self.generate_qa_pairs(plain_text, title),
            'key_facts': self.extract_key_facts(plain_text),
            'answer_worthy_content': self.identify_answer_content(plain_text),
            'optimization_score': self._calculate_aio_score(plain_text)
        }
    
    def extract_snippets(self, text: str) -> List[Dict[str, str]]:
        """フィーチャードスニペット候補を抽出"""
        sentences = self._split_sentences(text)
        snippets = []
        
        for sentence in sentences:
            if len(sentence) <= self.snippet_max_length and len(sentence) >= 50:
                # 定義文や説明文の候補
                if any(pattern in sentence for pattern in ['とは', 'である', 'です', 'means', 'is']):
                    snippets.append({
                        'text': sentence,
                        'type': 'definition',
                        'length': len(sentence)
                    })
                # 手順や方法の候補
                elif any(pattern in sentence for pattern in ['方法', '手順', 'ステップ', 'how to', 'step']):
                    snippets.append({
                        'text': sentence,
                        'type': 'instruction',
                        'length': len(sentence)
                    })
        
        # 長さでソートして上位候補を返す
        return sorted(snippets, key=lambda x: x['length'])[:5]
    
    def generate_qa_pairs(self, text: str, title: str = "") -> List[Dict[str, str]]:
        """質問-回答ペアを自動生成"""
        qa_pairs = []
        sentences = self._split_sentences(text)
        
        # タイトルから質問生成
        if title:
            qa_pairs.append({
                'question': f"{title}とは何ですか？",
                'answer': sentences[0] if sentences else "",
                'type': 'title_based'
            })
        
        # 定義文から質問生成
        for sentence in sentences:
            if 'とは' in sentence and len(sentence) < 200:
                parts = sentence.split('とは')
                if len(parts) >= 2:
                    subject = parts[0].strip()
                    definition = 'とは'.join(parts[1:]).strip()
                    qa_pairs.append({
                        'question': f"{subject}とは何ですか？",
                        'answer': definition,
                        'type': 'definition'
                    })
        
        # 理由や方法を説明する文から質問生成
        for sentence in sentences:
            if any(word in sentence for word in ['理由', '原因', 'なぜ']) and len(sentence) < 200:
                qa_pairs.append({
                    'question': f"なぜ{sentence.split('理由')[0] if '理由' in sentence else sentence[:20]}...ですか？",
                    'answer': sentence,
                    'type': 'reason'
                })
        
        return qa_pairs[:self.qa_max_pairs]
    
    def extract_key_facts(self, text: str) -> List[Dict[str, Any]]:
        """キーファクトを抽出"""
        facts = []
        
        # 数値データを含む文
        number_pattern = r'(\d+(?:\.\d+)?(?:%|件|個|人|回|時間|分|秒|年|月|日))'
        sentences = self._split_sentences(text)
        
        for sentence in sentences:
            numbers = re.findall(number_pattern, sentence)
            if numbers:
                facts.append({
                    'text': sentence,
                    'metrics': numbers,
                    'type': 'quantitative',
                    'confidence': 0.8
                })
        
        # 重要そうな文（強調語を含む）
        emphasis_words = ['重要', '注意', 'ポイント', '特徴', '利点', '効果', 'メリット']
        for sentence in sentences:
            if any(word in sentence for word in emphasis_words):
                facts.append({
                    'text': sentence,
                    'type': 'qualitative',
                    'confidence': 0.7
                })
        
        return facts[:self.fact_max_count]
    
    def identify_answer_content(self, text: str) -> Dict[str, List[str]]:
        """回答に適したコンテンツを特定"""
        sentences = self._split_sentences(text)
        
        answer_content = {
            'how_to': [],
            'what_is': [],
            'why': [],
            'benefits': [],
            'steps': []
        }
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            
            # How-to系
            if any(word in sentence for word in ['方法', '手順', 'やり方', 'how']):
                answer_content['how_to'].append(sentence)
            
            # 定義系
            elif any(word in sentence for word in ['とは', 'である', '定義', 'what is']):
                answer_content['what_is'].append(sentence)
            
            # 理由系
            elif any(word in sentence for word in ['理由', '原因', 'なぜ', 'why']):
                answer_content['why'].append(sentence)
            
            # メリット系
            elif any(word in sentence for word in ['利点', 'メリット', '効果', 'benefit']):
                answer_content['benefits'].append(sentence)
            
            # ステップ系
            elif any(word in sentence for word in ['ステップ', '段階', 'step', '工程']):
                answer_content['steps'].append(sentence)
        
        return answer_content
    
    def _calculate_aio_score(self, text: str) -> float:
        """AI Overview最適化スコアを計算"""
        sentences = self._split_sentences(text)
        
        # 構造化要素の存在
        structure_score = 0
        if any('とは' in s for s in sentences):
            structure_score += 20
        if any(word in text for word in ['方法', '手順', 'ステップ']):
            structure_score += 20
        if re.search(r'\d+', text):
            structure_score += 15
        if any(word in text for word in ['利点', 'メリット', '効果']):
            structure_score += 15
        
        # 文章の長さと質
        length_score = min(len(sentences) * 2, 30)
        
        return min(structure_score + length_score, 100)
    
    def _markdown_to_text(self, markdown_content: str) -> str:
        """Markdownをプレーンテキストに変換"""
        html = markdown.markdown(markdown_content)
        soup = BeautifulSoup(html, 'html.parser')
        return soup.get_text()
    
    def _split_sentences(self, text: str) -> List[str]:
        """文章を文に分割"""
        sentences = re.split(r'[.!?。！？]+', text)
        return [s.strip() for s in sentences if s.strip()]