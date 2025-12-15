"""Disable serverhunter source."""
from pymongo import MongoClient
from app.core.config import settings

client = MongoClient(settings.mongodb_url)
db = client.dealbro

db.sources.update_one({"name": "serverhunter"}, {"$set": {"enabled": False}})
print("Disabled serverhunter")

sources = list(db.sources.find({}, {"name": 1, "enabled": 1}))
print("\nEnabled sources:")
for s in sources:
    if s.get("enabled"):
        print(f"  ✓ {s['name']}")
