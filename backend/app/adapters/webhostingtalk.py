"""
Adapter for WebHostingTalk.com Offers forums.
"""
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


class WebHostingTalkAdapter(SourceAdapter):
    """Adapter for WebHostingTalk.com Offers forums."""

    # Forum pages for offers
    OFFER_FORUMS = [
        ("forumdisplay.php?f=237", "shared"),      # Web Hosting Offers
        ("forumdisplay.php?f=238", "dedicated"),   # Dedicated Hosting Offers
        ("forumdisplay.php?f=242", "vps"),         # VPS Hosting Offers
        ("forumdisplay.php?f=243", "reseller"),    # Reseller Hosting Offers
    ]

    def __init__(self, base_url: str = "https://www.webhostingtalk.com", user_agent: str = None, rate_limit: int = 15):
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
        self.session.headers.update({
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
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
        """Discover threads from WHT offers forums by scraping forum pages."""
        
        for forum_path, category in self.OFFER_FORUMS:
            try:
                self._rate_limit()
                forum_url = urljoin(self.base_url, forum_path)
                
                response = self.session.get(forum_url, timeout=15)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # vBulletin thread list structure
                threads = soup.select('.threadbit, .threadtitle, li.threadbit')
                
                logger.info("wht_forum_scraped", forum=forum_path, found=len(threads))
                
                for thread in threads[:20]:  # Limit to 20 per forum
                    try:
                        # Find link to thread
                        link_elem = thread.select_one('a.threadtitle, a.title, a[id^="thread_title"]')
                        if not link_elem:
                            continue
                        
                        href = link_elem.get('href', '')
                        if not href:
                            continue
                        
                        url = make_absolute_url(href, self.base_url)
                        title = clean_text(link_elem.get_text())
                        
                        # Extract thread ID
                        thread_id = self._extract_thread_id(url)
                        if not thread_id:
                            continue
                        
                        yield DiscoveredThread(
                            url=url,
                            category=category,
                            discovered_at=datetime.utcnow(),
                            source_thread_id=thread_id,
                            title=title,
                        )
                    except Exception as e:
                        logger.warning("wht_thread_parse_error", error=str(e))
                        continue
                    
                logger.info("wht_discover_success", forum=forum_path, category=category, count=len(threads))
                
            except Exception as e:
                logger.error("wht_discover_error", forum=forum_path, error=str(e))

    def fetch_thread_html(self, url: str) -> str:
        """Fetch raw HTML for a thread."""
        self._rate_limit()
        response = self.session.get(url, timeout=20)
        response.raise_for_status()
        return response.text

    def _extract_thread_id(self, url: str) -> Optional[str]:
        """Extract thread ID from WHT URL."""
        # Match patterns like showthread.php?t=1234 or /threads/title.1234/
        patterns = [
            r't=(\d+)',
            r'\.(\d+)/?$',
            r'/(\d+)/?$',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None

    def parse_thread(
        self,
        html: str,
        url: str,
        category: str,
        summary: Optional[str] = None,
        title: Optional[str] = None,
    ) -> Tuple[ParsedDealPost, list[ParsedDealItem]]:
        """Parse a WHT thread HTML into structured data."""
        soup = BeautifulSoup(html, 'html.parser')

        # Extract title
        title_elem = soup.select_one('h1.p-title-value, .thread-title, h1')
        extracted_title = clean_text(title_elem.get_text()) if title_elem else None
        final_title = extracted_title or title or "WHT Offer"

        # Extract author
        author_elem = soup.select_one('.message-userDetails a, .author-name, .username')
        author = clean_text(author_elem.get_text()) if author_elem else None

        # Extract post date
        date_elem = soup.select_one('time, .DateTime, .post-date')
        posted_at = None
        if date_elem:
            date_str = date_elem.get('datetime') or date_elem.get('title') or date_elem.get_text()
            try:
                posted_at = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except:
                posted_at = datetime.utcnow()

        # Extract first post content
        post_elem = soup.select_one('.message-body, .postcontent, .post-content, article.message')
        raw_text = clean_text(post_elem.get_text()) if post_elem else ""

        # Determine category from URL or title
        final_category = category or self._categorize_from_url_title(url, final_title)

        post = ParsedDealPost(
            source_thread_id=self._extract_thread_id(url),
            canonical_url=url,
            title=final_title,
            author=author,
            posted_at=posted_at or datetime.utcnow(),
            category=final_category,
            raw_text=raw_text,
        )

        # Basic item extraction
        items = self._extract_items(soup, raw_text)

        return post, items

    def _categorize_from_url_title(self, url: str, title: str) -> str:
        """Categorize based on URL and title."""
        text = (url + " " + title).lower()
        
        if 'vps' in text or 'virtual' in text:
            return 'vps'
        elif 'dedicated' in text or 'dedi' in text:
            return 'dedicated'
        elif 'shared' in text or 'reseller' in text:
            return 'shared'
        elif 'cloud' in text:
            return 'cloud'
        
        return 'other'

    def _extract_items(self, soup: BeautifulSoup, raw_text: str) -> list[ParsedDealItem]:
        """Extract deal items from post content."""
        items = []
        
        # Try to find pricing from the text
        price_patterns = [
            r'\$[\d.]+(?:/mo|/month|/yr|/year)?',
            r'€[\d.]+(?:/mo|/month|/yr|/year)?',
            r'[\d.]+\s*(?:USD|EUR|GBP)(?:/mo|/month)?',
        ]
        
        prices = []
        for pattern in price_patterns:
            matches = re.findall(pattern, raw_text, re.IGNORECASE)
            prices.extend(matches)
        
        if prices:
            # Use first price found
            price_text = prices[0]
            
            item = ParsedDealItem(
                provider_name=None,
                provider_domain=None,
                price_amount=normalize_price(price_text),
                price_currency=extract_currency(price_text),
                billing_period=extract_billing_period(price_text),
                location=self._extract_location(raw_text),
                ram_mb=extract_ram_mb(raw_text),
                storage_gb=extract_storage_gb(raw_text),
                bandwidth_gb=extract_bandwidth_gb(raw_text),
                is_primary=True,
            )
            items.append(item)
        
        return items

    def _extract_location(self, text: str) -> Optional[str]:
        """Extract location from text."""
        location_patterns = [
            r'(?:location|datacenter|dc)[\s:]+([A-Za-z\s,]+?)(?:\n|$|\.)',
            r'(?:US|USA|EU|Europe|Asia|Germany|Netherlands|France|UK|Singapore|Japan)\b',
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return clean_text(match.group(1) if match.lastindex else match.group(0))
        
        return None
