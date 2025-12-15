from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class DiscoveredThread:
    """Represents a thread discovered during scraping."""
    url: str
    category: str  # shared/vps/dedicated/etc.
    discovered_at: datetime
    source_thread_id: Optional[str] = None
    title: Optional[str] = None
    summary: Optional[str] = None  # RSS summary content


@dataclass
class ParsedDealPost:
    """Represents a parsed forum post with deal information."""
    canonical_url: str
    title: str
    author: Optional[str]
    posted_at: Optional[datetime]
    category: str
    raw_text: str
    source_thread_id: Optional[str] = None


@dataclass
class ParsedDealItem:
    """Represents a single deal item (plan/offer) extracted from a post."""
    provider_name: Optional[str] = None
    plan_name: Optional[str] = None
    provider_domain: Optional[str] = None
    price_amount: Optional[float] = None
    price_currency: Optional[str] = None
    billing_period: Optional[str] = None  # month/year/one_time
    price_monthly_normalized: Optional[float] = None
    location: Optional[str] = None
    cpu: Optional[str] = None
    cpu_brand: Optional[str] = None
    cpu_cores: Optional[int] = None
    ram_mb: Optional[int] = None
    storage_gb: Optional[int] = None
    bandwidth_gb: Optional[int] = None
    ipv4: Optional[int] = None
    ipv6: Optional[bool] = None
    order_url: Optional[str] = None
    is_primary: bool = False
