#!/usr/bin/env python3
"""
アクセスログアナライザー
Flaskアプリケーションのアクセスログを分析して統計情報を生成する
"""

import re
import os
import json
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from urllib.parse import unquote
import ipaddress
from user_agents import parse

class AccessLogAnalyzer:
    """アクセスログ分析クラス"""
    
    def __init__(self, log_file_path):
        self.log_file_path = log_file_path
        self.log_pattern = re.compile(
            r'(?P<ip>\d+\.\d+\.\d+\.\d+) - - \[(?P<timestamp>[^\]]+)\] '
            r'"(?P<method>\w+) (?P<path>[^\s]+) (?P<protocol>[^"]+)" '
            r'(?P<status>\d+) (?P<size>\d+|-)'
        )
        self.stats = {
            'total_requests': 0,
            'unique_visitors': set(),
            'popular_pages': Counter(),
            'status_codes': Counter(),
            'methods': Counter(),
            'hourly_traffic': defaultdict(int),
            'daily_traffic': defaultdict(int),
            'user_agents': Counter(),
            'browsers': Counter(),
            'os': Counter(),
            'referers': Counter(),
            'bot_requests': 0,
            'admin_requests': 0,
            'static_requests': 0,
            'api_requests': 0,
            'error_4xx': 0,
            'error_5xx': 0
        }
    
    def parse_log_line(self, line):
        """ログ行を解析"""
        match = self.log_pattern.match(line.strip())
        if not match:
            return None
        
        data = match.groupdict()
        
        # タイムスタンプを datetime に変換
        timestamp_str = data['timestamp']
        try:
            # 例: "22/Jun/2025 16:12:50"
            timestamp = datetime.strptime(timestamp_str.split(' ')[0], '%d/%b/%Y')
            data['datetime'] = timestamp
        except ValueError:
            data['datetime'] = datetime.now()
        
        # パスをデコード
        data['path'] = unquote(data['path'])
        
        # ステータスコードを整数に変換
        data['status'] = int(data['status'])
        
        # サイズを整数に変換（ハイフンの場合は0）
        data['size'] = int(data['size']) if data['size'] != '-' else 0
        
        return data
    
    def is_bot_request(self, user_agent):
        """ボットのリクエストかどうか判定"""
        bot_patterns = [
            'bot', 'crawler', 'spider', 'scraper',
            'Googlebot', 'Bingbot', 'Yahoo', 'facebook',
            'TwitterBot', 'LinkedInBot', 'WhatsApp'
        ]
        user_agent_lower = user_agent.lower()
        return any(pattern.lower() in user_agent_lower for pattern in bot_patterns)
    
    def categorize_request(self, path, method):
        """リクエストのカテゴリを判定"""
        if path.startswith('/admin'):
            return 'admin'
        elif path.startswith('/static'):
            return 'static'
        elif path.startswith('/api'):
            return 'api'
        elif method in ['POST', 'PUT', 'DELETE']:
            return 'form'
        else:
            return 'page'
    
    def analyze_logs(self, max_lines=None):
        """ログファイルを分析"""
        if not os.path.exists(self.log_file_path):
            raise FileNotFoundError(f"Log file not found: {self.log_file_path}")
        
        lines_processed = 0
        
        with open(self.log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if max_lines and lines_processed >= max_lines:
                    break
                
                data = self.parse_log_line(line)
                if not data:
                    continue
                
                self.process_request(data)
                lines_processed += 1
        
        # セットを数に変換
        self.stats['unique_visitors'] = len(self.stats['unique_visitors'])
        
        print(f"📊 {lines_processed} 行のログを分析しました")
        return self.stats
    
    def process_request(self, data):
        """個別リクエストの処理"""
        ip = data['ip']
        path = data['path']
        method = data['method']
        status = data['status']
        user_agent = data.get('user_agent', '')
        timestamp = data['datetime']
        
        # 基本統計
        self.stats['total_requests'] += 1
        self.stats['unique_visitors'].add(ip)
        self.stats['status_codes'][status] += 1
        self.stats['methods'][method] += 1
        
        # 人気ページ（静的ファイルを除く）
        if not path.startswith('/static'):
            self.stats['popular_pages'][path] += 1
        
        # 時間別・日別トラフィック
        hour_key = timestamp.strftime('%H')
        day_key = timestamp.strftime('%Y-%m-%d')
        self.stats['hourly_traffic'][hour_key] += 1
        self.stats['daily_traffic'][day_key] += 1
        
        # User Agent 解析
        if user_agent:
            self.stats['user_agents'][user_agent] += 1
            
            # ボット判定
            if self.is_bot_request(user_agent):
                self.stats['bot_requests'] += 1
            else:
                # ブラウザ・OS解析
                try:
                    parsed_ua = parse(user_agent)
                    self.stats['browsers'][parsed_ua.browser.family] += 1
                    self.stats['os'][parsed_ua.os.family] += 1
                except:
                    pass
        
        # リクエストカテゴリ
        category = self.categorize_request(path, method)
        if category == 'admin':
            self.stats['admin_requests'] += 1
        elif category == 'static':
            self.stats['static_requests'] += 1
        elif category == 'api':
            self.stats['api_requests'] += 1
        
        # エラー統計
        if 400 <= status < 500:
            self.stats['error_4xx'] += 1
        elif status >= 500:
            self.stats['error_5xx'] += 1
    
    def generate_report(self):
        """分析レポートを生成"""
        total = self.stats['total_requests']
        if total == 0:
            return {"error": "分析するデータがありません"}
        
        report = {
            "summary": {
                "total_requests": total,
                "unique_visitors": self.stats['unique_visitors'],
                "bot_requests": self.stats['bot_requests'],
                "admin_requests": self.stats['admin_requests'],
                "static_requests": self.stats['static_requests'],
                "api_requests": self.stats['api_requests'],
                "error_4xx": self.stats['error_4xx'],
                "error_5xx": self.stats['error_5xx'],
                "error_rate": round((self.stats['error_4xx'] + self.stats['error_5xx']) / total * 100, 2)
            },
            "popular_pages": dict(self.stats['popular_pages'].most_common(10)),
            "status_codes": dict(self.stats['status_codes'].most_common()),
            "methods": dict(self.stats['methods'].most_common()),
            "browsers": dict(self.stats['browsers'].most_common(10)),
            "operating_systems": dict(self.stats['os'].most_common(10)),
            "hourly_traffic": dict(sorted(self.stats['hourly_traffic'].items())),
            "daily_traffic": dict(sorted(self.stats['daily_traffic'].items())),
            "top_user_agents": dict(self.stats['user_agents'].most_common(5))
        }
        
        return report
    
    def export_json(self, output_file):
        """JSON形式でレポートをエクスポート"""
        report = self.generate_report()
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"📄 レポートを {output_file} に保存しました")

def main():
    """メイン実行関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='アクセスログアナライザー')
    parser.add_argument('--log-file', default='flask.log', help='ログファイルのパス')
    parser.add_argument('--max-lines', type=int, help='処理する最大行数')
    parser.add_argument('--output', help='JSON出力ファイル名')
    
    args = parser.parse_args()
    
    try:
        analyzer = AccessLogAnalyzer(args.log_file)
        stats = analyzer.analyze_logs(max_lines=args.max_lines)
        report = analyzer.generate_report()
        
        # コンソール出力
        print("\n" + "="*50)
        print("📊 アクセスログ分析レポート")
        print("="*50)
        
        summary = report['summary']
        print(f"📈 総リクエスト数: {summary['total_requests']:,}")
        print(f"👥 ユニークビジター: {summary['unique_visitors']:,}")
        print(f"🤖 ボットリクエスト: {summary['bot_requests']:,}")
        print(f"🔧 管理画面アクセス: {summary['admin_requests']:,}")
        print(f"⚠️  エラー率: {summary['error_rate']}%")
        
        print(f"\n📝 人気ページ TOP 5:")
        for i, (page, count) in enumerate(list(report['popular_pages'].items())[:5], 1):
            print(f"  {i}. {page} ({count:,} アクセス)")
        
        print(f"\n🌐 ブラウザ TOP 3:")
        for i, (browser, count) in enumerate(list(report['browsers'].items())[:3], 1):
            print(f"  {i}. {browser} ({count:,} アクセス)")
        
        # JSON出力
        if args.output:
            analyzer.export_json(args.output)
    
    except FileNotFoundError as e:
        print(f"❌ エラー: {e}")
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")

if __name__ == '__main__':
    main()