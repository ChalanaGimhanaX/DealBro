"""Reset DealBro MongoDB data.

- Clears ONLY deal-related collections (posts/items/fingerprints).
- Ensures default sources exist (upsert) so the scheduler can run.

Uses backend settings (.env) for Mongo connection.
"""

import sys
sys.path.insert(0, 'C:/Users/chala/Documents/Projects/DealBro/backend')

from datetime import datetime

from pymongo import MongoClient

from app.core.config import settings


def main() -> None:
    client = MongoClient(settings.mongodb_url)
    db = client[settings.database_name]

    print(f"Connecting to MongoDB database: {settings.database_name}")
    print("Clearing deal collections...")

    db.deal_posts.delete_many({})
    db.deal_items.delete_many({})
    db.deal_fingerprints.delete_many({})

    print("Ensuring sources...")
    default_sources = [
        {"name": "lowendtalk", "base_url": "https://lowendtalk.com", "enabled": True},
        {"name": "lowendbox", "base_url": "https://lowendbox.com", "enabled": True},
        {"name": "webhostingtalk", "base_url": "https://www.webhostingtalk.com", "enabled": True},
        {"name": "serverhunter", "base_url": "https://www.serverhunter.com", "enabled": True},
        {"name": "hostingdiscussion", "base_url": "https://hostingdiscussion.com", "enabled": True},
    ]

    now = datetime.utcnow()
    for source in default_sources:
        existing = db.sources.find_one({"name": source["name"]})
        if existing:
            db.sources.update_one(
                {"_id": existing["_id"]},
                {
                    "$set": {
                        "base_url": source["base_url"],
                        "enabled": source["enabled"],
                        "updated_at": now,
                    },
                    "$setOnInsert": {"created_at": now},
                },
            )
            print(f"  Updated: {source['name']}")
        else:
            source_doc = {
                **source,
                "created_at": now,
                "updated_at": now,
            }
            db.sources.insert_one(source_doc)
            print(f"  Added: {source['name']}")

    print("\nDatabase cleanup complete!")
    print(f"Sources: {db.sources.count_documents({})}")
    print(f"Deal Posts: {db.deal_posts.count_documents({})}")
    print(f"Deal Items: {db.deal_items.count_documents({})}")


if __name__ == "__main__":
    main()
