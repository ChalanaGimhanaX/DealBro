"""Debug WebHostingTalk RSS feeds."""
import cloudscraper
import feedparser
from urllib.parse import urljoin

base_url = "https://www.webhostingtalk.com"

# Forum IDs from inspection
rss_urls = [
    "/external.php?type=RSS2&forumids=237",  # Web Hosting Offers
    "/external.php?type=RSS2&forumids=238",  # Dedicated Hosting Offers
    "/external.php?type=RSS2&forumids=242",  # VPS Hosting Offers
]

session = cloudscraper.create_scraper()

for rss_path in rss_urls:
    full_url = urljoin(base_url, rss_path)
    print(f"\nTesting: {full_url}")
    
    try:
        response = session.get(full_url, timeout=15)
        print(f"Status: {response.status_code}")
        print(f"Content length: {len(response.text)} chars")
        
        feed = feedparser.parse(response.text)
        print(f"Entries: {len(feed.entries)}")
        
        if feed.entries:
            print(f"\nFirst entry:")
            entry = feed.entries[0]
            print(f"  Title: {entry.get('title', 'N/A')}")
            print(f"  Link: {entry.get('link', 'N/A')}")
        else:
            print("  (No entries in feed)")
            print(f"\nFirst 500 chars of response:")
            print(response.text[:500])
        
    except Exception as e:
        print(f"Error: {e}")
