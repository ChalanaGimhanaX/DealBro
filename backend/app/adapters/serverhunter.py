"""
Adapter for ServerHunter.com - a hosting deals directory.
"""
import re
import time
from datetime import datetime
from typing import Iterable, Tuple, Optional
from urllib.parse import urljoin

import cloudscraper
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


class ServerHunterAdapter(SourceAdapter):
    """Adapter for ServerHunter.com directory."""

    def __init__(self, base_url: str = "https://www.serverhunter.com", user_agent: str = None, rate_limit: int = 20):
        super().__init__(base_url, user_agent)
        self.rate_limit = rate_limit
        self.last_request_time = 0
        
        # Use cloudscraper for potential Cloudflare bypass
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
        """Discover VPS listings from ServerHunter homepage."""
        # Scrape homepage - where the actual content is
        try:
            self._rate_limit()
            response = self.session.get(self.base_url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find server cards/listings - need to inspect the actual HTML structure
            # Common patterns: cards, listings, offers, server items
            listings = soup.select('.card, .server, .listing, .offer, [class*="server"], [class*="listing"]')
            
            logger.info("serverhunter_listings_found", count=len(listings))
            
            for listing in listings[:50]:
                try:
                    # Extract link - various possible patterns
                    link_elem = listing.select_one('a[href*="/server"], a[href*="/offer"], a[href*="/view"], a')
                    if not link_elem:
                        continue
                    
                    href = link_elem.get('href', '')
                    if not href or href.startswith('#') or href == '/':
                        continue
                    
                    url = make_absolute_url(href, self.base_url)
                    
                    # Extract title
                    title_elem = listing.select_one('h1, h2, h3, h4, .title, [class*="title"], [class*="name"]')
                    title = clean_text(title_elem.get_text()) if title_elem else "Server Offer"
                    
                    # Extract server ID from URL
                    server_id = self._extract_server_id(url)
                    if not server_id:
                        continue
                    
                    # Determine category from title/description
                    category = self._categorize_from_text(title)
                    
                    yield DiscoveredThread(
                        url=url,
                        category=category,
                        discovered_at=datetime.utcnow(),
                        source_thread_id=server_id,
                        title=title,
                    )
                    
                except Exception as e:
                    logger.warning("serverhunter_listing_parse_error", error=str(e))
                    continue
                    
        except Exception as e:
            logger.error("serverhunter_discover_error", error=str(e))

    def fetch_thread_html(self, url: str) -> str:
        """Fetch raw HTML for a listing."""
        self._rate_limit()
        response = self.session.get(url, timeout=20)
        response.raise_for_status()
        return response.text

    def _extract_id(self, url: str) -> str:
        """Extract unique ID from URL."""
        # Try to get ID from URL path
        match = re.search(r'/(\d+)/?$', url)
        if match:
            return match.group(1)
        
        # Fallback to hash of URL
        import hashlib
        return hashlib.md5(url.encode()).hexdigest()[:12]

    def parse_thread(
        self,
        html: str,
        url: str,
        category: str,
        summary: Optional[str] = None,
        title: Optional[str] = None,
    ) -> Tuple[ParsedDealPost, list[ParsedDealItem]]:
        """Parse a ServerHunter listing page."""
        soup = BeautifulSoup(html, 'html.parser')

        # Extract title
        title_elem = soup.select_one('h1, .server-title, .listing-title')
        extracted_title = clean_text(title_elem.get_text()) if title_elem else None
        final_title = extracted_title or title or "Server Offer"

        # Extract provider name
        provider_elem = soup.select_one('.provider-name, .company-name, .seller-name')
        provider = clean_text(provider_elem.get_text()) if provider_elem else None

        # Extract full description
        desc_elem = soup.select_one('.server-description, .listing-content, .description, article')
        raw_text = clean_text(desc_elem.get_text()) if desc_elem else ""

        # Try to extract specs from structured data
        specs = self._extract_specs(soup)

        # Create post
        post = ParsedDealPost(
            source_thread_id=self._extract_id(url),
            canonical_url=url,
            title=final_title,
            author=provider,
            posted_at=datetime.utcnow(),
            category=category or ("vps" if "vps" in url.lower() else "dedicated"),
            raw_text=raw_text,
        )

        # Create items from specs
        items = []
        if specs:
            item = ParsedDealItem(
                provider_name=provider,
                provider_domain=extract_domain(url),
                price_amount=specs.get('price'),
                price_currency=specs.get('currency', 'USD'),
                billing_period=specs.get('billing_period', 'month'),
                price_monthly_normalized=normalize_monthly_price(specs.get('price'), specs.get('billing_period', 'month')),
                location=specs.get('location'),
                cpu=specs.get('cpu'),
                ram_mb=specs.get('ram_mb'),
                storage_gb=specs.get('storage_gb'),
                bandwidth_gb=specs.get('bandwidth_gb'),
                is_primary=True,
            )
            items.append(item)

        return post, items

    def _extract_specs(self, soup: BeautifulSoup) -> dict:
        """Extract specs from the page."""
        specs = {}
        
        # Look for spec rows/items
        spec_rows = soup.select('.spec-row, .spec-item, .server-spec, tr')
        
        for row in spec_rows:
            text = row.get_text().lower()
            
            # RAM
            if 'ram' in text or 'memory' in text:
                specs['ram_mb'] = extract_ram_mb(text)
            
            # Storage
            if 'storage' in text or 'disk' in text or 'ssd' in text or 'hdd' in text:
                specs['storage_gb'] = extract_storage_gb(text)
            
            # Bandwidth
            if 'bandwidth' in text or 'traffic' in text or 'transfer' in text:
                specs['bandwidth_gb'] = extract_bandwidth_gb(text)
            
            # CPU
            if 'cpu' in text or 'core' in text or 'processor' in text:
                cpu_elem = row.select_one('.spec-value, td:last-child')
                if cpu_elem:
                    specs['cpu'] = clean_text(cpu_elem.get_text())
            
            # Location
            if 'location' in text or 'datacenter' in text or 'region' in text:
                loc_elem = row.select_one('.spec-value, td:last-child')
                if loc_elem:
                    specs['location'] = clean_text(loc_elem.get_text())
        
        # Extract price
        price_elem = soup.select_one('.price, .server-price, .listing-price')
        if price_elem:
            price_text = price_elem.get_text()
            specs['price'] = normalize_price(price_text)
            specs['currency'] = extract_currency(price_text)
            specs['billing_period'] = extract_billing_period(price_text)
        
        return specs

    def _extract_server_id(self, url: str) -> Optional[str]:
        """Extract server ID from URL."""
        # Try to get ID from URL path
        match = re.search(r'/server/([^/]+)', url)
        if match:
            return match.group(1)
        
        match = re.search(r'/(\d+)/?$', url)
        if match:
            return match.group(1)
        
        # Fallback to hash of URL
        import hashlib
        return hashlib.md5(url.encode()).hexdigest()[:12]

    def _categorize_from_text(self, text: str) -> str:
        """Categorize offer from text."""
        text_lower = text.lower()
        if 'dedicated' in text_lower:
            return 'dedicated'
        elif 'vps' in text_lower or 'virtual' in text_lower:
            return 'vps'
        elif 'cloud' in text_lower:
            return 'cloud'
        elif 'shared' in text_lower or 'hosting' in text_lower:
            return 'shared'
        return 'vps'  # default
