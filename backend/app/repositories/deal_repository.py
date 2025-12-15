import re
from typing import Optional, List, Dict, Any

from bson import ObjectId

from app.core.database import get_async_db


class DealRepository:
    """Repository for deal queries with MongoDB."""

    def __init__(self):
        self.db = get_async_db()

    async def get_deals(
        self,
        skip: int = 0,
        limit: int = 20,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        billing_period: Optional[str] = None,
        currency: Optional[str] = None,
        location: Optional[str] = None,
        source_id: Optional[str] = None,
        search: Optional[str] = None,
        include_duplicates: bool = False,
        order_by: str = "posted_at"
    ) -> tuple[List[Dict], int]:
        """Get deals with filtering and pagination."""

        post_match: Dict[str, Any] = {}

        if not include_duplicates:
            post_match["is_duplicate"] = False

        if category:
            post_match["category"] = category

        if source_id:
            post_match["source_id"] = source_id

        if search:
            escaped = re.escape(search)
            post_match["$or"] = [
                {"title": {"$regex": escaped, "$options": "i"}},
                {"raw_text": {"$regex": escaped, "$options": "i"}},
            ]

        item_match: Dict[str, Any] = {}

        if billing_period:
            item_match["billing_period"] = billing_period

        if currency:
            item_match["price_currency"] = currency.upper()

        if location:
            item_match["location"] = {"$regex": re.escape(location), "$options": "i"}

        price_range: Dict[str, Any] = {}
        if min_price is not None:
            price_range["$gte"] = float(min_price)
        if max_price is not None:
            price_range["$lte"] = float(max_price)
        if price_range:
            item_match["price_monthly_normalized"] = price_range

        sort_field = order_by if order_by in ["posted_at", "created_at", "title"] else "posted_at"
        sort_direction = -1 if sort_field in ["posted_at", "created_at"] else 1

        deal_items_lookup_pipeline: List[Dict[str, Any]] = [
            {"$match": {"$expr": {"$eq": ["$deal_post_id", "$$postId"]}}},
        ]
        if item_match:
            deal_items_lookup_pipeline.append({"$match": item_match})
        deal_items_lookup_pipeline.extend(
            [
                {"$addFields": {"id": {"$toString": "$_id"}}},
                {"$project": {"_id": 0}},
            ]
        )

        pipeline: List[Dict[str, Any]] = [
            {"$match": post_match},
            {
                "$lookup": {
                    "from": "deal_items",
                    "let": {"postId": {"$toString": "$_id"}},
                    "pipeline": deal_items_lookup_pipeline,
                    "as": "deal_items",
                }
            },
        ]

        if item_match:
            pipeline.append({"$match": {"deal_items.0": {"$exists": True}}})

        pipeline.extend(
            [
                {
                    "$lookup": {
                        "from": "sources",
                        "localField": "source_name",
                        "foreignField": "name",
                        "as": "source",
                    }
                },
                {"$unwind": {"path": "$source", "preserveNullAndEmptyArrays": True}},
                {
                    "$facet": {
                        "items": [
                            {"$sort": {sort_field: sort_direction}},
                            {"$skip": int(skip)},
                            {"$limit": int(limit)},
                            {
                                "$addFields": {
                                    "id": {"$toString": "$_id"},
                                    "provider_name": {"$ifNull": [{"$getField": {"field": "provider_name", "input": "$llm_metadata"}}, None]},
                                    "provider_domain": {"$ifNull": [{"$getField": {"field": "provider_domain", "input": "$llm_metadata"}}, None]},
                                    "highlights": {"$ifNull": [{"$getField": {"field": "highlights", "input": "$llm_metadata"}}, []]},
                                    "source": {
                                        "$cond": [
                                            {"$ne": ["$source", None]},
                                            {
                                                "$mergeObjects": [
                                                    "$source",
                                                    {"id": {"$toString": "$source._id"}},
                                                ]
                                            },
                                            None,
                                        ]
                                    },
                                }
                            },
                            {"$project": {"_id": 0, "source._id": 0, "canonical_url": 0, "raw_html": 0, "raw_text": 0, "llm_metadata": 0}},
                        ],
                        "total": [{"$count": "count"}],
                    }
                },
            ]
        )

        result = await self.db.deal_posts.aggregate(pipeline).to_list(1)
        if not result:
            return [], 0

        deals = result[0].get("items", [])
        total_list = result[0].get("total", [])
        total = total_list[0]["count"] if total_list else 0
        return deals, total

    async def get_deal_by_id(self, deal_id: str) -> Optional[Dict]:
        """Get a single deal by ID."""
        try:
            post = await self.db.deal_posts.find_one({"_id": ObjectId(deal_id)})
            if not post:
                return None
            
            # Get source
            source = await self.db.sources.find_one({"name": post.get("source_name", "")})
            
            # Get items
            items = await self.db.deal_items.find({"deal_post_id": str(post["_id"])}).to_list(100)
            
            # Convert ObjectId
            post["id"] = str(post["_id"])
            del post["_id"]
            
            # Extract provider info from LLM metadata
            llm_meta = post.get("llm_metadata", {})
            post["provider_name"] = llm_meta.get("provider_name")
            post["provider_domain"] = llm_meta.get("provider_domain")
            post["highlights"] = llm_meta.get("highlights", [])
            
            # Hide forum URLs and internal data
            post.pop("canonical_url", None)
            post.pop("raw_html", None)
            post.pop("raw_text", None)
            post.pop("llm_metadata", None)
            
            if source:
                source["id"] = str(source["_id"])
                del source["_id"]
                post["source"] = source
            
            for item in items:
                item["id"] = str(item["_id"])
                del item["_id"]
            
            post["deal_items"] = items
            return post
            
        except Exception as e:
            print(f"Error getting deal: {e}")
            return None

    async def get_sources(self) -> List[Dict]:
        """Get all sources."""
        sources = await self.db.sources.find().to_list(100)
        for source in sources:
            source["id"] = str(source["_id"])
            del source["_id"]
        return sources

    async def get_source_by_id(self, source_id: str) -> Optional[Dict]:
        """Get a source by ID."""
        try:
            source = await self.db.sources.find_one({"_id": ObjectId(source_id)})
            if source:
                source["id"] = str(source["_id"])
                del source["_id"]
            return source
        except:
            return None

    async def get_categories(self) -> List[str]:
        """Get list of distinct categories."""
        categories = await self.db.deal_posts.distinct("category")
        return [c for c in categories if c]

    async def get_currencies(self) -> List[str]:
        """Get list of distinct currencies."""
        currencies = await self.db.deal_items.distinct("price_currency")
        return [c for c in currencies if c]

    async def get_deal_stats(self) -> dict:
        """Get statistics about deals."""
        total_deals = await self.db.deal_posts.count_documents({})
        total_active = await self.db.deal_posts.count_documents({"is_duplicate": False})
        
        # By category
        pipeline = [
            {"$match": {"is_duplicate": False}},
            {"$group": {"_id": "$category", "count": {"$sum": 1}}}
        ]
        by_category_result = await self.db.deal_posts.aggregate(pipeline).to_list(100)
        by_category = {item["_id"]: item["count"] for item in by_category_result if item["_id"]}
        
        # By source
        pipeline = [
            {"$match": {"is_duplicate": False}},
            {"$group": {"_id": "$source_name", "count": {"$sum": 1}}}
        ]
        by_source_result = await self.db.deal_posts.aggregate(pipeline).to_list(100)
        by_source = {item["_id"]: item["count"] for item in by_source_result if item["_id"]}
        
        return {
            "total_deals": total_deals,
            "total_active": total_active,
            "by_category": by_category,
            "by_source": by_source
        }
