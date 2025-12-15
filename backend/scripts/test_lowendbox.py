"""Test LowEndBox adapter directly."""
from app.adapters.lowendbox import LowEndBoxAdapter

adapter = LowEndBoxAdapter(
    base_url="https://lowendbox.com",
    user_agent="DealBro/1.0",
    rate_limit=30
)

print("Discovering LowEndBox threads...")
threads = list(adapter.discover())
print(f"\nDiscovered {len(threads)} threads from LowEndBox:")
for i, t in enumerate(threads[:10], 1):
    print(f"{i}. {t.title[:80]}")
