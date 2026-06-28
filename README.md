# LINE ITニュース通知Bot

毎朝7:00（JST）に、RSSフィードから新着のITニュースを集めてLINEにプッシュ通知します。

## セットアップ手順

### 1. LINE公式アカウント（Messaging API）を作成する

1. [LINE Developers](https://developers.line.biz/console/) にLINEアカウントでログイン
2. 「新規プロバイダー作成」→ 任意の名前（例: `自分用News`）で作成
3. 作成したプロバイダー内で「新規チャネル作成」→ 「Messaging API」を選択
4. チャネル名・説明・業種などを入力して作成（個人利用でOK、業種は「個人」など）
5. 作成後、チャネルの「Messaging API設定」タブを開く
   - **チャネルアクセストークン（長期）** を発行してコピーしておく（後でGitHub Secretsに登録）
   - QRコードが表示されるので、それを自分のLINEで読み取り「友達追加」する
   - 「応答メッセージ」はオフにしておくと良い（Bot設定 → 応答設定）

### 2. このリポジトリをGitHubにpush

```bash
cd line-news-bot
git init
git add .
git commit -m "Initial commit: LINE IT news bot"
git branch -M main
git remote add origin <あなたのGitHubリポジトリURL>
git push -u origin main
```

### 3. GitHub Secretsにトークンを登録

1. GitHubリポジトリ → Settings → Secrets and variables → Actions
2. 「New repository secret」
   - Name: `LINE_CHANNEL_ACCESS_TOKEN`
   - Secret: 手順1でコピーしたチャネルアクセストークン

### 4. 動作確認

GitHubリポジトリの Actions タブ → 「Send IT News to LINE」 → 「Run workflow」で手動実行し、
LINEに通知が届くか確認してください。

以降は毎日 22:00 UTC（日本時間 朝7:00）に自動実行されます。

## カスタマイズ

- `feeds.txt`: 取得するRSSフィードのURLを1行ずつ記載。`#`で始まる行はコメント（無効化）。
- `fetch_news.py` 内の定数で調整可能:
  - `MAX_PER_FEED`: 1フィードあたりの最大記事数
  - `LOOKBACK_HOURS`: 何時間前までの記事を対象にするか
  - `.github/workflows/news.yml` の `cron`: 実行時刻（UTC指定）

## ローカルでのテスト

```bash
pip install -r requirements.txt
export LINE_CHANNEL_ACCESS_TOKEN="xxxx"   # Windows PowerShellなら $env:LINE_CHANNEL_ACCESS_TOKEN="xxxx"
python fetch_news.py
```

## 注意点

- LINEのブロードキャスト配信は、そのBotを友達登録している**全員**に届きます。自分しか友達登録していなければ実質「自分専用通知」になりますが、Botを誰かと共有しないよう注意してください。
- LINE Messaging APIの無料プランは月1000通まで無料（ブロードキャストは1回の配信が1通としてカウント）。1日1回の通知なら余裕で無料枠内です。
