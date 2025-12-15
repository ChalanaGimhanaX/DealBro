import pytest
from app.adapters.utils import (
    extract_domain,
    normalize_price,
    extract_currency,
    extract_billing_period,
    normalize_monthly_price,
    extract_ram_mb,
    extract_storage_gb,
    extract_bandwidth_gb,
)


class TestUtilityFunctions:
    """Test adapter utility functions."""

    def test_extract_domain(self):
        """Test domain extraction from URLs."""
        assert extract_domain("https://example.com/order") == "example.com"
        assert extract_domain("https://www.example.com/order") == "example.com"
        assert extract_domain("http://subdomain.example.com") == "subdomain.example.com"
        assert extract_domain("example.com") == "example.com"
        assert extract_domain("") is None

    def test_normalize_price(self):
        """Test price normalization."""
        assert normalize_price("$9.99") == 9.99
        assert normalize_price("0.99 EUR") == 0.99
        assert normalize_price("Free") == 0.0
        assert normalize_price("free trial") == 0.0
        assert normalize_price("123") == 123.0
        assert normalize_price("invalid") is None

    def test_extract_currency(self):
        """Test currency extraction."""
        assert extract_currency("$9.99") == "USD"
        assert extract_currency("€10.00") == "EUR"
        assert extract_currency("£5.00") == "GBP"
        assert extract_currency("9.99 EUR/mo") == "EUR"
        assert extract_currency("9.99 usd") == "USD"
        assert extract_currency("9.99") == "USD"  # Default

    def test_extract_billing_period(self):
        """Test billing period extraction."""
        assert extract_billing_period("$9.99/mo") == "month"
        assert extract_billing_period("$99/year") == "year"
        assert extract_billing_period("monthly") == "month"
        assert extract_billing_period("yearly") == "year"
        assert extract_billing_period("annually") == "year"
        assert extract_billing_period("one-time") == "one_time"
        assert extract_billing_period("lifetime") == "one_time"
        assert extract_billing_period("per month") == "month"

    def test_normalize_monthly_price(self):
        """Test monthly price normalization."""
        assert normalize_monthly_price(12.0, "month") == 12.0
        assert normalize_monthly_price(120.0, "year") == 10.0
        assert normalize_monthly_price(100.0, "one_time") is None
        assert normalize_monthly_price(None, "month") is None

    def test_extract_ram_mb(self):
        """Test RAM extraction."""
        assert extract_ram_mb("2GB RAM") == 2048
        assert extract_ram_mb("512MB") == 512
        assert extract_ram_mb("1 GB") == 1024
        assert extract_ram_mb("4GB memory") == 4096
        assert extract_ram_mb("no ram mentioned") is None

    def test_extract_storage_gb(self):
        """Test storage extraction."""
        assert extract_storage_gb("50GB SSD") == 50
        assert extract_storage_gb("1TB HDD") == 1024
        assert extract_storage_gb("500 GB") == 500
        assert extract_storage_gb("2TB storage") == 2048
        assert extract_storage_gb("no storage") is None

    def test_extract_bandwidth_gb(self):
        """Test bandwidth extraction."""
        assert extract_bandwidth_gb("1TB bandwidth") == 1024
        assert extract_bandwidth_gb("500GB") == 500
        assert extract_bandwidth_gb("unlimited") == -1
        assert extract_bandwidth_gb("Unlimited bandwidth") == -1
        assert extract_bandwidth_gb("no bandwidth") is None
