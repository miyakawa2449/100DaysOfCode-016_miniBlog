PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE users (
	id INTEGER NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	handle_name VARCHAR(100), 
	password_hash VARCHAR(255) NOT NULL, 
	role VARCHAR(20), 
	created_at DATETIME, 
	totp_secret VARCHAR(255), 
	totp_enabled BOOLEAN, 
	reset_token VARCHAR(255), 
	reset_token_expires DATETIME, 
	notify_on_publish BOOLEAN, 
	notify_on_comment BOOLEAN, 
	introduction TEXT, 
	birthplace VARCHAR(10), 
	birthday DATE, 
	sns_x VARCHAR(100), 
	sns_facebook VARCHAR(100), 
	sns_instagram VARCHAR(100), 
	sns_threads VARCHAR(100), 
	sns_youtube VARCHAR(100), 
	ext_json TEXT, 
	PRIMARY KEY (id), 
	UNIQUE (email)
);
INSERT INTO users VALUES(1,'admin@example.com','管理者','admin','scrypt:32768:8:1$u1LNpuA1FYky10VD$c56415334a045a34b09df8ee081b7928901e930155d8396ff7d314552e03ab6b0e60e8a4c421f88d64650459271c175b51ffd5ced76b4ec430233da6c5a0b709','admin','2025-06-25 12:07:44.142291',NULL,0,NULL,NULL,0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);
CREATE TABLE categories (
	id INTEGER NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	slug VARCHAR(100) NOT NULL, 
	description TEXT, 
	parent_id INTEGER, 
	created_at DATETIME, 
	updated_at DATETIME, 
	meta_title VARCHAR(255), 
	meta_description TEXT, 
	meta_keywords VARCHAR(255), 
	ogp_image VARCHAR(255), 
	canonical_url VARCHAR(255), 
	json_ld TEXT, 
	ext_json TEXT, ogp_image_alt VARCHAR(255), 
	PRIMARY KEY (id), 
	UNIQUE (name), 
	UNIQUE (slug), 
	FOREIGN KEY(parent_id) REFERENCES categories (id)
);
INSERT INTO categories VALUES(1,'テクノロジー','technology','技術に関する記事のカテゴリ',NULL,'2025-06-26 09:59:05.919004','2025-06-26 09:59:05.919005',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO categories VALUES(2,'プログラミング','programming','プログラミングに関する記事',NULL,'2025-06-26 09:59:05.920230','2025-06-26 09:59:05.920231',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO categories VALUES(3,'テスト','test','テスト用カテゴリ',NULL,'2025-06-27 06:22:02.658928','2025-06-27 06:22:02.658933',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);
CREATE TABLE site_settings (
	id INTEGER NOT NULL, 
	"key" VARCHAR(100) NOT NULL, 
	value TEXT, 
	description TEXT, 
	setting_type VARCHAR(20), 
	is_public BOOLEAN, 
	created_at DATETIME, 
	updated_at DATETIME, 
	PRIMARY KEY (id), 
	UNIQUE ("key")
);
CREATE TABLE block_types (
	id INTEGER NOT NULL, 
	type_name VARCHAR(50) NOT NULL, 
	type_label VARCHAR(100) NOT NULL, 
	description TEXT, 
	settings_schema TEXT, 
	template_name VARCHAR(100), 
	is_active BOOLEAN, 
	created_at DATETIME, 
	updated_at DATETIME, 
	PRIMARY KEY (id), 
	UNIQUE (type_name)
);
INSERT INTO block_types VALUES(1,'text','テキストブロック','Markdown形式のテキストブロック',NULL,'blocks/text_block.html',1,'2025-06-26 13:49:22.336982','2025-06-26 13:49:22.336985');
INSERT INTO block_types VALUES(2,'image','画像ブロック','1:1比率の画像ブロック（700px）',NULL,'blocks/image_block.html',1,'2025-06-26 13:49:22.337505','2025-06-26 13:49:22.337505');
INSERT INTO block_types VALUES(3,'featured_image','アイキャッチ画像ブロック','16:9比率のアイキャッチ画像ブロック（800px）',NULL,'blocks/featured_image_block.html',1,'2025-06-26 13:49:22.337749','2025-06-26 13:49:22.337749');
INSERT INTO block_types VALUES(4,'sns_embed','SNS埋込ブロック','Twitter、Facebook、InstagramなどのSNS投稿埋込',NULL,'blocks/sns_embed_block.html',1,'2025-06-26 13:49:22.337964','2025-06-26 13:49:22.337964');
INSERT INTO block_types VALUES(5,'external_article','外部記事埋込ブロック','OGPカード形式の外部記事埋込',NULL,'blocks/external_article_block.html',1,'2025-06-26 13:49:22.338135','2025-06-26 13:49:22.338136');
CREATE TABLE articles (
	id INTEGER NOT NULL, 
	title VARCHAR(255) NOT NULL, 
	slug VARCHAR(255) NOT NULL, 
	summary TEXT, 
	body TEXT, 
	author_id INTEGER NOT NULL, 
	created_at DATETIME, 
	updated_at DATETIME, 
	is_published BOOLEAN, 
	published_at DATETIME, 
	allow_comments BOOLEAN, 
	meta_title VARCHAR(255), 
	meta_description TEXT, 
	meta_keywords VARCHAR(255), 
	canonical_url VARCHAR(255), 
	featured_image VARCHAR(255), 
	use_block_editor BOOLEAN, 
	legacy_body_backup TEXT, 
	ext_json TEXT, featured_image_alt VARCHAR(255), 
	PRIMARY KEY (id), 
	UNIQUE (slug), 
	FOREIGN KEY(author_id) REFERENCES users (id)
);
INSERT INTO articles VALUES(1,'最初のテスト記事','first-test-post','WordPressインポート機能のテスト記事です。',replace('# SNS自動埋込テスト\n\nこの記事では、MarkdownテキストエリアにURLを直接貼り付けるだけでSNSコンテンツが埋込表示される機能をテストします。\n\n## YouTube動画の埋込\n\nYouTube URLを貼り付けると、動画プレーヤーが表示されます：\n\nhttps://youtu.be/DNvGx4nAN2U?si=6VGsRqmU9ylm-Pz_\n\n## Twitter投稿の埋込\n\nTwitter投稿のURLを貼り付けると、ツイートが表示されます：\n\nhttps://twitter.com/jack/status/20\n\n## Instagram投稿の埋込\n\nInstagram投稿のURLを貼り付けると、投稿が表示されます：\n\nhttps://www.instagram.com/p/DKlxE3aRwrC/\n\n## Facebook投稿の埋込\n\nFacebook Watch動画：\n\nhttps://fb.watch/AtN7GyfvaS/\n\n## Threads投稿の埋込\n\nThreads投稿のURLを貼り付けると、カスタムカードが表示されます：\n\nhttps://www.threads.com/@nana_takabatake/post/DLXIm4KzNYT?xmt=AQF0srHCaN3QmpE1vH7yF0X0CdcOwpH2kMv4R_K_yW3UBA\n\n## 通常のテキストとの混在\n\nこのように、通常のMarkdownテキストの中に\n\nhttps://www.youtube.com/watch?v=jNQXAC9IVRw\n\nURLを混在させても正しく埋込表示されます。\n\n**太字**や *斜体* などの書式も問題なく使用できます。\n\n## 完了\n\n以上でテストは完了です！','\n',char(10)),1,'2025-06-26 09:59:36.324517','2025-06-26 09:59:36.324521',1,'2025-06-25 10:00:00.000000',1,NULL,'',NULL,NULL,NULL,0,NULL,NULL,NULL);
INSERT INTO articles VALUES(2,'プログラミング学習のコツ','programming-tips','効果的なプログラミング学習のコツを紹介します。',replace('<h1>効果的なプログラミング学習法</h1>\n\n<p>プログラミングを効果的に学習するためのコツをご紹介します。</p>\n\n<h2>1. 実際にコードを書く</h2>\n<p>理論だけでなく、実際に手を動かしてコードを書くことが重要です。</p>\n\n<pre><code>def hello_world():\n    print("Hello, World!")\n    \nhello_world()\n</code></pre>\n\n<h2>2. 小さなプロジェクトから始める</h2>\n<p>最初は簡単なプロジェクトから始めて、徐々に複雑なものに挑戦しましょう。</p>\n\n<h2>3. エラーを恐れない</h2>\n<p>エラーは学習の一部です。エラーメッセージを読んで理解することで成長できます。</p>\n\n<p><strong>継続が最も重要です。</strong>毎日少しずつでも続けることで、確実にスキルが向上します。</p>','\n',char(10)),1,'2025-06-26 09:59:36.327188','2025-06-26 09:59:36.327189',1,'2025-06-25 14:30:00.000000',1,NULL,'',NULL,NULL,NULL,0,NULL,NULL,NULL);
INSERT INTO articles VALUES(3,'ブロックエディタ-SNS埋込','xcom','SNS埋め込みテスト',NULL,1,'2025-06-26 13:42:46.145781','2025-06-27 02:00:30.457093',1,'2025-06-26 14:06:18.456161',0,'','','','',NULL,1,NULL,NULL,NULL);
INSERT INTO articles VALUES(4,'テスト','snstest','Threadsテスト','<p># Threads</p><p>https://www.threads.com/@hideo_kojima/post/DLU3lBqyOgY?xmt=AQF0A4stYAtCLKDI_OwEP5IL_5WPnkVfVy_-3hKFpr9vcQ</p>',1,'2025-06-27 05:44:01.663499','2025-06-30 02:36:57.708984',1,'2025-06-27 05:44:01.663577',1,'','','',NULL,NULL,0,NULL,NULL,NULL);
INSERT INTO articles VALUES(5,'testsnstestsns','testsnstestsns','',NULL,1,'2025-06-27 05:44:45.138483','2025-06-27 06:15:45.952869',1,'2025-06-27 05:46:41.889387',0,'','','','',NULL,1,NULL,NULL,NULL);
INSERT INTO articles VALUES(6,'再びSNSテスト','h','SNSテスト','<p><span style="color: rgb(0, 0, 0);">https://x.com/miyakawa2449/status/1938166417775567042</span></p>',1,'2025-06-27 06:16:34.000527','2025-06-30 02:35:55.340245',1,'2025-06-27 06:16:34.000590',1,'','','',NULL,NULL,0,NULL,NULL,NULL);
INSERT INTO articles VALUES(7,'SNS自動埋込機能テスト','sns-auto-embed-test','SNS URLの自動埋込機能をテストするための記事です。YouTube、Twitter、Instagram、Facebook、Threadsの各URLが正しく埋込表示されることを確認できます。',replace(replace('# SNS自動埋込機能のテスト記事\r\n\r\nこの記事では、Markdownテキストエリアに直接SNS URLを貼り付けて自動埋込される機能をテストします。\r\n\r\n## YouTube動画の埋込\r\n\r\nhttps://youtu.be/DNvGx4nAN2U\r\n\r\n上記のURLが動画プレーヤーとして表示されるはずです。\r\n\r\n## Twitter投稿の埋込\r\n\r\nhttps://twitter.com/jack/status/20\n\nX.comの新しいURL形式もテストします：\n\nhttps://x.com/jack/status/20\r\n\r\nTwitterの投稿が埋込表示されます。\r\n\r\n## Instagram投稿の埋込\r\n\r\nhttps://www.instagram.com/p/DKlxE3aRwrC/\r\n\r\nInstagram投稿が埋込表示されます。\r\n\r\n## Facebook動画の埋込\r\n\r\nhttps://fb.watch/AtN7GyfvaS/\r\n\r\nFacebook Watch動画が埋込表示されます。\r\n\r\n## Threads投稿の埋込\r\n\r\nhttps://www.threads.net/@zuck/post/C8FjcQBqm_k\r\n\r\nThreadsの投稿がカスタムカード形式で表示されます。\r\n\r\n## 通常のMarkdown書式との併用\r\n\r\n**太字**や*斜体*、[リンク](https://example.com)なども正常に動作します。\r\n\r\n- リスト項目1\r\n- リスト項目2  \r\n- リスト項目3\r\n\r\nコードブロックも正常です：\r\n\r\n```python\r\ndef hello():\r\n    print("Hello, World!")\r\n```\r\n\r\nこの記事で、SNS URLが正しく埋込表示に変換されることを確認してください。\n\n## X.com URL正規化テスト\n\n従来のTwitter URL:\nhttps://twitter.com/elonmusk/status/1\n\n新しいX.com URL:\nhttps://x.com/elonmusk/status/1\n\n両方とも同じ埋込形式で表示されるはずです。\n\n\n## Threads OGPカード表示テスト\n\n実際のThreads投稿でOGPデータを取得してカード表示をテストします：\n\nhttps://www.threads.net/@zuck/post/C8PZPXXpFdn\n\n上記のURLで投稿内容、画像、ユーザー名などが表示されるはずです。\n\n\n## 実際のThreads OGPテスト\n\nmiyakawa2449さんの実際の投稿で詳細情報の取得をテストします：\n\nhttps://www.threads.com/@miyakawa2449/post/DLUVx_svglN\n\n上記のURLで投稿内容、画像、詳細な説明が表示されるはずです。\n','\r',char(13)),'\n',char(10)),1,'2025-06-27 06:22:02.659406','2025-06-27 07:14:54.525404',1,'2025-06-27 06:24:53.033299',1,'','','',NULL,NULL,0,NULL,NULL,NULL);
INSERT INTO articles VALUES(8,'手動SNS埋込','s','MarkdownでSNS URLを入れた時の表示テストをしています。',replace(replace('# x.com\r\n\r\nhttps://x.com/MH_Wilds/status/1938375367733219604\r\n\r\nhttps://www.threads.com/@miyakawa2449/post/DLUVx_svglN\r\n\r\n\r\nhttps://www.instagram.com/p/DLYgyzAz7SG/','\r',char(13)),'\n',char(10)),1,'2025-06-27 06:40:33.425824','2025-06-30 02:38:23.475499',1,'2025-06-27 06:40:33.425924',0,'','','',NULL,'uploads/articles/featured_cropped_8_1751251103.jpg',0,NULL,NULL,NULL);
INSERT INTO articles VALUES(9,'テスト記事、画像、アイキャッチ、SEO','t','',replace(replace('![画像の説明](![画像の説明]())# 綾波レイ\r\n`<a>`\r\n今日はいい天気です。\r\n今日はいい天気です。\r\n\r\n今日はいい天気です。今日はいい天気です。今日はいい天気です。\r\n今日はいい天気です。\r\n\r\n今日はいい天気です。今日はいい天気です。\r\n**太文字**\r\n*斜体*\r\n# 見出し１\r\n## 見出し２\r\n### 見出し３\r\n\r\n- リスト\r\n- リスト\r\n- リスト\r\n\r\n1. リスト１\r\n2. リスト２\r\n\r\n[Googleへ](https://www.google.com)\r\n\r\n\r\n```\r\npython main.py\r\n```\r\n![綾波レイ](static/uploads/articles/featured_cropped_9_1751250878.jpg)\r\n\r\n今日はいい天気です。\r\n今日はいい天気です。\r\n\r\n今日はいい天気です。今日はいい天気です。\r\n\r\n1. テスト\r\n2. テスト','\r',char(13)),'\n',char(10)),1,'2025-06-30 01:23:59.859245','2025-06-30 05:08:34.707644',1,'2025-06-30 01:23:59.859321',1,'SEOメタタイトル','SEOメタディスクリプション','メタキーワード,キーワード2',NULL,'uploads/articles/featured_cropped_9_1751250878.jpg',0,NULL,NULL,NULL);
INSERT INTO articles VALUES(10,'マークダウンテスト記事','markdown-test',NULL,replace('# マークダウンテスト\n\n## 番号付きリストテスト\n\n基本的な番号付きリスト：\n1. 最初の項目\n2. 二番目の項目\n3. 三番目の項目\n\n段落の後の番号付きリスト：\n\n1. 新しい最初の項目\n2. 新しい二番目の項目\n\n## HTMLタグテスト\n\nこれは<a href="https://example.com">リンク</a>です。\n\n複数のリスト：\nタスクリスト：\n1. タスク1\n2. タスク2\n\n別のリスト：\n1. アイテム1\n2. アイテム2\n','\n',char(10)),1,'2025-06-30 01:54:53.608629','2025-06-30 01:54:53.608632',1,NULL,1,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL);
INSERT INTO articles VALUES(11,'画像アップロードテスト','imageuppload','',replace(replace('# ミラーレスカメラで殺絵したスイーツ\r\nあこがれのスイーツ特集\r\n\r\n![ケーキ](/static/uploads/content/content_1_1751263989.jpg "おいしいケーキ屋さんのスイーツ")\r\n','\r',char(13)),'\n',char(10)),1,'2025-06-30 05:39:41.873849','2025-06-30 06:13:57.674357',1,'2025-06-30 05:39:41.873922',0,'','','',NULL,'uploads/articles/featured_cropped_11_1751262150.jpg',0,NULL,NULL,NULL);
INSERT INTO articles VALUES(12,'タイトルでーーす','titoledesu','',replace(replace('### ケーキです\r\n\r\n\r\n![ケーキ](/static/uploads/content/content_1_1751265538.jpg "ケーキの説明文を入れることができます。")','\r',char(13)),'\n',char(10)),1,'2025-06-30 06:40:25.990319','2025-06-30 06:40:25.991955',1,'2025-06-30 06:40:25.990420',0,'SEOタイトル','メタディスクリプションです','メタキーワード1. メタキーワード2',NULL,NULL,0,NULL,NULL,NULL);
INSERT INTO articles VALUES(13,'新規作成アイキャッチ保存','aichathc','',replace(replace('![大仏](/static/uploads/content/content_1_1751525915.jpg "大仏さんでーす")![スイーツ](/static/uploads/content/content_1_1751494910.jpg "パウンドケーキです")スイーツでーす\r\n\r\nhttps://x.com/fladdict/status/1940355624614916287\r\n\r\nhttps://www.instagram.com/p/DLitpRIzL-C/?utm_source=ig_web_copy_link','\r',char(13)),'\n',char(10)),1,'2025-06-30 06:54:13.348471','2025-07-03 06:58:50.427221',1,'2025-06-30 06:54:13.348522',0,'','','','','uploads/articles/featured_cropped_13_1751525839.jpg',0,NULL,NULL,NULL);
INSERT INTO articles VALUES(14,'MySQL移行とSQLAlchemy 2.0リファクタリングを成功裏','mysql_sqlalchemy20','Phase 1 完了**: MySQL移行とSQLAlchemy 2.0リファクタリングを成功裏に実施。データベースインフラの近代化とコード品質の大幅改善を達成。',replace(replace('# 開発レポート - 2025年7月1日\r\n\r\n## 概要\r\n**Phase 1 完了**: MySQL移行とSQLAlchemy 2.0リファクタリングを成功裏に実施。データベースインフラの近代化とコード品質の大幅改善を達成。\r\n\r\n## 🎯 Phase 1 完了項目\r\n\r\n### ✅ **MySQL環境構築・移行**\r\n1. **環境セットアップ**\r\n   - MySQL 9.3.0をローカル環境にインストール・設定完了\r\n   - データベース`miniblog`作成・稼働確認\r\n   - PyMySQLドライバーのインストール・設定完了\r\n\r\n2. **完全データ移行**\r\n   - SQLiteからMySQLへの完全移行達成\r\n   - **移行データ詳細**:\r\n     - ユーザー: 1名（管理者）\r\n     - 記事: 13件\r\n     - カテゴリ: 3件\r\n     - アップロード画像: 6件\r\n     - すべてのリレーションシップを保持\r\n\r\n3. **データ整合性確認**\r\n   - 外部キー制約の完全保持\r\n   - データ欠損なしでの移行完了\r\n   - 全機能の動作確認済み\r\n\r\n### ✅ **SQLAlchemy 2.0対応完了**\r\n1. **非推奨パターンの全面刷新**\r\n   - **更新箇所**: 21か所の非推奨パターンを修正\r\n     - `.query.get()` → `db.session.get()`: 12箇所\r\n     - `session.query()` → `session.execute(select())`: 9箇所\r\n   - **対象ファイル**: `app.py`, `admin.py`\r\n   - **インポート追加**: `select` from sqlalchemy\r\n\r\n2. **警告の完全解消**\r\n   - LegacyAPIWarningの全面解消\r\n   - 非推奨メソッド使用の完全排除\r\n   - 将来性のあるコードパターンへの移行完了\r\n\r\n3. **機能継続性の確保**\r\n   - 既存機能への影響なしで移行完了\r\n   - 後方互換性の維持\r\n   - ユーザー体験の継続性確保\r\n\r\n## 🔧 技術的成果\r\n\r\n### **データベースインフラ改善**\r\n- **パフォーマンス**: SQLiteからMySQLによる高速化実現\r\n- **スケーラビリティ**: AWS RDS対応準備完了\r\n- **安定性**: プロダクション級データベースバックエンド確立\r\n- **保守性**: 標準的なRDBMS環境での運用体制構築\r\n\r\n### **コード品質向上**\r\n- **将来性**: SQLAlchemy 2.0/3.0対応による長期サポート確保\r\n- **型安全性**: モダンなAPIパターンによる開発効率向上\r\n- **保守性**: 標準的なクエリパターンによる可読性向上\r\n- **技術負債**: 非推奨APIの完全排除\r\n\r\n### **開発環境最適化**\r\n- **クリーンログ**: 警告メッセージの完全解消\r\n- **IDE支援**: 型チェック・補完機能の最適化\r\n- **デバッグ**: エラー追跡の効率化\r\n\r\n## 📊 移行統計\r\n\r\n### **データベース状況**\r\n- **接続状態**: ✅ MySQL稼働中\r\n- **データ整合性**: ✅ 100%保持\r\n- **パフォーマンス**: ✅ 最適化済み\r\n- **AWS準備**: ✅ RDS対応完了\r\n\r\n### **コード品質**\r\n- **SQLAlchemy準拠**: ✅ 2.0完全対応\r\n- **非推奨警告**: ✅ 0件（完全解消）\r\n- **型安全性**: ✅ 向上\r\n- **将来性**: ✅ 長期サポート確保\r\n\r\n### **機能動作確認**\r\n- **記事作成・編集**: ✅ 正常動作\r\n- **画像アップロード**: ✅ 正常動作\r\n- **コメント機能**: ✅ 正常動作\r\n- **SEO・OGP**: ✅ 正常動作\r\n- **ユーザー管理**: ✅ 正常動作\r\n\r\n## 🚀 AWS デプロイ準備状況\r\n\r\n### **完了項目**\r\n- **データベース**: MySQL対応によりRDS即座対応可能\r\n- **コードベース**: モダンなパターンで本番環境対応済み\r\n- **スケーラビリティ**: 高負荷対応アーキテクチャ確立\r\n- **セキュリティ**: プロダクション級データベース設定\r\n\r\n### **準備完了要素**\r\n- **環境変数**: DATABASE_URL設定によるクラウド対応\r\n- **接続ドライバ**: PyMySQL使用でAWS RDS対応\r\n- **マイグレーション**: Alembicによる本番環境スキーマ管理\r\n- **モニタリング**: SQLAlchemy 2.0による効率的ログ出力\r\n\r\n## 🎯 次回作業計画（Phase 2）\r\n\r\n### **AWS デプロイ実装**\r\n1. **RDS設定**: Amazon RDS for MySQL環境構築\r\n2. **環境分離**: 開発・ステージング・本番環境の設定\r\n3. **セキュリティ**: VPC・セキュリティグループ設定\r\n4. **CI/CD**: 自動デプロイパイプライン構築\r\n\r\n### **残存機能テスト**\r\n1. **包括テスト**: 安定したMySQL環境での全機能検証\r\n2. **パフォーマンステスト**: 本番同等環境での負荷テスト\r\n3. **セキュリティテスト**: 脆弱性スキャン・ペネトレーションテスト\r\n4. **ユーザビリティテスト**: エンドツーエンドのユーザー体験検証\r\n\r\n### **運用準備**\r\n1. **監視設定**: CloudWatchによるアプリケーション監視\r\n2. **バックアップ**: 自動バックアップ戦略実装\r\n3. **ログ管理**: 集約ログ分析システム構築\r\n4. **災害復旧**: DR（Disaster Recovery）計画策定\r\n\r\n## 📈 プロジェクト進捗\r\n\r\n### **完了フェーズ**\r\n- ✅ **機能開発**: 記事作成・編集・表示・コメント・SEO機能完成\r\n- ✅ **UI/UX改善**: レスポンシブ・アクセシビリティ対応完了\r\n- ✅ **インフラ近代化**: MySQL移行・SQLAlchemy 2.0対応完了\r\n\r\n### **現在フェーズ**\r\n- 🚀 **AWS デプロイ準備**: 本番環境構築準備中\r\n\r\n### **次期フェーズ**\r\n- 📋 **運用開始**: プロダクション環境での本格運用\r\n\r\n## 開発者メモ\r\n\r\n### **技術的判断の評価**\r\n- **MySQL移行タイミング**: ✅ 最適（データ量最小・機能安定期）\r\n- **SQLAlchemy 2.0対応**: ✅ 先行対応により技術負債回避成功\r\n- **一括リファクタリング**: ✅ 効率的アプローチで品質大幅向上\r\n\r\n### **学習成果**\r\n- MySQL環境構築・運用ノウハウ獲得\r\n- SQLAlchemy 2.0パターンの完全習得\r\n- 大規模データ移行の安全な実施方法習得\r\n- プロダクション準備の体系的アプローチ習得\r\n\r\n---\r\n\r\n**Phase 1 総合評価**: 計画した全目標を100%達成。データベースインフラの近代化とコード品質の大幅向上を実現し、AWS本番環境への準備が完全に整った。技術的負債を完全に解消し、スケーラブルで保守性の高いアーキテクチャを確立。\r\n\r\n**プロジェクト状況**: 開発段階から本番準備段階への移行完了。高品質なプロダクションレディシステムとして確立。\r\n','\r',char(13)),'\n',char(10)),1,'2025-07-01 02:18:07.157795','2025-07-02 11:29:35.001185',1,'2025-07-01 02:18:07.157891',0,'','','','','uploads/articles/featured_cropped_14_1751336538.jpg',0,NULL,NULL,NULL);
INSERT INTO articles VALUES(15,'SNS','xfacebookinstagram','SNS表示テスト',replace(replace('## YouTube動画の埋込\r\n\r\nhttps://youtu.be/DNvGx4nAN2U\r\n\r\nhttps://twitter.com/jack/status/20\r\n\r\nhttps://x.com/jack/status/20\r\n\r\nhttps://www.instagram.com/p/DKlxE3aRwrC/','\r',char(13)),'\n',char(10)),1,'2025-07-01 02:25:41.057457','2025-07-01 02:25:41.058189',1,'2025-07-01 02:25:41.057520',0,'','','',NULL,NULL,0,NULL,NULL,NULL);
INSERT INTO articles VALUES(16,'アイキャッチ画像、本文画像テスト','ichatch-image','テスト中です',replace(replace('# 寺院写真\r\n\r\n![DSC07350](/static/uploads/content/content_1_1751526467.jpg)\r\n\r\n![DSC03960](/static/uploads/content/content_1_1751526310.jpg "大仏さまです")','\r',char(13)),'\n',char(10)),1,'2025-07-03 07:05:57.533295','2025-07-03 07:08:27.079483',1,'2025-07-03 07:06:15.310073',0,'','','','','uploads/articles/featured_cropped_16_1751526357.jpg',0,NULL,NULL,NULL);
INSERT INTO articles VALUES(17,'Markdown Test 2','markdwontest2','',replace(replace('# マークダウンテスト\r\n\r\n## 番号付きリストテスト\r\n\r\n基本的な番号付きリスト：\r\n1. 最初の項目\r\n2. 二番目の項目\r\n3. 三番目の項目\r\n\r\n段落の後の番号付きリスト：\r\n\r\n1. 新しい最初の項目\r\n2. 新しい二番目の項目\r\n\r\n## HTMLタグテスト\r\n\r\nこれは<a href="https://example.com">リンク</a>です。\r\n\r\n複数のリスト：\r\nタスクリスト：\r\n1. タスク1\r\n2. タスク2\r\n\r\n別のリスト：\r\n1. アイテム1\r\n2. アイテム2\r\n\r\n![DSCF0608](/static/uploads/content/content_1_1751619515.jpg "彼岸花")\r\n\r\nhttps://x.com/thegitsofficial/status/1940954985866604743','\r',char(13)),'\n',char(10)),1,'2025-07-04 08:56:58.878476','2025-07-04 09:13:31.690979',1,'2025-07-04 08:56:58.876882',0,'','','','','uploads/articles/featured_cropped_17_1751620411.jpg',0,NULL,NULL,NULL);
CREATE TABLE article_categories (
	article_id INTEGER NOT NULL, 
	category_id INTEGER NOT NULL, 
	PRIMARY KEY (article_id, category_id), 
	FOREIGN KEY(article_id) REFERENCES articles (id), 
	FOREIGN KEY(category_id) REFERENCES categories (id)
);
INSERT INTO article_categories VALUES(1,1);
INSERT INTO article_categories VALUES(2,2);
INSERT INTO article_categories VALUES(2,1);
INSERT INTO article_categories VALUES(7,3);
INSERT INTO article_categories VALUES(8,3);
INSERT INTO article_categories VALUES(9,3);
INSERT INTO article_categories VALUES(14,2);
CREATE TABLE comments (
	id INTEGER NOT NULL, 
	article_id INTEGER NOT NULL, 
	author_name VARCHAR(100) NOT NULL, 
	author_email VARCHAR(255) NOT NULL, 
	author_website VARCHAR(255), 
	content TEXT NOT NULL, 
	is_approved BOOLEAN, 
	ip_address VARCHAR(45), 
	user_agent VARCHAR(500), 
	parent_id INTEGER, 
	created_at DATETIME, 
	updated_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(article_id) REFERENCES articles (id), 
	FOREIGN KEY(parent_id) REFERENCES comments (id)
);
INSERT INTO comments VALUES(1,10,'テストさん','t.miyakawa244@gmail.com','https://miyakawai.com','便利ですね。すごいですね、',0,'127.0.0.1','Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',NULL,'2025-06-30 03:03:05.368951','2025-06-30 03:03:05.368954');
CREATE TABLE article_blocks (
	id INTEGER NOT NULL, 
	article_id INTEGER NOT NULL, 
	block_type_id INTEGER NOT NULL, 
	sort_order INTEGER NOT NULL, 
	title VARCHAR(255), 
	content TEXT, 
	image_path VARCHAR(500), 
	image_alt_text VARCHAR(255), 
	image_caption TEXT, 
	crop_data TEXT, 
	embed_url VARCHAR(1000), 
	embed_platform VARCHAR(50), 
	embed_id VARCHAR(200), 
	embed_html TEXT, 
	ogp_title VARCHAR(500), 
	ogp_description TEXT, 
	ogp_image VARCHAR(500), 
	ogp_site_name VARCHAR(200), 
	ogp_url VARCHAR(1000), 
	ogp_cached_at DATETIME, 
	settings TEXT, 
	css_classes VARCHAR(500), 
	is_visible BOOLEAN, 
	created_at DATETIME, 
	updated_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(article_id) REFERENCES articles (id) ON DELETE CASCADE, 
	FOREIGN KEY(block_type_id) REFERENCES block_types (id)
);
INSERT INTO article_blocks VALUES(1,3,4,1,'x.com',NULL,NULL,NULL,NULL,NULL,'https://x.com/miyakawa2449/status/1938166417775567042','twitter','1938166417775567042',replace('\n            <blockquote class="twitter-tweet">\n                <a href="https://x.com/miyakawa2449/status/1938166417775567042"></a>\n            </blockquote>\n            <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>\n            ','\n',char(10)),'miyakawa2449さんのポスト','X (旧Twitter) でこの投稿を見る',NULL,'X (旧Twitter)','https://x.com/miyakawa2449/status/1938166417775567042',NULL,'{"display_mode": "ogp_card"}','',1,'2025-06-26 13:50:26.928764','2025-06-27 02:26:29.386588');
INSERT INTO article_blocks VALUES(2,3,4,2,'x.com ogp',NULL,NULL,NULL,NULL,NULL,'https://x.com/miyakawa2449/status/1938166417775567042','twitter','1938166417775567042',replace('\n            <blockquote class="twitter-tweet">\n                <a href="https://x.com/miyakawa2449/status/1938166417775567042"></a>\n            </blockquote>\n            <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>\n            ','\n',char(10)),'miyakawa2449さんのポスト','X (旧Twitter) でこの投稿を見る','','X (旧Twitter)','https://x.com/miyakawa2449/status/1938166417775567042','2025-06-27 02:00:22.585498','{"display_mode": "ogp_card"}','',1,'2025-06-26 14:04:53.772050','2025-06-27 02:00:22.585557');
INSERT INTO article_blocks VALUES(3,3,2,3,'画像',NULL,'uploads/blocks/block_image_3_1750946874.png','ターミナル','ターミナルのスクショです',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'',1,'2025-06-26 14:07:08.502731','2025-06-26 14:07:54.432727');
INSERT INTO article_blocks VALUES(4,3,4,4,'YouTube',NULL,NULL,NULL,NULL,NULL,'https://youtu.be/__lLkYY34NA?si=q-VC8AMmLcRKMJ0l','youtube','__lLkYY34NA',replace('\n            <div class="youtube-embed">\n                <iframe width="560" height="315" \n                        src="https://www.youtube.com/embed/__lLkYY34NA" \n                        title="YouTube video player" \n                        frameborder="0" \n                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" \n                        allowfullscreen>\n                </iframe>\n            </div>\n            ','\n',char(10)),'『DEATH STRANDING 2: ON THE BEACH』 - ファイナル・トレーラー','PlayStation®5用ソフトウェア『DEATH STRANDING 2: ON THE BEACH』発売中。詳細は公式サイトをご確認ください。https://www.playstation.com/ja-jp/games/death-stranding-2-on-the-beach/#DeathStrand...','https://i.ytimg.com/vi/__lLkYY34NA/maxresdefault.jpg','YouTube','https://youtu.be/__lLkYY34NA?si=q-VC8AMmLcRKMJ0l',NULL,'{"display_mode": "ogp_card"}','',1,'2025-06-27 01:55:21.690423','2025-06-27 02:26:29.386591');
INSERT INTO article_blocks VALUES(5,3,4,5,'x.com',NULL,NULL,NULL,NULL,NULL,'https://x.com/F1Movie_jp/status/1938401897603596310','twitter','1938401897603596310',replace('\n            <blockquote class="twitter-tweet">\n                <a href="https://x.com/F1Movie_jp/status/1938401897603596310"></a>\n            </blockquote>\n            <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>\n            ','\n',char(10)),'F1Movie_jpさんのポスト','X (旧Twitter) でこの投稿を見る',NULL,'X (旧Twitter)','https://x.com/F1Movie_jp/status/1938401897603596310',NULL,'{"display_mode": "ogp_card"}','',1,'2025-06-27 01:56:37.100242','2025-06-27 02:26:29.386592');
INSERT INTO article_blocks VALUES(6,3,4,6,'Instagram',NULL,NULL,NULL,NULL,NULL,'https://www.instagram.com/p/DLYgyzAz7SG/?utm_source=ig_web_copy_link','instagram','DLYgyzAz7SG',replace('\n            <blockquote class="instagram-media" data-instgrm-permalink="https://www.instagram.com/p/DLYgyzAz7SG/?utm_source=ig_web_copy_link">\n                <a href="https://www.instagram.com/p/DLYgyzAz7SG/?utm_source=ig_web_copy_link"></a>\n            </blockquote>\n            <script async src="//www.instagram.com/embed.js"></script>\n            ','\n',char(10)),'Instagram',NULL,NULL,'Instagram','https://www.instagram.com/p/DLYgyzAz7SG/?utm_source=ig_web_copy_link',NULL,'{"display_mode": "ogp_card"}','',1,'2025-06-27 01:57:31.654388','2025-06-27 02:26:29.386593');
INSERT INTO article_blocks VALUES(7,3,4,7,'Facebooke',NULL,NULL,NULL,NULL,NULL,'https://fb.watch/AtJ6-H7uor/','facebook',NULL,NULL,'Facebook投稿','Facebookでこの投稿を見る',NULL,'Facebook','https://fb.watch/AtJ6-H7uor/',NULL,'{"display_mode": "ogp_card"}','',1,'2025-06-27 01:58:56.996751','2025-06-27 02:26:29.386593');
INSERT INTO article_blocks VALUES(8,3,4,8,'Threads',NULL,NULL,NULL,NULL,NULL,'https://www.threads.com/@hideo_kojima/post/DLYTl87zVO4?xmt=AQF0HleuJozBG1Y1Gsy4-EVZi4KQsfBdYPpZ5Swfx5XA3w','threads','DLYTl87zVO4?xmt=AQF0HleuJozBG1Y1Gsy4-EVZi4KQsfBdYPpZ5Swfx5XA3w',replace('\n            <div class="threads-embed">\n                <a href="https://www.threads.com/@hideo_kojima/post/DLYTl87zVO4?xmt=AQF0HleuJozBG1Y1Gsy4-EVZi4KQsfBdYPpZ5Swfx5XA3w" target="_blank" rel="noopener">\n                    Threadsで見る\n                </a>\n            </div>\n            ','\n',char(10)),'Threads',NULL,NULL,'Threads','https://www.threads.com/@hideo_kojima/post/DLYTl87zVO4?xmt=AQF0HleuJozBG1Y1Gsy4-EVZi4KQsfBdYPpZ5Swfx5XA3w',NULL,'{"display_mode": "ogp_card"}','',1,'2025-06-27 01:59:28.601414','2025-06-27 02:26:29.386594');
INSERT INTO article_blocks VALUES(9,5,1,1,'新しいテキストブロック','https://x.com/miyakawa2449/status/1938166417775567042',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'',1,'2025-06-27 06:15:24.473504','2025-06-27 06:15:39.664338');
CREATE TABLE alembic_version (
	version_num VARCHAR(32) NOT NULL, 
	CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);
INSERT INTO alembic_version VALUES('9c67d0116b9c');
CREATE TABLE uploaded_images (
	id INTEGER NOT NULL, 
	filename VARCHAR(255) NOT NULL, 
	original_filename VARCHAR(255) NOT NULL, 
	file_path VARCHAR(500) NOT NULL, 
	file_size INTEGER NOT NULL, 
	mime_type VARCHAR(100) NOT NULL, 
	width INTEGER, 
	height INTEGER, 
	alt_text VARCHAR(255), 
	caption TEXT, 
	description TEXT, 
	uploader_id INTEGER NOT NULL, 
	upload_date DATETIME, 
	is_active BOOLEAN, 
	usage_count INTEGER, 
	last_used_at DATETIME, 
	created_at DATETIME, 
	updated_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(uploader_id) REFERENCES users (id)
);
INSERT INTO uploaded_images VALUES(1,'content_1_1751261902.jpeg','DSC01078.jpeg','uploads/content/content_1_1751261902.jpeg',293984,'image/jpeg',1500,1125,'スイーツ','テーブルセットされたスイーツ写真です','スイーツ',1,'2025-06-30 05:38:22.566972',1,0,NULL,'2025-06-30 05:38:22.566978','2025-06-30 05:38:22.566978');
INSERT INTO uploaded_images VALUES(2,'content_1_1751263799.jpeg','DSCF1473.jpeg','uploads/content/content_1_1751263799.jpeg',286510,'image/jpeg',2000,2000,'ショートケーキ','おいしいケーキ屋さんのショートケーキ','ケーキ',1,'2025-06-30 06:09:59.728840',1,0,NULL,'2025-06-30 06:09:59.728844','2025-06-30 06:09:59.728844');
INSERT INTO uploaded_images VALUES(3,'content_1_1751263989.jpg','cropped_image.jpg','uploads/content/content_1_1751263989.jpg',54578,'image/jpeg',800,600,'ケーキ','おいしいケーキ屋さんのスイーツ','ケーキ',1,'2025-06-30 06:13:09.214841',1,0,NULL,'2025-06-30 06:13:09.214847','2025-06-30 06:13:09.214847');
INSERT INTO uploaded_images VALUES(4,'content_1_1751265538.jpg','cropped_image.jpg','uploads/content/content_1_1751265538.jpg',57631,'image/jpeg',800,600,'ケーキ','ケーキの説明文を入れることができます。','ケーキ',1,'2025-06-30 06:38:58.721842',1,0,NULL,'2025-06-30 06:38:58.721850','2025-06-30 06:38:58.721850');
INSERT INTO uploaded_images VALUES(5,'content_1_1751266436.jpg','cropped_image.jpg','uploads/content/content_1_1751266436.jpg',48378,'image/jpeg',800,600,'バームクーヘン','バームクーヘンのテーブルセッティング','バームクーヘン',1,'2025-06-30 06:53:56.487014',1,0,NULL,'2025-06-30 06:53:56.487018','2025-06-30 06:53:56.487019');
INSERT INTO uploaded_images VALUES(6,'content_1_1751282267.jpg','cropped_image.jpg','uploads/content/content_1_1751282267.jpg',75871,'image/jpeg',800,600,'さくらんぼ','さくらんぼとガラスの器','果物,さくらんぼ',1,'2025-06-30 11:17:47.547242',1,0,NULL,'2025-06-30 11:17:47.547248','2025-06-30 11:17:47.547249');
INSERT INTO uploaded_images VALUES(7,'content_1_1751494910.jpg','cropped_image.jpg','uploads/content/content_1_1751494910.jpg',70561,'image/jpeg',800,600,'スイーツ','パウンドケーキです','スイーツ',1,'2025-07-02 22:21:50.613557',1,0,NULL,'2025-07-02 22:21:50.613563','2025-07-02 22:21:50.613564');
INSERT INTO uploaded_images VALUES(8,'content_1_1751525915.jpg','cropped_image.jpg','uploads/content/content_1_1751525915.jpg',71529,'image/jpeg',800,600,'大仏','大仏さんでーす','大仏',1,'2025-07-03 06:58:35.564934',1,0,NULL,'2025-07-03 06:58:35.564941','2025-07-03 06:58:35.564942');
INSERT INTO uploaded_images VALUES(9,'content_1_1751526310.jpg','cropped_image.jpg','uploads/content/content_1_1751526310.jpg',106861,'image/jpeg',800,600,'DSC03960','大仏さまです','大仏',1,'2025-07-03 07:05:10.317466',1,0,NULL,'2025-07-03 07:05:10.317472','2025-07-03 07:05:10.317473');
INSERT INTO uploaded_images VALUES(10,'content_1_1751526467.jpg','cropped_image.jpg','uploads/content/content_1_1751526467.jpg',96572,'image/jpeg',800,600,'DSC07350','','',1,'2025-07-03 07:07:47.213525',1,0,NULL,'2025-07-03 07:07:47.213531','2025-07-03 07:07:47.213532');
INSERT INTO uploaded_images VALUES(11,'content_1_1751619515.jpg','cropped_image.jpg','uploads/content/content_1_1751619515.jpg',79364,'image/jpeg',800,600,'DSCF0608','彼岸花','',1,'2025-07-04 08:58:35.741796',1,0,NULL,'2025-07-04 08:58:35.741801','2025-07-04 08:58:35.741801');
COMMIT;
