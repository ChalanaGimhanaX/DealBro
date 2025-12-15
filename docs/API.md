# DealBro API Documentation

## Base URL

```
http://localhost:8000/api
```

## Authentication

Currently no authentication required. Future versions may implement API keys.

## Endpoints

### Health Check

#### GET /api/health

Check API health status.

**Response**

```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T10:30:00",
  "database": "healthy",
  "version": "1.0.0"
}
```

---

### Deals

#### GET /api/deals

Get paginated list of deals with filters.

**Query Parameters**

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `page` | integer | Page number | 1 |
| `page_size` | integer | Items per page (1-100) | 20 |
| `category` | string | Filter by category | - |
| `min_price` | float | Minimum monthly price | - |
| `max_price` | float | Maximum monthly price | - |
| `billing_period` | string | month, year, one_time | - |
| `currency` | string | Currency code (USD, EUR, etc.) | - |
| `location` | string | Location/region | - |
| `source_id` | integer | Filter by source | - |
| `search` | string | Search in title and text | - |
| `include_duplicates` | boolean | Include duplicate deals | false |
| `order_by` | string | posted_at, created_at, title | posted_at |

**Response**

```json
{
  "items": [
    {
      "id": 1,
      "source_id": 1,
      "canonical_url": "https://forum.com/thread/123",
      "title": "VPS Special - 2GB RAM",
      "author": "ProviderName",
      "posted_at": "2025-01-15T10:00:00",
      "category": "vps",
      "is_duplicate": false,
      "source": {
        "id": 1,
        "name": "hostingdiscussion",
        "base_url": "https://hostingdiscussion.com",
        "enabled": true
      },
      "deal_items": [
        {
          "id": 1,
          "provider_domain": "provider.com",
          "price_amount": 5.99,
          "price_currency": "USD",
          "billing_period": "month",
          "price_monthly_normalized": 5.99,
          "ram_mb": 2048,
          "storage_gb": 50,
          "bandwidth_gb": 1024,
          "order_url": "https://provider.com/order",
          "is_primary": true
        }
      ]
    }
  ],
  "total": 150,
  "page": 1,
  "page_size": 20,
  "pages": 8
}
```

#### GET /api/deals/{deal_id}

Get a specific deal by ID.

**Response**

Returns a single deal object with full details including raw_text and raw_html.

---

### Sources

#### GET /api/sources

Get list of all sources.

**Response**

```json
[
  {
    "id": 1,
    "name": "hostingdiscussion",
    "base_url": "https://hostingdiscussion.com",
    "enabled": true,
    "created_at": "2025-01-15T10:00:00",
    "updated_at": "2025-01-15T10:00:00"
  }
]
```

#### GET /api/sources/{source_id}

Get a specific source by ID.

---

### Metadata

#### GET /api/categories

Get list of available categories.

**Response**

```json
{
  "categories": ["shared", "reseller", "vps", "dedicated", "cloud", "colo", "other"]
}
```

#### GET /api/currencies

Get list of available currencies.

**Response**

```json
{
  "currencies": ["USD", "EUR", "GBP", "CAD"]
}
```

#### GET /api/stats

Get statistics about deals.

**Response**

```json
{
  "total_deals": 500,
  "total_active": 450,
  "by_category": {
    "vps": 200,
    "shared": 150,
    "dedicated": 100
  },
  "by_source": {
    "hostingdiscussion": 250,
    "lowendtalk": 200
  }
}
```

---

## Error Responses

All endpoints may return error responses:

**404 Not Found**

```json
{
  "detail": "Deal not found"
}
```

**422 Validation Error**

```json
{
  "detail": [
    {
      "loc": ["query", "page"],
      "msg": "value is not a valid integer",
      "type": "type_error.integer"
    }
  ]
}
```

**500 Internal Server Error**

```json
{
  "detail": "Internal server error"
}
```

---

## Rate Limiting

Currently no rate limiting. Future versions may implement rate limits per IP.

## Examples

### Get VPS deals under $10/month

```bash
curl "http://localhost:8000/api/deals?category=vps&max_price=10"
```

### Search for specific provider

```bash
curl "http://localhost:8000/api/deals?search=ProviderName"
```

### Get deals from specific source

```bash
curl "http://localhost:8000/api/deals?source_id=1"
```

### Filter by multiple criteria

```bash
curl "http://localhost:8000/api/deals?category=vps&min_price=5&max_price=15&currency=USD&billing_period=month"
```
