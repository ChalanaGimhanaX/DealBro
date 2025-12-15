"""Disable broken sources temporarily."""
from datetime import datetime
from app.core.database import get_sync_db

db = get_sync_db()

# Disable sources with 404s
broken_sources = ['webhostingtalk', 'serverhunter', 'hostingdiscussion']

for source_name in broken_sources:
    db.sources.update_one(
        {'name': source_name},
        {'$set': {'enabled': False, 'updated_at': datetime.utcnow()}}
    )
    print(f"Disabled: {source_name}")

print("\nOnly LowEndTalk and LowEndBox are now enabled.")
