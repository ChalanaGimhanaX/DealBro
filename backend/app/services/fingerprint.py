import hashlib
import re
from typing import Optional

from datasketch import MinHash
from app.adapters.types import ParsedDealItem


def make_strict_fingerprint(
    item: ParsedDealItem,
    category: str
) -> str:
    """
    Create a strict fingerprint for exact duplicate detection.
    
    Based on: provider_domain + category + normalized_price + currency + location + specs
    """
    parts = [
        item.provider_domain or "",
        category or "",
        str(item.price_monthly_normalized or ""),
        item.price_currency or "",
        item.location or "",
        str(item.ram_mb or ""),
        str(item.storage_gb or ""),
        str(item.bandwidth_gb or ""),
    ]
    
    # Join and hash
    fingerprint_str = "|".join(parts).lower()
    return hashlib.sha1(fingerprint_str.encode()).hexdigest()


def make_fuzzy_fingerprint(
    title: str,
    provider_domain: Optional[str],
    raw_text: str
) -> str:
    """
    Create a fuzzy fingerprint for near-duplicate detection.
    
    Uses MinHash on normalized title + provider + first 200 chars of body
    """
    # Normalize text
    normalized_title = normalize_text_for_fingerprint(title)
    normalized_provider = provider_domain.lower() if provider_domain else ""
    normalized_body = normalize_text_for_fingerprint(raw_text[:200])
    
    # Combine
    combined = f"{normalized_provider} {normalized_title} {normalized_body}"
    
    # Create shingles (3-character sequences)
    shingles = set()
    for i in range(len(combined) - 2):
        shingles.add(combined[i:i+3])
    
    # Create MinHash
    minhash = MinHash(num_perm=128)
    for shingle in shingles:
        minhash.update(shingle.encode('utf8'))
    
    # Return hash digest
    return hashlib.sha1(str(minhash.hashvalues).encode()).hexdigest()


def normalize_text_for_fingerprint(text: str) -> str:
    """Normalize text for fingerprinting."""
    if not text:
        return ""
    
    # Lowercase
    text = text.lower()
    
    # Remove emojis
    text = re.sub(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', '', text)
    
    # Remove punctuation
    text = re.sub(r'[^\w\s]', ' ', text)
    
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


def calculate_fuzzy_similarity(hash1: str, hash2: str) -> float:
    """
    Calculate similarity between two fingerprints.
    
    Returns a value between 0 and 1, where 1 is identical.
    
    Note: For MinHash, we'd need to store the actual hash values,
    not just the digest. This is a simplified version using string comparison.
    """
    if hash1 == hash2:
        return 1.0
    
    # Simple hamming distance for demonstration
    if len(hash1) != len(hash2):
        return 0.0
    
    matches = sum(c1 == c2 for c1, c2 in zip(hash1, hash2))
    return matches / len(hash1)
