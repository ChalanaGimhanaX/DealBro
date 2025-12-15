import pytest
from app.adapters.lowendtalk import LowEndTalkAdapter
from tests.fixtures.lowendtalk_samples import (
    LOWENDTALK_THREAD_HTML,
    LOWENDTALK_RSS_FEED
)


class TestLowEndTalkAdapter:
    """Test LowEndTalk adapter with fixtures."""

    def test_parse_thread_basic(self):
        """Test parsing a basic LET thread."""
        adapter = LowEndTalkAdapter(
            base_url="https://lowendtalk.com",
            user_agent="Test/1.0"
        )
        
        url = "https://lowendtalk.com/discussion/185000/vps"
        post, items = adapter.parse_thread(
            LOWENDTALK_THREAD_HTML,
            url,
            "vps"
        )
        
        # Verify post data
        assert post.title == "VPS $3/month - 1GB RAM, KVM"
        assert post.author == "VPSProvider"
        assert post.canonical_url == url
        assert post.category == "vps"
        
        # Verify deal items
        assert len(items) >= 1
        
        primary_item = items[0]
        assert primary_item.price_amount == 3.00
        assert primary_item.price_currency == "USD"
        assert primary_item.billing_period == "month"
        assert primary_item.ram_mb == 1024  # 1GB
        assert primary_item.storage_gb == 25
        assert primary_item.order_url == "https://vpsprovider.com/order"

    def test_extract_thread_id(self):
        """Test extracting thread ID from LET URL."""
        adapter = LowEndTalkAdapter(
            base_url="https://lowendtalk.com",
            user_agent="Test/1.0"
        )
        
        url = "https://lowendtalk.com/discussion/185000/vps-offer"
        thread_id = adapter._extract_thread_id(url)
        
        assert thread_id == "185000"

    def test_categorize_from_title(self):
        """Test auto-categorization from title."""
        adapter = LowEndTalkAdapter(
            base_url="https://lowendtalk.com",
            user_agent="Test/1.0"
        )
        
        assert adapter._categorize_from_title("VPS Offer - KVM") == "vps"
        assert adapter._categorize_from_title("Shared Hosting Deal") == "shared"
        assert adapter._categorize_from_title("Dedicated Server") == "dedicated"
        assert adapter._categorize_from_title("Cloud VPS") == "cloud"
        assert adapter._categorize_from_title("Reseller Hosting") == "reseller"
        assert adapter._categorize_from_title("Random Offer") == "other"
