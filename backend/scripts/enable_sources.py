"""Enable webhostingtalk, serverhunter, and hostingdiscussion sources."""
from pymongo import MongoClient
from app.core.config import settings

def main():
    client = MongoClient(settings.mongodb_url)
    db = client.dealbro
    
    result = db.sources.update_many(
        {"name": {"$in": ["webhostingtalk", "serverhunter", "hostingdiscussion"]}},
        {"$set": {"enabled": True}}
    )
    
    print(f"Enabled {result.modified_count} sources")
    
    # List all sources
    sources = list(db.sources.find({}, {"name": 1, "enabled": 1}))
    print("\nAll sources:")
    for source in sources:
        status = "✓" if source.get("enabled") else "✗"
        print(f"  {status} {source['name']}")

if __name__ == "__main__":
    main()
