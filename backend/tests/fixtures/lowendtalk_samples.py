"""
Sample RSS/HTML fixtures for LowEndTalk forum.
"""

LOWENDTALK_RSS_FEED = """
<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0">
    <channel>
        <title>LowEndTalk Offers</title>
        <link>https://lowendtalk.com/categories/offers</link>
        <description>Latest offers from LowEndTalk</description>
        
        <item>
            <title>VPS $3/month - 1GB RAM, KVM</title>
            <link>https://lowendtalk.com/discussion/185000/vps-3-month</link>
            <pubDate>Wed, 15 Jan 2025 14:30:00 +0000</pubDate>
            <description>Great VPS deal available</description>
        </item>
        
        <item>
            <title>Shared Hosting - $1/month unlimited</title>
            <link>https://lowendtalk.com/discussion/185001/shared-hosting</link>
            <pubDate>Wed, 15 Jan 2025 12:00:00 +0000</pubDate>
            <description>Unlimited shared hosting</description>
        </item>
    </channel>
</rss>
"""

LOWENDTALK_THREAD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>VPS $3/month - 1GB RAM, KVM</title>
</head>
<body>
    <h1 class="Title">VPS $3/month - 1GB RAM, KVM</h1>
    
    <div class="Author">
        <a href="/profile/seller123">VPSProvider</a>
    </div>
    
    <time datetime="2025-01-15T14:30:00+00:00">January 15, 2025</time>
    
    <div class="Message">
        <p>We have an amazing VPS offer:</p>
        
        <ul>
            <li>1GB RAM</li>
            <li>25GB SSD</li>
            <li>1TB Bandwidth</li>
            <li>KVM Virtualization</li>
            <li>Location: Los Angeles, USA</li>
        </ul>
        
        <p>$3.00 USD/month</p>
        
        <p><a href="https://vpsprovider.com/order">Order here</a></p>
    </div>
</body>
</html>
"""
