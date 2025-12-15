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


class LowEndBoxAdapter(SourceAdapter):
    """Adapter for LowEndBox.com (WordPress blog)."""

    RSS_URL = "/feed/"

    def __init__(self, base_url: str, user_agent: str, rate_limit: int = 30):
        super().__init__(base_url, user_agent)
        self.rate_limit = rate_limit
        self.last_request_time = 0
        
        # Use cloudscraper for Cloudflare bypass
        self.session = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )

        self.user_agent = (
            user_agent
            or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
               "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        self.session.headers.update(
            {
                "User-Agent": self.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
            }
        )

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
        """Discover posts from RSS feed."""
        rss_url = urljoin(self.base_url, self.RSS_URL)
        
        try:
            self._rate_limit()
            response = self.session.get(rss_url, timeout=15)
            response.raise_for_status()
            
            feed = feedparser.parse(response.text)
            
            for entry in feed.entries[:50]:  # Limit to 50 most recent
                post_url = entry.get('link', '')
                title = clean_text(entry.get('title', ''))
                
                # Extract publish date
                published = entry.get('published_parsed')
                discovered_at = datetime(*published[:6]) if published else datetime.now()
                
                # Get summary content
                summary = entry.get('summary', '') or entry.get('content', [{}])[0].get('value', '')
                
                # LowEndBox posts are typically VPS deals
                category = self._categorize_from_title(title)
                
                yield DiscoveredThread(
                    url=post_url,
                    category=category,
                    discovered_at=discovered_at,
                    source_thread_id=self._extract_post_id(post_url),
                    title=title,
                    summary=summary
                )
            
            logger.info(
                "discovered_posts_rss",
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
        """Fetch post HTML using cloudscraper."""
        self._rate_limit()
        
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            return response.text
            
        except Exception as e:
            logger.warning(
                "post_fetch_failed",
                url=url,
                error=str(type(e).__name__),
                message="Failed to fetch post, will use RSS summary instead"
            )
            return None

    def parse_thread(
        self, html: Optional[str], url: str, category: str, summary: Optional[str] = None, title: Optional[str] = None
    ) -> Tuple[ParsedDealPost, list[ParsedDealItem]]:
        """Parse post HTML or RSS summary into structured data."""
        
        if html is None:
            # Use RSS summary data
            return self._parse_from_rss_summary(url, category, summary or "", title)
        
        # Parse from HTML
        soup = BeautifulSoup(html, 'lxml')
        
        # Extract post metadata (WordPress structure)
        title_elem = soup.select_one('h1.entry-title') or soup.select_one('h1.post-title') or soup.select_one('article h1')
        post_title = clean_text(title_elem.get_text()) if title_elem else (title or "Deal Post")
        
        # Extract post date
        time_elem = soup.select_one('time')
        posted_at = None
        if time_elem and time_elem.get('datetime'):
            try:
                posted_at = datetime.fromisoformat(time_elem['datetime'].replace('Z', '+00:00'))
            except:
                pass
        
        # Extract main post content
        content_elem = soup.select_one('article .entry-content') or soup.select_one('.post-content') or soup.select_one('article')
        raw_text = clean_text(content_elem.get_text()) if content_elem else ""
        
        # Extract post ID
        post_id = self._extract_post_id(url)
        
        # Create post object
        post = ParsedDealPost(
            canonical_url=url,
            title=post_title,
            author=None,
            posted_at=posted_at,
            category=category,
            raw_text=raw_text,
            source_thread_id=post_id
        )
        
        # Parse deal items
        items = self._parse_deal_items(content_elem, url) if content_elem else []
        
        return post, items

    def _parse_from_rss_summary(
        self, url: str, category: str, summary: str, title: str = None
    ) -> Tuple[ParsedDealPost, list[ParsedDealItem]]:
        """Parse post from RSS summary when HTML fetching fails."""
        from bs4 import BeautifulSoup
        
        post_title = title if title else "Deal Post"
        
        # Clean the summary HTML
        soup = BeautifulSoup(summary, 'lxml')
        raw_text = clean_text(soup.get_text())
        
        # Extract post ID
        post_id = self._extract_post_id(url)
        
        # Create post object
        post = ParsedDealPost(
            canonical_url=url,
            title=post_title,
            author=None,
            posted_at=None,
            category=category,
            raw_text=raw_text,
            source_thread_id=post_id
        )
        
        # Try to extract deal items from the summary
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
            if re.search(r'order|buy|purchase|client|cart|signup|visit', text, re.IGNORECASE) or \
               re.search(r'order|cart|client', href, re.IGNORECASE):
                full_url = make_absolute_url(href, base_url)
                order_links.append(full_url)
                
                if not provider_domain:
                    provider_domain = extract_domain(full_url)
        
        # Look for price patterns
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

    def _parse_deal_items_from_text(self, content_text: str, base_url: str) -> list[ParsedDealItem]:
        """Extract deal items from plain text content (RSS summary)."""
        items = []
        
        # Look for links in the text
        link_pattern = r'https?://[^\s<>"\']+'
        links = re.findall(link_pattern, content_text)
        order_links = []
        provider_domain = None
        
        for link in links:
            if re.search(r'order|buy|purchase|client|cart|signup|visit', link, re.IGNORECASE):
                order_links.append(link)
                if not provider_domain:
                    provider_domain = extract_domain(link)
        
        # Look for price patterns
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

    def _extract_post_id(self, url: str) -> str:
        """Extract post ID from URL."""
        # WordPress URLs: /<slug>/ or /?p=<id>
        match = re.search(r'\?p=(\d+)', url)
        if match:
            return match.group(1)
        
        # Use slug as ID
        match = re.search(r'/([^/]+)/?$', url)
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
        
        return 'vps'  # Default to VPS for LowEndBox
