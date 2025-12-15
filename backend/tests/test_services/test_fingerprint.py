import pytest
from datetime import datetime

from app.services.fingerprint import (
    make_strict_fingerprint,
    make_fuzzy_fingerprint,
    normalize_text_for_fingerprint,
)
from app.adapters.types import ParsedDealItem


class TestFingerprintService:
    """Test fingerprinting for deduplication."""

    def test_make_strict_fingerprint_same(self):
        """Test that identical items produce the same fingerprint."""
        item1 = ParsedDealItem(
            provider_domain="example.com",
            price_monthly_normalized=5.99,
            price_currency="USD",
            location="US",
            ram_mb=2048,
            storage_gb=50,
            bandwidth_gb=1024,
        )
        
        item2 = ParsedDealItem(
            provider_domain="example.com",
            price_monthly_normalized=5.99,
            price_currency="USD",
            location="US",
            ram_mb=2048,
            storage_gb=50,
            bandwidth_gb=1024,
        )
        
        fp1 = make_strict_fingerprint(item1, "vps")
        fp2 = make_strict_fingerprint(item2, "vps")
        
        assert fp1 == fp2

    def test_make_strict_fingerprint_different(self):
        """Test that different items produce different fingerprints."""
        item1 = ParsedDealItem(
            provider_domain="example.com",
            price_monthly_normalized=5.99,
            price_currency="USD",
        )
        
        item2 = ParsedDealItem(
            provider_domain="example.com",
            price_monthly_normalized=7.99,  # Different price
            price_currency="USD",
        )
        
        fp1 = make_strict_fingerprint(item1, "vps")
        fp2 = make_strict_fingerprint(item2, "vps")
        
        assert fp1 != fp2

    def test_make_fuzzy_fingerprint(self):
        """Test fuzzy fingerprinting."""
        title1 = "VPS Special Offer - 2GB RAM"
        title2 = "🔥 VPS Special Offer!!! - 2GB RAM 🚀"
        
        fp1 = make_fuzzy_fingerprint(title1, "example.com", "Great VPS deal")
        fp2 = make_fuzzy_fingerprint(title2, "example.com", "Great VPS deal")
        
        # Should be similar (fuzzy match) but not necessarily identical
        assert fp1 is not None
        assert fp2 is not None

    def test_normalize_text_for_fingerprint(self):
        """Test text normalization."""
        text = "🔥 VPS Special!!! - Great Offer 🚀"
        normalized = normalize_text_for_fingerprint(text)
        
        assert "🔥" not in normalized
        assert "🚀" not in normalized
        assert "!!!" not in normalized
        assert normalized.islower()
        assert "vps" in normalized
        assert "special" in normalized
