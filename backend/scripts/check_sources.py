"""Check enabled sources."""
from app.core.database import get_sync_db

db = get_sync_db()
sources = list(db.sources.find({}))

print("All sources:")
for s in sources:
    status = "ENABLED" if s.get("enabled") else "DISABLED"
    print(f"  {s['name']:20} {status:10} {s['base_url']}")

print(f"\nTotal enabled: {sum(1 for s in sources if s.get('enabled'))}")
