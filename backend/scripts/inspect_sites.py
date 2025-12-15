"""Inspect site structures to understand how to scrape them."""
import cloudscraper
from bs4 import BeautifulSoup

sites = [
    ("WebHostingTalk", "https://www.webhostingtalk.com/"),
    ("ServerHunter", "https://www.serverhunter.com/"),
    ("HostingDiscussion", "https://hostingdiscussion.com/"),
]

scraper = cloudscraper.create_scraper()

for name, url in sites:
    print(f"\n{'='*60}")
    print(f"Checking {name}: {url}")
    print('='*60)
    
    try:
        response = scraper.get(url, timeout=15)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            print(f"Title: {soup.title.string if soup.title else 'No title'}")
            
            # Look for common forum structures
            print("\nSearching for forum/deal sections...")
            
            # Check for RSS/feeds
            rss_links = soup.find_all('link', {'type': 'application/rss+xml'})
            if rss_links:
                print(f"Found {len(rss_links)} RSS feeds:")
                for link in rss_links[:3]:
                    print(f"  - {link.get('href')}")
            
            # Check for navigation/menu links
            nav_links = soup.find_all(['a', 'nav'])[:20]
            print(f"\nFirst few navigation links:")
            for link in nav_links[:10]:
                href = link.get('href', '')
                text = link.get_text(strip=True)[:50]
                if href and text:
                    print(f"  {text}: {href}")
        else:
            print(f"Failed with status {response.status_code}")
            
    except Exception as e:
        print(f"Error: {str(e)}")
