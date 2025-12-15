import pytest
from app.adapters.hostingdiscussion import HostingDiscussionAdapter
from tests.fixtures.hostingdiscussion_samples import (
    HOSTINGDISCUSSION_THREAD_HTML,
    HOSTINGDISCUSSION_FORUM_HTML
)


class TestHostingDiscussionAdapter:
    """Test HostingDiscussion adapter with fixtures."""

    def test_parse_thread_basic(self):
        """Test parsing a basic thread with price info."""
        adapter = HostingDiscussionAdapter(
            base_url="https://hostingdiscussion.com",
            user_agent="Test/1.0"
        )
        
        url = "https://hostingdiscussion.com/threads/vps-special.123456/"
        post, items = adapter.parse_thread(
            HOSTINGDISCUSSION_THREAD_HTML,
            url,
            "vps"
        )
        
        # Verify post data
        assert post.title == "VPS Special - 2GB RAM, 50GB SSD"
        assert post.author == "ProviderCompany"
        assert post.canonical_url == url
        assert post.category == "vps"
        assert "2GB RAM" in post.raw_text
        
        # Verify deal items
        assert len(items) >= 1
        
        primary_item = items[0]
        assert primary_item.is_primary is True
        assert primary_item.price_amount == 5.99
        assert primary_item.price_currency == "USD"
        assert primary_item.billing_period == "month"
        assert primary_item.price_monthly_normalized == 5.99
        assert primary_item.ram_mb == 2048  # 2GB = 2048MB
        assert primary_item.storage_gb == 50
        assert primary_item.bandwidth_gb == 2048  # 2TB = 2048GB
        assert primary_item.order_url == "https://provider.com/order"

    def test_extract_thread_id(self):
        """Test extracting thread ID from URL."""
        adapter = HostingDiscussionAdapter(
            base_url="https://hostingdiscussion.com",
            user_agent="Test/1.0"
        )
        
        url = "https://hostingdiscussion.com/threads/vps-special.123456/"
        thread_id = adapter._extract_thread_id(url)
        
        assert thread_id == "123456"

    def test_parse_multiple_prices(self):
        """Test parsing thread with multiple price points."""
        html = """
        <html>
        <body>
            <h1 class="p-title-value">VPS Plans</h1>
            <div class="message-name"><a>Provider</a></div>
            <time datetime="2025-01-15T10:00:00+00:00"></time>
            <div class="message-body">
                <div class="bbWrapper">
                    <p>Plan 1: Price: $3.99/mo - 1GB RAM, 20GB SSD</p>
                    <p>Plan 2: Price: $7.99/mo - 2GB RAM, 40GB SSD</p>
                    <a href="https://provider.com/order">Order</a>
                </div>
            </div>
        </body>
        </html>
        """
        
        adapter = HostingDiscussionAdapter(
            base_url="https://hostingdiscussion.com",
            user_agent="Test/1.0"
        )
        
        post, items = adapter.parse_thread(html, "https://test.com/thread", "vps")
        
        # Should extract both prices
        assert len(items) >= 2
        assert items[0].price_amount == 3.99
        assert items[1].price_amount == 7.99
        assert items[0].is_primary is True
        assert items[1].is_primary is False
