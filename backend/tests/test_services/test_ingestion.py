from datetime import datetime

from bson import ObjectId

from app.services.ingestion import IngestionService
from app.adapters.types import ParsedDealPost, ParsedDealItem


class TestIngestionService:
    """Test ingestion service."""

    def test_already_ingested(self, mongo_db, sample_source):
        """Test checking if a post was already ingested."""
        service = IngestionService(db=mongo_db)
        
        # Create a post
        post = ParsedDealPost(
            canonical_url="https://example.com/thread/123",
            title="Test Deal",
            author="TestAuthor",
            posted_at=datetime.now(),
            category="vps",
            raw_text="Test content",
        )
        
        # First check - should be False
        assert service.already_ingested(sample_source, post.canonical_url) is False
        
        # Insert the post
        post_id = service.insert_deal_post(sample_source, post, "<html></html>")
        assert post_id is not None
        
        # Second check - should be True
        assert service.already_ingested(sample_source, post.canonical_url) is True

    def test_insert_deal_post(self, mongo_db, sample_source):
        """Test inserting a deal post."""
        service = IngestionService(db=mongo_db)
        
        post = ParsedDealPost(
            canonical_url="https://example.com/thread/456",
            title="VPS Deal",
            author="Provider",
            posted_at=datetime.now(),
            category="vps",
            raw_text="Great VPS offer",
            source_thread_id="456",
        )
        
        post_id = service.insert_deal_post(sample_source, post, "<html>content</html>")
        
        assert post_id is not None
        
        # Verify it was inserted
        db_post = mongo_db.deal_posts.find_one({"_id": ObjectId(post_id)})
        assert db_post is not None
        assert db_post["title"] == "VPS Deal"
        assert db_post["author"] == "Provider"
        assert db_post["category"] == "vps"

    def test_insert_deal_item(self, mongo_db, sample_source):
        """Test inserting a deal item."""
        service = IngestionService(db=mongo_db)
        
        # Create a post first
        post = ParsedDealPost(
            canonical_url="https://example.com/thread/789",
            title="Test",
            author="Test",
            posted_at=datetime.now(),
            category="vps",
            raw_text="Test",
        )
        post_id = service.insert_deal_post(sample_source, post, "<html></html>")
        
        # Create an item
        item = ParsedDealItem(
            provider_domain="example.com",
            price_amount=9.99,
            price_currency="USD",
            billing_period="month",
            price_monthly_normalized=9.99,
            ram_mb=2048,
            storage_gb=50,
            is_primary=True,
        )
        
        item_id = service.insert_deal_item(post_id, item)
        
        assert item_id is not None
        
        # Verify it was inserted
        db_item = mongo_db.deal_items.find_one({"_id": ObjectId(item_id)})
        assert db_item is not None
        assert db_item["price_amount"] == 9.99
        assert db_item["ram_mb"] == 2048

    def test_ingest_thread_with_duplicate(self, mongo_db, sample_source):
        """Test ingesting a thread that's a duplicate."""
        service = IngestionService(db=mongo_db)
        
        # Create first post
        post1 = ParsedDealPost(
            canonical_url="https://example.com/thread/111",
            title="VPS Offer",
            author="Provider1",
            posted_at=datetime.now(),
            category="vps",
            raw_text="Great offer",
        )
        
        item1 = ParsedDealItem(
            provider_domain="provider1.com",
            price_amount=5.99,
            price_currency="USD",
            billing_period="month",
            price_monthly_normalized=5.99,
            ram_mb=1024,
            storage_gb=25,
            is_primary=True,
        )
        
        # Ingest first post
        post_id1 = service.ingest_thread(sample_source, post1, [item1], "<html>1</html>")
        assert post_id1 is not None
        
        # Create second post with same specs (duplicate)
        post2 = ParsedDealPost(
            canonical_url="https://example.com/thread/222",  # Different URL
            title="Another VPS Offer",
            author="Provider2",
            posted_at=datetime.now(),
            category="vps",
            raw_text="Another great offer",
        )
        
        item2 = ParsedDealItem(
            provider_domain="provider1.com",  # Same provider
            price_amount=5.99,  # Same price
            price_currency="USD",
            billing_period="month",
            price_monthly_normalized=5.99,
            ram_mb=1024,  # Same specs
            storage_gb=25,
            is_primary=True,
        )
        
        # Ingest second post - should be marked as duplicate
        post_id2 = service.ingest_thread(sample_source, post2, [item2], "<html>2</html>")
        assert post_id2 is not None
        
        # Verify second post is marked as duplicate
        db_post2 = mongo_db.deal_posts.find_one({"_id": ObjectId(post_id2)})
        assert db_post2 is not None
        assert db_post2["is_duplicate"] is True
