from typing import Optional
from datetime import datetime
from bson import ObjectId

from app.core.database import get_sync_db
from app.adapters.types import ParsedDealPost, ParsedDealItem
from app.services.fingerprint import make_strict_fingerprint, make_fuzzy_fingerprint
from app.services.llm_extractor import get_llm_extractor
from app.adapters.utils import normalize_monthly_price
from app.core.logging import get_logger

logger = get_logger(__name__)


class IngestionService:
    """Service for ingesting and storing deal posts (MongoDB version)."""

    def __init__(self, db=None):
        self.db = db or get_sync_db()

    def already_ingested(self, source: dict, canonical_url: str) -> bool:
        """Check if a post was already ingested."""
        existing = self.db.deal_posts.find_one({
            "source_id": str(source["_id"]),
            "canonical_url": canonical_url
        })
        
        if existing:
            # Update last_seen_at
            self.db.deal_posts.update_one(
                {"_id": existing["_id"]},
                {"$set": {"last_seen_at": datetime.utcnow()}}
            )
            return True
        
        return False

    def fingerprint_exists(self, fingerprint: str, fp_type: str) -> Optional[str]:
        """Check if a fingerprint already exists. Returns deal_post_id if found."""
        existing = self.db.deal_fingerprints.find_one({
            "fingerprint": fingerprint,
            "fingerprint_type": fp_type
        })
        
        return existing["deal_post_id"] if existing else None

    def insert_deal_post(
        self,
        source: dict,
        post: ParsedDealPost,
        raw_html: str,
        is_duplicate: bool = False,
        llm_metadata: dict = None
    ) -> str:
        """Insert a new deal post."""
        deal_post = {
            "source_id": str(source["_id"]),
            "source_name": source["name"],
            "source_thread_id": post.source_thread_id,
            "canonical_url": post.canonical_url,
            "title": post.title,
            "author": post.author,
            "posted_at": post.posted_at,
            "last_seen_at": datetime.utcnow(),
            "category": post.category,
            "raw_html": raw_html,
            "raw_text": post.raw_text,
            "is_duplicate": is_duplicate,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Add LLM metadata if available
        if llm_metadata:
            deal_post["llm_metadata"] = {
                "provider_name": llm_metadata.get('provider_name'),
                "provider_domain": llm_metadata.get('provider_domain'),
                "highlights": llm_metadata.get('highlights', []),
                "expires_at": llm_metadata.get('expires_at'),
                "extracted_at": datetime.utcnow()
            }
        
        result = self.db.deal_posts.insert_one(deal_post)
        post_id = str(result.inserted_id)
        
        logger.info(
            "deal_post_inserted",
            post_id=post_id,
            source=source["name"],
            title=post.title,
            is_duplicate=is_duplicate,
            llm_enhanced=bool(llm_metadata)
        )
        
        return post_id

    def insert_deal_item(self, deal_post_id: str, item: ParsedDealItem) -> str:
        """Insert a new deal item."""
        deal_item = {
            "deal_post_id": deal_post_id,
            "provider_name": item.provider_name,
            "plan_name": getattr(item, "plan_name", None),
            "provider_domain": item.provider_domain,
            "price_amount": item.price_amount,
            "price_currency": item.price_currency,
            "billing_period": item.billing_period,
            "price_monthly_normalized": getattr(item, 'price_monthly_normalized', None),
            "location": item.location,
            "cpu": item.cpu,
            "cpu_brand": getattr(item, "cpu_brand", None),
            "cpu_cores": getattr(item, "cpu_cores", None),
            "ram_mb": item.ram_mb,
            "storage_gb": item.storage_gb,
            "bandwidth_gb": item.bandwidth_gb,
            "ipv4": getattr(item, "ipv4", None),
            "ipv6": getattr(item, "ipv6", None),
            "promo_code": getattr(item, "promo_code", None),
            "promo_url": getattr(item, "promo_url", None),
            "order_url": item.order_url,
            "is_primary": item.is_primary,
            "created_at": datetime.utcnow()
        }
        
        result = self.db.deal_items.insert_one(deal_item)
        return str(result.inserted_id)

    def insert_fingerprint(self, deal_post_id: str, fingerprint: str, fp_type: str):
        """Insert a fingerprint for duplicate detection."""
        fp = {
            "deal_post_id": deal_post_id,
            "fingerprint": fingerprint,
            "fingerprint_type": fp_type,
            "created_at": datetime.utcnow()
        }
        
        self.db.deal_fingerprints.insert_one(fp)

    def mark_post_duplicate(self, post_id: str):
        """Mark a post as a duplicate."""
        self.db.deal_posts.update_one(
            {"_id": ObjectId(post_id)},
            {"$set": {"is_duplicate": True}}
        )
        
        logger.info("post_marked_duplicate", post_id=post_id)

    def ingest_thread(
        self,
        source: dict,
        post: ParsedDealPost,
        items: list[ParsedDealItem],
        raw_html: str
    ) -> Optional[str]:
        """Ingest a complete thread with LLM extraction and deduplication."""
        
        # Check if already ingested
        if self.already_ingested(source, post.canonical_url):
            logger.debug("thread_already_ingested", url=post.canonical_url)
            return None
        
        # Use LLM to extract and validate deal information
        extractor = get_llm_extractor()
        llm_data = extractor.extract_deal_info(post.title, post.raw_text, post.canonical_url)

        # Strict mode: if the LLM cannot validate/structure, don't ingest.
        if llm_data is None:
            logger.info("deal_rejected_by_llm", url=post.canonical_url, title=post.title)
            return None
        
        # Enhance post with LLM extracted data
        post.category = llm_data.get('deal_type', post.category) or post.category
        
        # Create enhanced deal items from LLM data or fall back to parsed items
        enhanced_items = []
        
        # Handle new configurations array format from LLM
        if llm_data.get('configurations'):
            configurations = llm_data['configurations']
            default_location = ', '.join(llm_data.get('locations', [])) if llm_data.get('locations') else None
            provider_name = llm_data.get('provider_name')
            provider_domain = llm_data.get('provider_domain')
            
            for idx, config in enumerate(configurations):
                if not isinstance(config, dict):
                    continue

                price_amount = config.get('price_amount')
                price_currency = config.get('price_currency', 'USD')
                billing_period = config.get('billing_period', 'month')
                price_monthly = None
                if price_amount is not None and billing_period:
                    try:
                        price_monthly = normalize_monthly_price(float(price_amount), billing_period)
                    except Exception:
                        price_monthly = None

                cpu_brand = config.get('cpu_brand')
                cpu_model = config.get('cpu_model')
                cpu_cores = config.get('cpu_cores')
                cpu_display = cpu_model or None
                if not cpu_display and cpu_brand and cpu_cores:
                    cpu_display = f"{cpu_brand} {cpu_cores}c"
                elif not cpu_display and cpu_cores:
                    cpu_display = f"{cpu_cores} cores"
                    
                enhanced_item = ParsedDealItem(
                    provider_name=provider_name,
                    plan_name=config.get('name'),
                    provider_domain=provider_domain,
                    price_amount=price_amount,
                    price_currency=price_currency,
                    billing_period=billing_period,
                    price_monthly_normalized=price_monthly,
                    location=config.get('location') or default_location,
                    cpu=cpu_display,
                    cpu_brand=cpu_brand,
                    cpu_cores=cpu_cores,
                    ram_mb=config.get('ram_mb'),
                    storage_gb=config.get('storage_gb'),
                    bandwidth_gb=config.get('bandwidth_gb'),
                    ipv4=config.get('ipv4'),
                    ipv6=config.get('ipv6'),
                    order_url=llm_data.get('order_url'),
                    is_primary=(idx == 0)  # First config is primary
                )
                enhanced_items.append(enhanced_item)
        
        # Fallback to old specs/price_info format if no configurations
        elif llm_data.get('specs') and llm_data.get('price_info'):
            specs = llm_data['specs']
            price_info = llm_data['price_info']
            
            # Handle case where price_info might be a list instead of dict
            if isinstance(price_info, list):
                price_info = price_info[0] if price_info else {}
            
            enhanced_item = ParsedDealItem(
                provider_name=llm_data.get('provider_name'),
                provider_domain=llm_data.get('provider_domain'),
                price_amount=price_info.get('amount') if isinstance(price_info, dict) else None,
                price_currency=price_info.get('currency') if isinstance(price_info, dict) else None,
                billing_period=price_info.get('billing_period') if isinstance(price_info, dict) else None,
                price_monthly_normalized=normalize_monthly_price(
                    float(price_info.get('amount')),
                    price_info.get('billing_period')
                ) if isinstance(price_info, dict) and price_info.get('amount') and price_info.get('billing_period') else None,
                location=', '.join(llm_data.get('locations', [])) if llm_data.get('locations') else None,
                cpu=specs.get('cpu_type') if isinstance(specs, dict) else None,
                ram_mb=specs.get('ram_mb') if isinstance(specs, dict) else None,
                storage_gb=specs.get('storage_gb') if isinstance(specs, dict) else None,
                bandwidth_gb=specs.get('bandwidth_gb') if isinstance(specs, dict) else None,
                order_url=llm_data.get('order_url'),
                is_primary=True
            )
            enhanced_items.append(enhanced_item)
        
        # Use enhanced items if available, otherwise fall back to parsed items
        items_to_store = enhanced_items if enhanced_items else items
        
        # Check for duplicates using fingerprints
        is_duplicate = False
        
        if items_to_store:
            for item in items_to_store:
                price_monthly = getattr(item, 'price_monthly_normalized', None)
                if price_monthly:
                    strict_fp = make_strict_fingerprint(item, post.category)
                    existing_post_id = self.fingerprint_exists(strict_fp, "strict")
                    
                    if existing_post_id:
                        is_duplicate = True
                        logger.info(
                            "duplicate_detected_strict",
                            url=post.canonical_url,
                            existing_post_id=existing_post_id
                        )
                        break
        
        # Check fuzzy fingerprint
        if not is_duplicate:
            fuzzy_fp = make_fuzzy_fingerprint(
                post.title,
                items_to_store[0].provider_domain if items_to_store else None,
                post.raw_text
            )
            existing_post_id = self.fingerprint_exists(fuzzy_fp, "fuzzy")
            
            if existing_post_id:
                logger.info(
                    "duplicate_detected_fuzzy",
                    url=post.canonical_url,
                    existing_post_id=existing_post_id
                )
        
        # Insert the post with LLM metadata
        post_id = self.insert_deal_post(source, post, raw_html, is_duplicate, llm_metadata=llm_data)
        
        # Insert items and fingerprints
        for item in items_to_store:
            self.insert_deal_item(post_id, item)
            
            # Create fingerprints
            price_monthly = getattr(item, 'price_monthly_normalized', None)
            if price_monthly:
                strict_fp = make_strict_fingerprint(item, post.category)
                self.insert_fingerprint(post_id, strict_fp, "strict")
        
        # Create fuzzy fingerprint for the post
        fuzzy_fp = make_fuzzy_fingerprint(
            post.title,
            items_to_store[0].provider_domain if items_to_store else None,
            post.raw_text
        )
        self.insert_fingerprint(post_id, fuzzy_fp, "fuzzy")
        
        return post_id
    def ingest_thread_with_llm_data(
        self,
        source: dict,
        post: ParsedDealPost,
        items: list[ParsedDealItem],
        raw_html: str,
        llm_data: dict
    ) -> Optional[str]:
        """
        Ingest a thread with pre-validated LLM data (from batch validation).
        Skips the individual LLM call since validation already happened.
        """
        # Check if already ingested
        if self.already_ingested(source, post.canonical_url):
            logger.debug("thread_already_ingested", url=post.canonical_url)
            return None
        
        # Update category from LLM
        post.category = llm_data.get('deal_type', post.category) or post.category
        
        # Build items from LLM configurations
        enhanced_items = []
        
        if llm_data.get('configurations'):
            configurations = llm_data['configurations']
            default_location = ', '.join(llm_data.get('locations', [])) if llm_data.get('locations') else None
            provider_name = llm_data.get('provider_name')
            provider_domain = llm_data.get('provider_domain')
            
            for idx, config in enumerate(configurations):
                if not isinstance(config, dict):
                    continue

                price_amount = config.get('price_amount')
                price_currency = config.get('price_currency', 'USD')
                billing_period = config.get('billing_period', 'month')
                price_monthly = None
                if price_amount is not None and billing_period:
                    try:
                        price_monthly = normalize_monthly_price(float(price_amount), billing_period)
                    except Exception:
                        price_monthly = None

                cpu_brand = config.get('cpu_brand')
                cpu_model = config.get('cpu_model')
                cpu_cores = config.get('cpu_cores')
                cpu_display = cpu_model or None
                if not cpu_display and cpu_brand and cpu_cores:
                    cpu_display = f"{cpu_brand} {cpu_cores}c"
                elif not cpu_display and cpu_cores:
                    cpu_display = f"{cpu_cores} cores"
                    
                enhanced_item = ParsedDealItem(
                    provider_name=provider_name,
                    plan_name=config.get('name'),
                    provider_domain=provider_domain,
                    price_amount=price_amount,
                    price_currency=price_currency,
                    billing_period=billing_period,
                    price_monthly_normalized=price_monthly,
                    location=config.get('location') or default_location,
                    cpu=cpu_display,
                    cpu_brand=cpu_brand,
                    cpu_cores=cpu_cores,
                    ram_mb=config.get('ram_mb'),
                    storage_gb=config.get('storage_gb'),
                    bandwidth_gb=config.get('bandwidth_gb'),
                    ipv4=config.get('ipv4'),
                    ipv6=config.get('ipv6'),
                    order_url=llm_data.get('order_url'),
                    is_primary=(idx == 0)
                )
                enhanced_items.append(enhanced_item)
        
        items_to_store = enhanced_items if enhanced_items else items
        
        # Check for duplicates
        is_duplicate = False
        if items_to_store:
            for item in items_to_store:
                price_monthly = getattr(item, 'price_monthly_normalized', None)
                if price_monthly:
                    strict_fp = make_strict_fingerprint(item, post.category)
                    existing_post_id = self.fingerprint_exists(strict_fp, "strict")
                    if existing_post_id:
                        is_duplicate = True
                        break
        
        # Insert post
        post_id = self.insert_deal_post(source, post, raw_html, is_duplicate, llm_metadata=llm_data)
        
        # Insert items and fingerprints
        for item in items_to_store:
            self.insert_deal_item(post_id, item)
            price_monthly = getattr(item, 'price_monthly_normalized', None)
            if price_monthly:
                strict_fp = make_strict_fingerprint(item, post.category)
                self.insert_fingerprint(post_id, strict_fp, "strict")
        
        # Create fuzzy fingerprint
        fuzzy_fp = make_fuzzy_fingerprint(
            post.title,
            items_to_store[0].provider_domain if items_to_store else None,
            post.raw_text
        )
        self.insert_fingerprint(post_id, fuzzy_fp, "fuzzy")
        
        logger.info(
            "thread_ingested_with_llm",
            post_id=post_id,
            title=post.title,
            items_count=len(items_to_store)
        )
        
        return post_id