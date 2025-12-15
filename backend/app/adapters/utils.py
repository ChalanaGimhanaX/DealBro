import re
from urllib.parse import urlparse, urljoin
from typing import Optional


def extract_domain(url: str) -> Optional[str]:
    """Extract domain from URL."""
    if not url:
        return None
    try:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path.split('/')[0]
        # Remove www. prefix
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain or None
    except Exception:
        return None


def normalize_price(price_str: str) -> Optional[float]:
    """
    Extract numeric price from string.
    
    Examples:
        "$9.99" -> 9.99
        "0.99 EUR" -> 0.99
        "Free" -> 0.0
    """
    if not price_str:
        return None
    
    # Handle "free" cases
    if re.search(r'\bfree\b', price_str, re.IGNORECASE):
        return 0.0
    
    # Extract numeric value
    match = re.search(r'(\d+(?:[.,]\d+)?)', price_str.replace(',', ''))
    if match:
        try:
            return float(match.group(1).replace(',', '.'))
        except ValueError:
            return None
    return None


def extract_currency(price_str: str) -> Optional[str]:
    """
    Extract currency from price string.
    
    Examples:
        "$9.99" -> "USD"
        "0.99 EUR/mo" -> "EUR"
        "£5.00" -> "GBP"
    """
    if not price_str:
        return None
    
    # Map of currency symbols to codes
    currency_map = {
        '$': 'USD',
        '€': 'EUR',
        '£': 'GBP',
        '¥': 'JPY',
        '₹': 'INR',
    }
    
    # Check for symbol
    for symbol, code in currency_map.items():
        if symbol in price_str:
            return code
    
    # Check for currency codes
    match = re.search(r'\b(USD|EUR|GBP|CAD|AUD|JPY|INR|CNY|SGD)\b', price_str, re.IGNORECASE)
    if match:
        return match.group(1).upper()
    
    return 'USD'  # Default to USD


def extract_billing_period(text: str) -> Optional[str]:
    """
    Extract billing period from text.
    
    Returns: "month", "year", or "one_time"
    """
    if not text:
        return None
    
    text_lower = text.lower()
    
    # Check for monthly
    if re.search(r'/mo\b|/month\b|monthly|per month', text_lower):
        return 'month'
    
    # Check for yearly
    if re.search(r'/yr\b|/year\b|yearly|annually|per year|/annum', text_lower):
        return 'year'
    
    # Check for one-time
    if re.search(r'one.?time|lifetime|once', text_lower):
        return 'one_time'
    
    return 'month'  # Default to monthly


def normalize_monthly_price(amount: Optional[float], period: Optional[str]) -> Optional[float]:
    """Convert price to monthly equivalent."""
    if amount is None or period is None:
        return None
    
    if period == 'month':
        return amount
    elif period == 'year':
        return round(amount / 12, 2)
    elif period == 'one_time':
        return None  # Can't normalize one-time to monthly
    
    return None


def extract_ram_mb(text: str) -> Optional[int]:
    """
    Extract RAM in MB from text.
    
    Examples:
        "2GB RAM" -> 2048
        "512MB" -> 512
        "1 GB" -> 1024
    """
    if not text:
        return None
    
    # Look for GB
    match = re.search(r'(\d+(?:\.\d+)?)\s*GB', text, re.IGNORECASE)
    if match:
        return int(float(match.group(1)) * 1024)
    
    # Look for MB
    match = re.search(r'(\d+)\s*MB', text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    
    return None


def extract_storage_gb(text: str) -> Optional[int]:
    """
    Extract storage in GB from text.
    
    Examples:
        "50GB SSD" -> 50
        "1TB HDD" -> 1024
        "500 GB" -> 500
    """
    if not text:
        return None

    storage_kw = r"(?:ssd|hdd|nvme|disk|storage|space)"
    bandwidth_kw = r"(?:bandwidth|bw|transfer|traffic|data)"
    ram_kw = r"(?:ram|memory)"

    # Prefer matches that mention storage keywords to avoid confusing bandwidth/RAM.
    for pattern in [
        rf"(\d+(?:\.\d+)?)\s*(TB|GB)\s*{storage_kw}\b",
        rf"{storage_kw}\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*(TB|GB)\b",
    ]:
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            continue
        number = float(match.group(1))
        unit = match.group(2).upper()
        return int(number * 1024) if unit == "TB" else int(number)

    # Fallback: first TB/GB number that isn't clearly bandwidth or RAM.
    for match in re.finditer(r"(\d+(?:\.\d+)?)\s*(TB|GB)\b", text, re.IGNORECASE):
        window = text[max(0, match.start() - 30) : min(len(text), match.end() + 30)].lower()
        if re.search(bandwidth_kw, window):
            continue
        if re.search(ram_kw, window):
            continue
        number = float(match.group(1))
        unit = match.group(2).upper()
        return int(number * 1024) if unit == "TB" else int(number)

    return None


def extract_bandwidth_gb(text: str) -> Optional[int]:
    """Extract bandwidth in GB from text."""
    if not text:
        return None
    
    # Check for unlimited
    if re.search(r'\bunlimited\b', text, re.IGNORECASE):
        return -1  # Use -1 to represent unlimited
    
    storage_kw = r"(?:ssd|hdd|nvme|disk|storage|space)"
    bandwidth_kw = r"(?:bandwidth|bw|transfer|traffic|data)"
    ram_kw = r"(?:ram|memory)"

    # Prefer matches that mention bandwidth keywords to avoid confusing storage/RAM.
    for pattern in [
        rf"(\d+(?:\.\d+)?)\s*(TB|GB)\s*{bandwidth_kw}\b",
        rf"{bandwidth_kw}\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*(TB|GB)\b",
    ]:
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            continue
        number = float(match.group(1))
        unit = match.group(2).upper()
        return int(number * 1024) if unit == "TB" else int(number)

    # Fallback: first TB/GB number that isn't clearly storage or RAM.
    for match in re.finditer(r"(\d+(?:\.\d+)?)\s*(TB|GB)\b", text, re.IGNORECASE):
        window = text[max(0, match.start() - 30) : min(len(text), match.end() + 30)].lower()
        if re.search(storage_kw, window):
            continue
        if re.search(ram_kw, window):
            continue
        number = float(match.group(1))
        unit = match.group(2).upper()
        return int(number * 1024) if unit == "TB" else int(number)

    return None


def clean_text(text: str) -> str:
    """Clean and normalize text."""
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove emojis (basic approach)
    text = re.sub(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', '', text)
    
    return text.strip()


def make_absolute_url(url: str, base_url: str) -> str:
    """Convert relative URL to absolute."""
    if not url:
        return url
    
    if url.startswith('http://') or url.startswith('https://'):
        return url
    
    return urljoin(base_url, url)
