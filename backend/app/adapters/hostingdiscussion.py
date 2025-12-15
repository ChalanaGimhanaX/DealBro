import re
import time
from datetime import datetime
from typing import Iterable, Tuple, Optional
from urllib.parse import urljoin

import cloudscraper
import feedparser
from bs4 import BeautifulSoup

from app.adapters.base import SourceAdapter
from app.adapters.types import DiscoveredThread, ParsedDealPost, ParsedDealItem
from app.adapters.utils import (
    extract_domain, normalize_price, extract_currency,
    extract_billing_period, normalize_monthly_price,
    extract_ram_mb, extract_storage_gb, extract_bandwidth_gb,
    clean_text, make_absolute_url
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class HostingDiscussionAdapter(SourceAdapter):
    """Adapter for HostingDiscussion.com (XenForo)."""

    RSS_URL = "/forums/-/index.rss"

    def __init__(self, base_url: str, user_agent: str, rate_limit: int = 30):
        super().__init__(base_url, user_agent)
        self.rate_limit = rate_limit
        self.last_request_time = 0
        
        # Use cloudscraper for Cloudflare bypass
        self.session = cloudscraper.create_scraper(
            browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
        )
        self.user_agent = user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        self.session.headers.update({
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9"
        })

    def _rate_limit(self):
        """Enforce rate limiting."""
        if self.rate_limit <= 0:
            return
        
        time_since_last = time.time() - self.last_request_time
        min_interval = 60.0 / self.rate_limit
        
        if time_since_last < min_interval:
            time.sleep(min_interval - time_since_last)
        
        self.last_request_time = time.time()

    def discover(self) -> Iterable[DiscoveredThread]:
        """Discover threads from RSS feed."""
        rss_url = urljoin(self.base_url, self.RSS_URL)
        
        try:
            self._rate_limit()
            response = self.session.get(rss_url, timeout=15)
            response.raise_for_status()
            
            feed = feedparser.parse(response.text)
            
            for entry in feed.entries[:50]:  # Limit to 50 most recent
                thread_url = entry.get('link', '')
                title = clean_text(entry.get('title', ''))
                
                # Extract publish date
                published = entry.get('published_parsed')
                discovered_at = datetime(*published[:6]) if published else datetime.utcnow()
                
                # Get summary
                summary = entry.get('summary', '')
                
                # Categorize from title
                category = self._categorize_from_title(title)
                
                yield DiscoveredThread(
                    url=thread_url,
                    category=category,
                    discovered_at=discovered_at,
                    source_thread_id=self._extract_thread_id(thread_url),
                    title=title,
                    summary=summary
                )
            
            logger.info("hostingdiscussion_discover_success", count=len(feed.entries))
            
        except Exception as e:
            logger.error("hostingdiscussion_discover_error", error=str(e))

    def fetch_thread_html(self, url: str) -> str:
        """Fetch thread HTML."""
        self._rate_limit()
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        return response.text

    def parse_thread(
        self, html: str, url: str, category: str, summary: Optional[str] = None, title: Optional[str] = None
    ) -> Tuple[ParsedDealPost, list[ParsedDealItem]]:
        """Parse thread HTML into structured data."""
        soup = BeautifulSoup(html, 'lxml')
        
        # Extract post metadata
        title_elem = soup.select_one('h1.p-title-value')
        title = clean_text(title_elem.get_text()) if title_elem else "Unknown"
        
        author_elem = soup.select_one('.message-name')
        author = clean_text(author_elem.get_text()) if author_elem else None
        
        # Extract post date
        time_elem = soup.select_one('time')
        posted_at = None
        if time_elem and time_elem.get('datetime'):
            try:
                posted_at = datetime.fromisoformat(time_elem['datetime'].replace('Z', '+00:00'))
            except:
                pass
        
        # Extract main post content
        content_elem = soup.select_one('.message-body .bbWrapper')
        raw_text = clean_text(content_elem.get_text()) if content_elem else ""
        
        # Extract thread ID
        thread_id = self._extract_thread_id(url)
        
        # Create post object
        post = ParsedDealPost(
            canonical_url=url,
            title=title,
            author=author,
            posted_at=posted_at,
            category=category,
            raw_text=raw_text,
            source_thread_id=thread_id
        )
        
        # Parse deal items
        items = self._parse_deal_items(content_elem, url) if content_elem else []
        
        return post, items

    def _parse_deal_items(self, content_soup, base_url: str) -> list[ParsedDealItem]:
        """Extract deal items from post content."""
        items = []
        content_text = content_soup.get_text()
        
        # Find all links in content (potential order links)
        links = content_soup.find_all('a', href=True)
        order_links = []
        provider_domain = None
        
        for link in links:
            href = link.get('href', '')
            text = clean_text(link.get_text())
            
            # Look for order/buy links
            if re.search(r'order|buy|purchase|client|billing', text, re.IGNORECASE):
                full_url = make_absolute_url(href, base_url)
                order_links.append(full_url)
                
                # Extract provider domain from first order link
                if not provider_domain:
                    provider_domain = extract_domain(full_url)
        
        # Look for price patterns
        price_pattern = r'Price[:\s]+([€$£¥₹]?\d+(?:[.,]\d+)?)\s*([A-Z]{3})?(?:/|\s*per\s*)?(mo|month|yr|year)?'
        price_matches = re.finditer(price_pattern, content_text, re.IGNORECASE)
        
        for idx, match in enumerate(price_matches):
            price_str = match.group(1)
            currency_code = match.group(2)
            period_str = match.group(3)
            
            price_amount = normalize_price(price_str)
            price_currency = currency_code or extract_currency(price_str)
            billing_period = extract_billing_period(period_str or match.group(0))
            
            # Extract specs from surrounding text
            context_start = max(0, match.start() - 200)
            context_end = min(len(content_text), match.end() + 200)
            context = content_text[context_start:context_end]
            
            item = ParsedDealItem(
                provider_domain=provider_domain,
                price_amount=price_amount,
                price_currency=price_currency,
                billing_period=billing_period,
                ram_mb=extract_ram_mb(context),
                storage_gb=extract_storage_gb(context),
                bandwidth_gb=extract_bandwidth_gb(context),
                order_url=order_links[0] if order_links else None,
                is_primary=(idx == 0)
            )
            
            # Calculate normalized monthly price
            if item.price_amount and item.billing_period:
                item.price_monthly_normalized = normalize_monthly_price(
                    item.price_amount,
                    item.billing_period
                )
            
            items.append(item)
        
        # If no price found, create a basic item
        if not items and provider_domain:
            items.append(ParsedDealItem(
                provider_domain=provider_domain,
                order_url=order_links[0] if order_links else None,
                is_primary=True
            ))
        
        return items

    def _extract_thread_id(self, url: str) -> str:
        """Extract thread ID from URL."""
        # XenForo URLs: /threads/<slug>.<id>/
        match = re.search(r'/threads/[^/]+\.(\d+)/?', url)
        if match:
            return match.group(1)
        return url

    def _categorize_from_title(self, title: str) -> str:
        """Categorize from thread title."""
        title_lower = title.lower()
        if 'vps' in title_lower:
            return 'vps'
        elif 'dedicated' in title_lower:
            return 'dedicated'
        elif 'shared' in title_lower or 'web hosting' in title_lower:
            return 'shared'
        elif 'reseller' in title_lower:
            return 'reseller'
        elif 'cloud' in title_lower:
            return 'cloud'
        return 'vps'  # default
