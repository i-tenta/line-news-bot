"""
ITニュースをRSSフィードから取得し、LINEにブロードキャスト配信するスクリプト。

毎朝GitHub Actionsから実行される想定。
LINE Messaging APIの「ブロードキャスト配信」を使うため、
自分のLINEユーザーIDを調べる必要はない（友達がBotアカウント自分だけなら、配信先は自分だけになる）。
"""

import os
import sys
from datetime import datetime, timedelta, timezone

import feedparser
import requests

FEEDS_FILE = os.path.join(os.path.dirname(__file__), "feeds.txt")
LINE_BROADCAST_URL = "https://api.line.me/v2/bot/message/broadcast"
JST = timezone(timedelta(hours=9))
MAX_PER_FEED = 5
LOOKBACK_HOURS = 26  # 前回実行からの取りこぼしを防ぐため24時間より少し長め


def load_feed_urls():
    with open(FEEDS_FILE, encoding="utf-8") as f:
        urls = [line.strip() for line in f]
    return [u for u in urls if u and not u.startswith("#")]


def entry_is_recent(entry, cutoff):
    for key in ("published_parsed", "updated_parsed"):
        t = entry.get(key)
        if t:
            published = datetime(*t[:6], tzinfo=timezone.utc)
            return published >= cutoff
    return True  # 日付が取れない場合は対象に含める


def collect_articles(feed_urls):
    cutoff = datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)
    articles = []
    for url in feed_urls:
        parsed = feedparser.parse(url)
        site_name = parsed.feed.get("title", url)
        count = 0
        for entry in parsed.entries:
            if count >= MAX_PER_FEED:
                break
            if not entry_is_recent(entry, cutoff):
                continue
            title = entry.get("title", "(無題)").strip()
            link = entry.get("link", "").strip()
            if not link:
                continue
            articles.append({"site": site_name, "title": title, "link": link})
            count += 1
    return articles


def build_messages(articles):
    today = datetime.now(JST).strftime("%Y/%m/%d")
    if not articles:
        return [f"【ITニュース {today}】\n本日は新着記事が見つかりませんでした。"]

    lines = [f"【ITニュース {today}】 全{len(articles)}件\n"]
    for a in articles:
        lines.append(f"■{a['title']}\n{a['link']}")
    full_text = "\n\n".join(lines)

    # LINEのテキストメッセージは1件最大5000文字、broadcastは最大5件まで送信可能
    messages = []
    chunk = ""
    for block in full_text.split("\n\n"):
        candidate = (chunk + "\n\n" + block) if chunk else block
        if len(candidate) > 4800:
            messages.append(chunk)
            chunk = block
        else:
            chunk = candidate
    if chunk:
        messages.append(chunk)
    return messages[:5]


def send_to_line(messages, channel_access_token):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {channel_access_token}",
    }
    payload = {"messages": [{"type": "text", "text": m} for m in messages]}
    resp = requests.post(LINE_BROADCAST_URL, headers=headers, json=payload, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(f"LINE API error {resp.status_code}: {resp.text}")


def main():
    channel_access_token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    if not channel_access_token:
        print("環境変数 LINE_CHANNEL_ACCESS_TOKEN が設定されていません", file=sys.stderr)
        sys.exit(1)

    feed_urls = load_feed_urls()
    articles = collect_articles(feed_urls)
    messages = build_messages(articles)
    send_to_line(messages, channel_access_token)
    print(f"送信完了: {len(articles)}件の記事を{len(messages)}件のメッセージで送信しました")


if __name__ == "__main__":
    main()
