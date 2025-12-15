"""Find offers/deals sections on each site."""
import cloudscraper
from bs4 import BeautifulSoup

scraper = cloudscraper.create_scraper()

print("="*60)
print("WebHostingTalk - Finding offers sections")
print("="*60)
try:
    response = scraper.get("https://www.webhostingtalk.com/", timeout=15)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Look for "offers" or "deals" links
    links = soup.find_all('a', href=True)
    offer_links = [l for l in links if any(word in l.get_text().lower() for word in ['offer', 'deal', 'promo', 'special'])]
    
    print(f"Found {len(offer_links)} offer-related links:")
    for link in offer_links[:10]:
        print(f"  {link.get_text(strip=True)}: {link['href']}")
    
    # Try RSS feed
    print("\nTrying RSS feed...")
    rss_response = scraper.get("https://www.webhostingtalk.com/external.php?type=RSS2", timeout=15)
    print(f"RSS Status: {rss_response.status_code}")
    if rss_response.status_code == 200:
        print(f"RSS length: {len(rss_response.text)} chars")
        
except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*60)
print("ServerHunter - Finding server listings")
print("="*60)
try:
    # Try different potential paths
    paths_to_try = [
        "/",
        "/servers/",
        "/offers/",
        "/deals/",
        "/search/",
    ]
    
    for path in paths_to_try:
        try:
            url = f"https://www.serverhunter.com{path}"
            response = scraper.get(url, timeout=10)
            if response.status_code == 200:
                print(f"✓ {path}: {response.status_code}")
                soup = BeautifulSoup(response.text, 'html.parser')
                # Look for server listings
                if 'server' in response.text.lower() or 'vps' in response.text.lower():
                    print(f"  Contains server/VPS content")
            else:
                print(f"✗ {path}: {response.status_code}")
        except:
            print(f"✗ {path}: Failed")
            
except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*60)
print("HostingDiscussion - Finding forums/offers")
print("="*60)
try:
    response = scraper.get("https://hostingdiscussion.com/", timeout=15)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find forum links
    links = soup.find_all('a', href=True)
    forum_links = [l for l in links if 'forum' in l['href'] or any(word in l.get_text().lower() for word in ['vps', 'dedicated', 'hosting', 'offer'])]
    
    print(f"Found {len(forum_links)} forum/hosting links:")
    for link in forum_links[:15]:
        print(f"  {link.get_text(strip=True)[:50]}: {link['href']}")
        
    # Try RSS
    print("\nTrying RSS feed...")
    rss_response = scraper.get("https://hostingdiscussion.com/forums/-/index.rss", timeout=15)
    print(f"RSS Status: {rss_response.status_code}")
    
except Exception as e:
    print(f"Error: {e}")
