"""
Sample HTML fixture for HostingDiscussion forum thread.

This is a simplified version - real fixtures should be saved from actual scrapes.
"""

HOSTINGDISCUSSION_THREAD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>VPS Offer - Great Deal</title>
</head>
<body>
    <div class="p-title">
        <h1 class="p-title-value">VPS Special - 2GB RAM, 50GB SSD</h1>
    </div>
    
    <article class="message">
        <div class="message-name">
            <a href="/members/provider123.456/">ProviderCompany</a>
        </div>
        
        <time datetime="2025-01-15T10:30:00+00:00">Jan 15, 2025 at 10:30 AM</time>
        
        <div class="message-body">
            <div class="bbWrapper">
                <p>We're offering an amazing VPS deal!</p>
                
                <p><strong>Specifications:</strong></p>
                <ul>
                    <li>2GB RAM</li>
                    <li>50GB SSD Storage</li>
                    <li>2TB Bandwidth</li>
                    <li>Location: US (New York)</li>
                </ul>
                
                <p><strong>Price: $5.99 USD/month</strong></p>
                
                <p><a href="https://provider.com/order">Order Now</a></p>
            </div>
        </div>
    </article>
</body>
</html>
"""

HOSTINGDISCUSSION_FORUM_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>VPS Offers</title>
</head>
<body>
    <div class="structItem structItem--thread">
        <div class="structItem-title">
            <a href="/threads/vps-special-2gb-ram.123456/">VPS Special - 2GB RAM, 50GB SSD</a>
        </div>
    </div>
    
    <div class="structItem structItem--thread">
        <div class="structItem-title">
            <a href="/threads/dedicated-server-offer.123457/">Dedicated Server Offer</a>
        </div>
    </div>
</body>
</html>
"""
