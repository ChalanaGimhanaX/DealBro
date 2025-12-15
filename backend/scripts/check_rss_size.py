"""Check RSS feed size."""
import feedparser
import cloudscraper

session = cloudscraper.create_scraper()
response = session.get("https://lowendtalk.com/categories/offers/feed.rss", timeout=30)
feed = feedparser.parse(response.text)

print(f"LowEndTalk RSS returned {len(feed.entries)} entries")
print("\nFirst 10 titles:")
for i, entry in enumerate(feed.entries[:10], 1):
    print(f"{i}. {entry.title}")
