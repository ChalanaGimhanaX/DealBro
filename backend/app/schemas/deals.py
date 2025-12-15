from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class SourceSchema(BaseModel):
    id: int
    name: str
    base_url: str
    enabled: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DealItemSchema(BaseModel):
    id: int
    provider_name: Optional[str]
    plan_name: Optional[str] = None
    provider_domain: Optional[str]
    price_amount: Optional[float]
    price_currency: Optional[str]
    billing_period: Optional[str]
    price_monthly_normalized: Optional[float]
    location: Optional[str]
    cpu: Optional[str]
    cpu_brand: Optional[str] = None
    cpu_cores: Optional[int] = None
    ram_mb: Optional[int]
    storage_gb: Optional[int]
    bandwidth_gb: Optional[int]
    ipv4: Optional[int] = None
    ipv6: Optional[bool] = None
    promo_code: Optional[str] = None
    promo_url: Optional[str] = None
    order_url: Optional[str]
    is_primary: bool

    class Config:
        from_attributes = True


class DealPostSchema(BaseModel):
    id: int
    source_id: int
    source_thread_id: Optional[str]
    canonical_url: str
    title: str
    author: Optional[str]
    posted_at: Optional[datetime]
    last_seen_at: datetime
    category: Optional[str]
    raw_text: Optional[str]
    is_duplicate: bool
    created_at: datetime
    updated_at: datetime
    
    # Relationships
    source: SourceSchema
    deal_items: List[DealItemSchema]

    class Config:
        from_attributes = True


class DealPostListSchema(BaseModel):
    id: int
    source_id: int
    canonical_url: str
    title: str
    author: Optional[str]
    posted_at: Optional[datetime]
    category: Optional[str]
    is_duplicate: bool
    
    # Nested
    source: SourceSchema
    deal_items: List[DealItemSchema]

    class Config:
        from_attributes = True


class PaginatedDealsResponse(BaseModel):
    items: List[DealPostListSchema]
    total: int
    page: int
    page_size: int
    pages: int


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    database: str
    version: str
