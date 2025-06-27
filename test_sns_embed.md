# SNS自動埋込テスト

この記事では、MarkdownテキストエリアにURLを直接貼り付けるだけでSNSコンテンツが埋込表示される機能をテストします。

## YouTube動画の埋込

以下のYouTube URLを貼り付けると、動画プレーヤーが表示されます：

https://www.youtube.com/watch?v=dQw4w9WgXcQ

短縮URLでも動作します：

https://youtu.be/dQw4w9WgXcQ

## Twitter/X投稿の埋込

Twitter/X投稿のURLを貼り付けると、ツイートが表示されます：

https://twitter.com/elonmusk/status/1234567890

X.comドメインでも動作します：

https://x.com/elonmusk/status/1234567890

## Instagram投稿の埋込

Instagram投稿のURLを貼り付けると、投稿が表示されます：

https://www.instagram.com/p/ABC123DEF456/

リール動画でも動作します：

https://www.instagram.com/reel/ABC123DEF456/

## Facebook投稿の埋込

Facebook投稿のURLを貼り付けると、投稿が表示されます：

https://www.facebook.com/pages/posts/1234567890

Facebook Watchの動画でも動作します：

https://fb.watch/abc123def456/

## Threads投稿の埋込

Threads投稿のURLを貼り付けると、リンクボタンが表示されます：

https://www.threads.net/@username/post/ABC123DEF456

## 通常のテキストとの混在

このように、通常のMarkdownテキストの中に

https://www.youtube.com/watch?v=dQw4w9WgXcQ

SNS URLを混在させても正しく埋込表示されます。

**太字**や *斜体* などの書式も問題なく使用できます。

## リストでの使用

1. YouTubeの埋込例：
   https://www.youtube.com/watch?v=dQw4w9WgXcQ

2. Twitterの埋込例：
   https://twitter.com/example/status/1234567890

- Instagram投稿：
  https://www.instagram.com/p/ABC123DEF456/

- Facebook投稿：
  https://www.facebook.com/pages/posts/1234567890

これで完了です！