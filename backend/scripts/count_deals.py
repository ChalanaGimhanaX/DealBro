"""Check deal counts by source."""
import sys
sys.path.insert(0, 'C:/Users/chala/Documents/Projects/DealBro/backend')
from pymongo import MongoClient
from app.core.config import settings

client = MongoClient(settings.mongodb_url)
db = client.dealbro

# Count by source
pipeline = [{'$group': {'_id': '$source_name', 'count': {'$sum': 1}}}]
results = list(db.deal_posts.aggregate(pipeline))

print('\nDeals by source:')
for r in sorted(results, key=lambda x: x['count'], reverse=True):
    print(f"  {r['_id']}: {r['count']}")

print(f"\nTotal: {db.deal_posts.count_documents({})}")
