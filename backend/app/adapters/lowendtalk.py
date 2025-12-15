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


class LowEndTalkAdapter(SourceAdapter):
    """Adapter for LowEndTalk.com (Vanilla Forums)."""

    CATEGORY_URL = "/categories/offers"
    RSS_URL = "/categories/offers/feed.rss"

    def __init__(self, base_url: str, user_agent: str, rate_limit: int = 30):
        super().__init__(base_url, user_agent)
        self.rate_limit = rate_limit
        self.last_request_time = 0
        
        # Use cloudscraper instead of requests.Session for Cloudflare bypass
        self.session = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )

        # Use a real browser UA
        self.user_agent = (
            user_agent
            or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
               "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        self.session.headers.update(
            {
                "User-Agent": self.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Cache-Control": "max-age=0",
            }
        )

        # Prime cookies so subsequent thread requests look less like a bot
        self._bootstrap_cookies()

    def _rate_limit(self):
        """Enforce rate limiting."""
        if self.rate_limit <= 0:
            return
        
        time_since_last = time.time() - self.last_request_time
        min_interval = 60.0 / self.rate_limit
        
        if time_since_last < min_interval:
            time.sleep(min_interval - time_since_last)
        
        self.last_request_time = time.time()

    def _bootstrap_cookies(self):
        """Hit a couple of safe pages to pick up session cookies before scraping threads."""
        try:
            for path in ["/", self.CATEGORY_URL]:
                self._rate_limit()
                self.session.get(urljoin(self.base_url, path), timeout=30)
        except Exception as exc:  # Best-effort warmup
            logger.warning("lowendtalk_cookie_bootstrap_failed", error=str(exc))

    def discover(self) -> Iterable[DiscoveredThread]:
        """Discover threads from RSS feed."""
        rss_url = urljoin(self.base_url, self.RSS_URL)
        
        try:
            self._rate_limit()
            response = self.session.get(rss_url, timeout=30)
            response.raise_for_status()
            
            feed = feedparser.parse(response.text)
            
            for entry in feed.entries[:100]:  # Limit to 100 most recent
                thread_url = entry.get('link', '')
                thread_id = self._extract_thread_id(thread_url)
                title = clean_text(entry.get('title', ''))
                
                # Try to extract publish date
                published = entry.get('published_parsed')
                discovered_at = datetime(*published[:6]) if published else datetime.now()
                
                # Get RSS summary content
                summary = entry.get('summary', '')
                
                # Categorize based on title keywords
                category = self._categorize_from_title(title)
                
                yield DiscoveredThread(
                    url=thread_url,
                    category=category,
                    discovered_at=discovered_at,
                    source_thread_id=thread_id,
                    title=title,
                    summary=summary
                )
            
            logger.info(
                "discovered_threads_rss",
                feed_url=rss_url,
                count=len(feed.entries)
            )
            
        except Exception as e:
            logger.error(
                "rss_discovery_failed",
                feed_url=rss_url,
                error=str(e)
            )

    def fetch_thread_html(self, url: str) -> Optional[str]:
        """Fetch thread HTML using cloudscraper for Cloudflare bypass."""
        self._rate_limit()
        
        try:
            response = self.session.get(url, timeout=15)  # Shorter timeout
            response.raise_for_status()
            return response.text
            
        except Exception as e:
            logger.warning(
                "thread_fetch_failed",
                url=url,
                error=str(type(e).__name__),
                message="Failed to fetch thread, will use RSS summary instead"
            )
            return None  # Signal to use RSS summary instead

    def parse_thread(
        self, html: Optional[str], url: str, category: str, summary: Optional[str] = None, title: Optional[str] = None
    ) -> Tuple[ParsedDealPost, list[ParsedDealItem]]:
        """Parse thread HTML into structured data. Falls back to RSS summary if HTML is unavailable."""
        
        if html is None:
            # Use RSS summary data
            return self._parse_from_rss_summary(url, category, summary or "", title)
        
        # Parse from HTML as before
        soup = BeautifulSoup(html, 'lxml')
        
        # Extract post metadata (Vanilla Forums structure)
        # Try multiple selectors for title
        title_elem = (
            soup.select_one('h1.Title') or 
            soup.select_one('.PageTitle h1') or
            soup.select_one('h1.discussionTitle') or
            soup.select_one('article h1') or
            soup.select_one('h1')
        )
        extracted_title = clean_text(title_elem.get_text()) if title_elem else None
        
        # Use extracted title, fallback to RSS title parameter, then "Unknown"
        final_title = extracted_title if extracted_title and extracted_title != "Unknown" else (title or "Deal Post")
        
        author_elem = soup.select_one('.Author a') or soup.select_one('.username')
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
        content_elem = soup.select_one('.Message') or soup.select_one('.post-content') or soup.select_one('article')
        raw_text = clean_text(content_elem.get_text()) if content_elem else ""
        
        # Extract thread ID
        thread_id = self._extract_thread_id(url)
        
        # Create post object
        post = ParsedDealPost(
            canonical_url=url,
            title=final_title,
            author=author,
            posted_at=posted_at,
            category=category,
            raw_text=raw_text,
            source_thread_id=thread_id
        )
        
        # Parse deal items
        items = self._parse_deal_items(content_elem, url) if content_elem else []
        
        return post, items

    def _parse_from_rss_summary(
        self, url: str, category: str, summary: str, title: str = None
    ) -> Tuple[ParsedDealPost, list[ParsedDealItem]]:
        """Parse thread from RSS summary when HTML fetching fails."""
        from bs4 import BeautifulSoup
        
        # Use title from thread if available
        post_title = title or "Deal Post"
        
        # Clean the summary HTML
        soup = BeautifulSoup(summary, 'lxml')
        raw_text = clean_text(soup.get_text())
        
        # Extract thread ID
        thread_id = self._extract_thread_id(url)
        
        # Create post object with limited metadata
        post = ParsedDealPost(
            canonical_url=url,
            title=post_title,
            author=None,  # Not available in RSS
            posted_at=None,  # Not available in RSS
            category=category,
            raw_text=raw_text,
            source_thread_id=thread_id
        )
        
        # Try to extract some deal items from the summary
        items = self._parse_deal_items_from_text(raw_text, url)
        
        return post, items

    def _parse_deal_items(self, content_soup, base_url: str) -> list[ParsedDealItem]:
        """Extract deal items from post content."""
        items = []
        content_text = content_soup.get_text()
        
        # Find all links in content
        links = content_soup.find_all('a', href=True)
        order_links = []
        provider_domain = None
        
        for link in links:
            href = link.get('href', '')
            text = clean_text(link.get_text())
            
            # Look for order/buy links
            if re.search(r'order|buy|purchase|client|cart|signup', text, re.IGNORECASE) or \
               re.search(r'order|cart|client', href, re.IGNORECASE):
                full_url = make_absolute_url(href, base_url)
                order_links.append(full_url)
                
                if not provider_domain:
                    provider_domain = extract_domain(full_url)
        
        # Look for price patterns (common in LET posts)
        price_patterns = [
            r'(?:^|\n)\s*([€$£¥₹]?\d+(?:[.,]\d+)?)\s*([A-Z]{3})?(?:/|\s*per\s*)?(mo|month|yr|year|annually)',
            r'Price[:\s]+([€$£¥₹]?\d+(?:[.,]\d+)?)\s*([A-Z]{3})?(?:/|\s*per\s*)?(mo|month|yr|year)?',
        ]
        
        for pattern in price_patterns:
            matches = re.finditer(pattern, content_text, re.IGNORECASE | re.MULTILINE)
            
            for idx, match in enumerate(matches):
                price_str = match.group(1)
                currency_code = match.group(2) if match.lastindex >= 2 else None
                period_str = match.group(3) if match.lastindex >= 3 else None
                
                price_amount = normalize_price(price_str)
                price_currency = currency_code or extract_currency(match.group(0))
                billing_period = extract_billing_period(period_str or match.group(0))
                
                # Extract specs from surrounding text
                context_start = max(0, match.start() - 300)
                context_end = min(len(content_text), match.end() + 300)
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
                    is_primary=(len(items) == 0)
                )
                
                if item.price_amount and item.billing_period:
                    item.price_monthly_normalized = normalize_monthly_price(
                        item.price_amount,
                        item.billing_period
                    )
                
                items.append(item)
                
            if items:
                break
        
        # If no price found, create a basic item
        if not items and provider_domain:
            items.append(ParsedDealItem(
                provider_domain=provider_domain,
                order_url=order_links[0] if order_links else None,
                is_primary=True
            ))
        
        return items

    def _parse_deal_items_from_text(self, content_text: str, base_url: str) -> list[ParsedDealItem]:
        """Extract deal items from plain text content (RSS summary)."""
        items = []
        
        # Look for links in the text using regex
        link_pattern = r'https?://[^\s<>"\']+'
        links = re.findall(link_pattern, content_text)
        order_links = []
        provider_domain = None
        
        for link in links:
            # Look for order/buy links
            if re.search(r'order|buy|purchase|client|cart|signup', link, re.IGNORECASE):
                order_links.append(link)
                if not provider_domain:
                    provider_domain = extract_domain(link)
        
        # Look for price patterns (same as HTML version)
        price_patterns = [
            r'(?:^|\n)\s*([€$£¥₹]?\d+(?:[.,]\d+)?)\s*([A-Z]{3})?(?:/|\s*per\s*)?(mo|month|yr|year|annually)',
            r'Price[:\s]+([€$£¥₹]?\d+(?:[.,]\d+)?)\s*([A-Z]{3})?(?:/|\s*per\s*)?(mo|month|yr|year)?',
        ]
        
        for pattern in price_patterns:
            matches = re.finditer(pattern, content_text, re.IGNORECASE | re.MULTILINE)
            
            for idx, match in enumerate(matches):
                price_str = match.group(1)
                currency_code = match.group(2) if match.lastindex >= 2 else None
                period_str = match.group(3) if match.lastindex >= 3 else None
                
                price_amount = normalize_price(price_str)
                price_currency = currency_code or extract_currency(match.group(0))
                billing_period = extract_billing_period(period_str or match.group(0))
                
                # Extract specs from surrounding text
                context_start = max(0, match.start() - 300)
                context_end = min(len(content_text), match.end() + 300)
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
                    is_primary=(len(items) == 0)
                )
                
                if item.price_amount and item.billing_period:
                    item.price_monthly_normalized = normalize_monthly_price(
                        item.price_amount,
                        item.billing_period
                    )
                
                items.append(item)
                
            if items:
                break
        
        # If no price found, create a basic item if we have a provider domain
        if not items and provider_domain:
            items.append(ParsedDealItem(
                provider_domain=provider_domain,
                order_url=order_links[0] if order_links else None,
                is_primary=True
            ))
        
        return items

    def _extract_thread_id(self, url: str) -> str:
        """Extract thread ID from URL."""
        # Vanilla Forums URLs: /discussion/<id>/<slug>
        match = re.search(r'/discussion/(\d+)/', url)
        if match:
            return match.group(1)
        return url

    def _categorize_from_title(self, title: str) -> str:
        """Categorize deal based on title keywords."""
        title_lower = title.lower()
        
        if any(kw in title_lower for kw in ['shared', 'cpanel', 'wordpress']):
            return 'shared'
        elif any(kw in title_lower for kw in ['reseller']):
            return 'reseller'
        elif any(kw in title_lower for kw in ['cloud']):
            return 'cloud'
        elif any(kw in title_lower for kw in ['vps', 'kvm', 'openvz', 'virtual']):
            return 'vps'
        elif any(kw in title_lower for kw in ['dedicated', 'dedi', 'bare metal']):
            return 'dedicated'
        elif any(kw in title_lower for kw in ['colo', 'colocation']):
            return 'colo'
        
        return 'other'
