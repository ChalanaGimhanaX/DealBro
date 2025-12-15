from typing import Optional
from fastapi import APIRouter, Query, HTTPException
import math

from app.repositories.deal_repository import DealRepository

router = APIRouter()


@router.get("/deals")
async def get_deals(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    category: Optional[str] = Query(None, description="Filter by category"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum monthly price"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum monthly price"),
    billing_period: Optional[str] = Query(None, description="Billing period: month, year, one_time"),
    currency: Optional[str] = Query(None, description="Currency code (USD, EUR, etc.)"),
    location: Optional[str] = Query(None, description="Location/region"),
    source_id: Optional[str] = Query(None, description="Source ID"),
    search: Optional[str] = Query(None, description="Search in title and text"),
    include_duplicates: bool = Query(False, description="Include duplicate deals"),
    order_by: str = Query("posted_at", description="Order by: posted_at, created_at, title"),
):
    """Get paginated list of deals with filtering options."""
    repo = DealRepository()
    
    skip = (page - 1) * page_size
    
    deals, total = await repo.get_deals(
        skip=skip,
        limit=page_size,
        category=category,
        min_price=min_price,
        max_price=max_price,
        billing_period=billing_period,
        currency=currency,
        location=location,
        source_id=source_id,
        search=search,
        include_duplicates=include_duplicates,
        order_by=order_by
    )
    
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    
    return {
        "items": deals,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": total_pages
    }


@router.get("/deals/{deal_id}")
async def get_deal(deal_id: str):
    """Get a specific deal by ID."""
    repo = DealRepository()
    deal = await repo.get_deal_by_id(deal_id)
    
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    return deal


@router.get("/sources")
async def get_sources():
    """Get all sources."""
    repo = DealRepository()
    sources = await repo.get_sources()
    return sources


@router.get("/sources/{source_id}")
async def get_source(source_id: str):
    """Get a specific source by ID."""
    repo = DealRepository()
    source = await repo.get_source_by_id(source_id)
    
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    return source


@router.get("/categories")
async def get_categories():
    """Get list of all categories."""
    repo = DealRepository()
    categories = await repo.get_categories()
    return {"categories": categories}


@router.get("/currencies")
async def get_currencies():
    """Get list of all currencies."""
    repo = DealRepository()
    currencies = await repo.get_currencies()
    return {"currencies": currencies}


@router.get("/stats")
async def get_stats():
    """Get statistics about deals."""
    repo = DealRepository()
    return await repo.get_deal_stats()
