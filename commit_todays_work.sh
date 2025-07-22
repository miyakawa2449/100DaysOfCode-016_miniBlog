#!/bin/bash

# 2025年7月9日の作業内容を段階的にコミット

echo "🚀 2025年7月9日の作業内容を段階的にコミットします"

# 第1段階: サイト設定初期化スクリプト
echo "📝 第1段階: サイト設定初期化スクリプト"
git add initialize_site_settings.py
git commit -m "$(cat <<'EOF'
🔧 機能追加: サイト設定初期化スクリプト

サイト設定機能のための初期化スクリプトを追加:
- 15項目の基本設定項目を定義
- 基本情報、外観、機能、SEO、SNS設定を包含
- 既存設定の重複チェック機能
- 自動的なsetting_type推測機能

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"

# 第2段階: app.pyのコンテキストプロセッサとページネーション機能
echo "📝 第2段階: app.pyのコンテキストプロセッサとページネーション機能"
git add app.py
git commit -m "$(cat <<'EOF'
⚡ 機能追加: サイト設定コンテキストプロセッサ & ページネーション

app.pyの機能拡張:
- inject_site_settings()コンテキストプロセッサ追加
- 全テンプレートでサイト設定利用可能
- 公開設定のみ取得する最適化
- 設定タイプ別の適切な値変換(boolean, number, json)

ページネーション機能:
- SQLAlchemy 2.0のdb.paginate()使用
- posts_per_page設定との連携
- /page/<int:page>ルート追加

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"

# 第3段階: admin.pyのサイト設定機能強化
echo "📝 第3段階: admin.pyのサイト設定機能強化"
git add admin.py
git commit -m "$(cat <<'EOF'
🔧 機能強化: サイト設定管理機能の拡張

admin.pyのサイト設定機能強化:
- 30項目以上の設定項目に対応
- 新規設定項目追加(site_name, theme_color, social_github等)
- boolean/number/json型の適切な処理
- 個別SNS設定とJSON設定の自動同期
- エラーハンドリング強化(SQLAlchemyError対応)

設定項目:
- 基本情報: site_name, contact_email, footer_text
- 外観: theme_color, site_logo_url, site_favicon_url  
- 機能: posts_per_page, maintenance_mode
- SNS: social_github追加、自動同期機能

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"

# 第4段階: 管理画面テンプレートの更新
echo "📝 第4段階: 管理画面テンプレートの更新"
git add templates/admin/site_settings.html
git commit -m "$(cat <<'EOF'
🎨 UI改善: サイト設定管理画面のテンプレート更新

templates/admin/site_settings.htmlの改善:
- 新規設定項目のフォームフィールド追加
- site_name, theme_color, footer_textの設定UI
- GitHub SNS設定項目の追加
- Bootstrap 5対応のフォームコンポーネント
- 適切なプレースホルダーとヘルプテキスト

設定項目の構成:
- 基本設定: サイト名、説明、テーマカラー
- SNS設定: GitHub追加でTwitter,Facebook,Instagram,GitHubに対応
- 直感的なUI設計

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"

# 第5段階: レイアウトテンプレートの動的設定対応
echo "📝 第5段階: レイアウトテンプレートの動的設定対応"
git add templates/layout.html
git commit -m "$(cat <<'EOF'
🎨 機能追加: 動的サイト設定対応 & SNSアイコン & テーマカラー

templates/layout.htmlの大幅拡張:

サイト設定の動的反映:
- site_name, site_description, seo_keywordsの動的表示
- favicon, logoの動的設定
- footer_text, contact_emailの動的表示

SNSアイコン機能:
- ナビゲーションにSNSアイコンを追加
- Twitter, Facebook, Instagram, GitHub, YouTubeサポート
- 円形デザインとホバー効果
- target="_blank"で新しいタブで開く

テーマカラー機能:
- CSS変数による動的カラー生成
- 主要UI要素への適用(ボタン、リンク、ページネーション等)
- ホバー効果の統一

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"

# 第6段階: ホームページテンプレートのページネーション
echo "📝 第6段階: ホームページテンプレートのページネーション"
git add templates/home.html
git commit -m "$(cat <<'EOF'
📄 機能追加: ホームページのページネーション機能

templates/home.htmlの機能拡張:
- Bootstrap 5対応のページネーション追加
- 前のページ/次のページボタン
- ページ番号表示とアクティブ状態
- ページ情報表示(○件中○〜○件を表示)
- アクセシビリティ対応(aria-label)

動的設定対応:
- site_name, site_descriptionの動的表示
- サイト設定との完全連携

ページネーション機能:
- pagination.has_prev/has_next判定
- pagination.iter_pages()による効率的なページ番号表示
- レスポンシブデザイン対応

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"

# 第7段階: 設定確認・修正用スクリプト
echo "📝 第7段階: 設定確認・修正用スクリプト"
git add check_posts_per_page.py fix_sns_settings.py sync_sns_settings.py update_sns_settings.py
git commit -m "$(cat <<'EOF'
🔧 ユーティリティ: サイト設定の確認・修正スクリプト

サイト設定機能のサポートスクリプト:
- check_posts_per_page.py: ページネーション設定の確認
- fix_sns_settings.py: SNS設定の公開フラグ修正とJSON同期
- sync_sns_settings.py: 個別設定とJSON設定の同期
- update_sns_settings.py: サンプルSNSリンクの設定

主な機能:
- 設定値の確認とデバッグ
- is_public フラグの修正
- 個別SNS設定とsocial_media_links(JSON)の同期
- データベース整合性の確保

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"

# 第8段階: 作業ドキュメント
echo "📝 第8段階: 作業ドキュメント"
git add reports/2025-07-09_work_completion_report.md reports/2025-07-10_ToDoList.md
git commit -m "$(cat <<'EOF'
📊 ドキュメント: 7月9日作業完了報告 & 7月10日作業計画

作業完了ドキュメント:
- 2025-07-09_work_completion_report.md: 本日の包括的作業報告
- 2025-07-10_ToDoList.md: 明日の詳細作業計画

本日の主要成果:
- サイト設定機能: 100% 完成
- ページネーション機能: 100% 完成
- SNSアイコン機能: 100% 完成
- テーマカラー機能: 100% 完成

プロジェクト進捗: 95% → 97%

明日の作業計画:
- Priority 1: ユーザー管理機能完成
- Priority 2: モダンSEO対策機能(LLMO/AIO)
- Priority 3: Google Analytics統合
- Priority 4: フロントページリニューアル

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"

echo "✅ 全8段階のコミットが完了しました！"
echo "📊 コミット履歴を確認:"
git log --oneline -8