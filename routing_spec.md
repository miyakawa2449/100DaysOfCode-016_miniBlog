# ルーティング設計例

## 公開側
- / : ホーム
- /login/ : ログイン
- /totp/ : 2段階認証
- /logon/ : ログイン完了
- /logout/ : ログアウト
- /password_reminder/ : パスワード再発行
- /password_reset/ : パスワードリセット
- /category/<slug>/ : カテゴリーページ
- /article/<slug>/ : 記事ページ
- /article/<slug>/comment/ : コメント投稿（POST）
- /profile/<handle_name>/ : プロフィールページ

## 管理側
- /admin/ : ダッシュボード
- /admin/site/ : サイト管理
- /admin/users/ : ユーザ管理
- /admin/user/edit/<user_id>/ : ユーザ編集
- /admin/articles/ : 記事管理
- /admin/article/edit/<article_id>/ : 記事編集
- /admin/article/preview/<article_id>/ : 記事プレビュー
- /admin/article/upload_image/ : 画像アップロード（POST）
- /admin/categories/ : カテゴリ管理
- /admin/category/edit/<category_id>/ : カテゴリ編集
- /admin/comments/ : コメント管理
- /admin/comments/edit/<comment_id> : コメント編集
- /admin/comments/approve/<comment_id> : コメント承認
- /admin/comments/delete/<comment_id> : コメント削除
- /admin/export/csv/ : CSVエクスポート
- /admin/export/json/ : JSONエクスポート
- /admin/mails/ : メール管理
- /admin/settings/notifications/ : 通知設定

## 初期設定
- /setup/admin/ : 管理者登録
- /setup/site/ : サイト情報登録