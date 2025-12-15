from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from app.core.config import settings

# Async client (for FastAPI)
async_client: AsyncIOMotorClient = None
async_db = None

# Sync client (for scheduler)
sync_client: MongoClient = None
sync_db = None


async def connect_to_mongo():
    """Connect to MongoDB (async)."""
    global async_client, async_db
    async_client = AsyncIOMotorClient(settings.mongodb_url)
    async_db = async_client[settings.database_name]
    
    # Create indexes
    await create_indexes(async_db)
    print(f"Connected to MongoDB: {settings.database_name}")


async def close_mongo_connection():
    """Close MongoDB connection (async)."""
    global async_client
    if async_client:
        async_client.close()
        print("Closed MongoDB connection")


def get_sync_db():
    """Get synchronous database connection for scheduler."""
    global sync_client, sync_db
    if sync_db is None:
        sync_client = MongoClient(settings.mongodb_url)
        sync_db = sync_client[settings.database_name]
        create_indexes_sync(sync_db)
    return sync_db


def get_async_db():
    """Get async database instance."""
    return async_db


async def create_indexes(db):
    """Create MongoDB indexes."""
    # Sources collection
    await db.sources.create_index("name", unique=True)
    
    # Deal posts collection
    await db.deal_posts.create_index("source_id")
    await db.deal_posts.create_index("canonical_url")
    await db.deal_posts.create_index([("source_id", 1), ("canonical_url", 1)], unique=True)
    await db.deal_posts.create_index("posted_at")
    await db.deal_posts.create_index("category")
    await db.deal_posts.create_index("is_duplicate")
    
    # Deal items collection
    await db.deal_items.create_index("deal_post_id")
    await db.deal_items.create_index("price_monthly_normalized")
    
    # Fingerprints collection
    await db.deal_fingerprints.create_index("fingerprint")
    await db.deal_fingerprints.create_index("deal_post_id")


def create_indexes_sync(db):
    """Create MongoDB indexes (sync version)."""
    db.sources.create_index("name", unique=True)
    db.deal_posts.create_index("source_id")
    db.deal_posts.create_index("canonical_url")
    db.deal_posts.create_index([("source_id", 1), ("canonical_url", 1)], unique=True)
    db.deal_posts.create_index("posted_at")
    db.deal_posts.create_index("category")
    db.deal_posts.create_index("is_duplicate")
    db.deal_items.create_index("deal_post_id")
    db.deal_items.create_index("price_monthly_normalized")
    db.deal_fingerprints.create_index("fingerprint")
    db.deal_fingerprints.create_index("deal_post_id")


async def init_default_sources():
    """Initialize default sources if not exist."""
    db = get_async_db()
    
    default_sources = [
        {"name": "lowendtalk", "base_url": "https://lowendtalk.com", "enabled": True},
        {"name": "lowendbox", "base_url": "https://lowendbox.com", "enabled": True},
        {"name": "webhostingtalk", "base_url": "https://www.webhostingtalk.com", "enabled": True},
        {"name": "serverhunter", "base_url": "https://www.serverhunter.com", "enabled": True},
        {"name": "hostingdiscussion", "base_url": "https://hostingdiscussion.com", "enabled": True},
    ]
    
    for source in default_sources:
        existing = await db.sources.find_one({"name": source["name"]})
        if not existing:
            from datetime import datetime
            source["created_at"] = datetime.utcnow()
            source["updated_at"] = datetime.utcnow()
            await db.sources.insert_one(source)
            print(f"Created source: {source['name']}")


def init_default_sources_sync():
    """Initialize default sources if not exist (sync version)."""
    db = get_sync_db()
    
    default_sources = [
        {"name": "lowendtalk", "base_url": "https://lowendtalk.com", "enabled": True},
        {"name": "lowendbox", "base_url": "https://lowendbox.com", "enabled": True},
        {"name": "webhostingtalk", "base_url": "https://www.webhostingtalk.com", "enabled": True},
        {"name": "serverhunter", "base_url": "https://www.serverhunter.com", "enabled": True},
        {"name": "hostingdiscussion", "base_url": "https://hostingdiscussion.com", "enabled": True},
    ]
    
    for source in default_sources:
        existing = db.sources.find_one({"name": source["name"]})
        if not existing:
            from datetime import datetime
            source["created_at"] = datetime.utcnow()
            source["updated_at"] = datetime.utcnow()
            db.sources.insert_one(source)
            print(f"Created source: {source['name']}")
