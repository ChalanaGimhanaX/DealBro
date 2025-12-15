# Development Guide

## Project Structure

```
DealBro/
├── backend/                    # Python FastAPI backend
│   ├── alembic/               # Database migrations
│   │   └── versions/          # Migration files
│   ├── app/
│   │   ├── adapters/          # Source-specific scrapers
│   │   │   ├── base.py        # Base adapter interface
│   │   │   ├── hostingdiscussion.py
│   │   │   ├── lowendtalk.py
│   │   │   ├── types.py       # Data classes
│   │   │   └── utils.py       # Helper functions
│   │   ├── api/               # REST endpoints
│   │   │   ├── deals.py
│   │   │   └── health.py
│   │   ├── core/              # Core configuration
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   └── logging.py
│   │   ├── ingestion/         # Ingestion service
│   │   │   └── scheduler.py
│   │   ├── models/            # SQLAlchemy models
│   │   │   ├── deal_item.py
│   │   │   ├── deal_post.py
│   │   │   ├── deal_fingerprint.py
│   │   │   ├── enums.py
│   │   │   └── source.py
│   │   ├── repositories/      # Data access layer
│   │   │   └── deal_repository.py
│   │   ├── schemas/           # Pydantic schemas
│   │   │   └── deals.py
│   │   ├── services/          # Business logic
│   │   │   ├── fingerprint.py
│   │   │   └── ingestion.py
│   │   └── main.py            # FastAPI app
│   ├── scripts/               # Utility scripts
│   │   ├── health_check.py
│   │   ├── setup.py
│   │   ├── start.sh
│   │   └── start.bat
│   ├── tests/                 # Test suite
│   │   ├── fixtures/          # Sample HTML/RSS
│   │   ├── test_adapters/
│   │   └── test_services/
│   ├── .env.example
│   ├── alembic.ini
│   ├── pytest.ini
│   └── requirements.txt
├── frontend/                   # Next.js frontend
│   ├── src/
│   │   ├── app/               # App router
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx
│   │   │   └── globals.css
│   │   ├── components/        # React components
│   │   │   ├── DealCard.tsx
│   │   │   ├── DealsFilter.tsx
│   │   │   └── Pagination.tsx
│   │   ├── lib/               # Utilities
│   │   │   └── api.ts
│   │   └── types/             # TypeScript types
│   │       └── index.ts
│   ├── package.json
│   ├── tsconfig.json
│   └── tailwind.config.js
├── docs/                       # Documentation
└── README.md
```

## Adding a New Source Adapter

### 1. Create Adapter Class

Create a new file in `backend/app/adapters/`:

```python
# newsource.py
from app.adapters.base import SourceAdapter
from app.adapters.types import DiscoveredThread, ParsedDealPost, ParsedDealItem

class NewSourceAdapter(SourceAdapter):
    def discover(self) -> Iterable[DiscoveredThread]:
        # Implement discovery logic
        pass
    
    def fetch_thread_html(self, url: str) -> str:
        # Implement fetching logic
        pass
    
    def parse_thread(self, html: str, url: str, category: str):
        # Implement parsing logic
        pass
```

### 2. Register Adapter

Add to `backend/app/adapters/__init__.py`:

```python
from app.adapters.newsource import NewSourceAdapter

def get_adapter_class(source_name: str) -> Type[SourceAdapter]:
    adapters = {
        "hostingdiscussion": HostingDiscussionAdapter,
        "lowendtalk": LowEndTalkAdapter,
        "newsource": NewSourceAdapter,  # Add this
    }
    return adapters.get(source_name)
```

### 3. Add to Database

Insert into sources table:

```sql
INSERT INTO sources (name, base_url, enabled)
VALUES ('newsource', 'https://newsource.com', true);
```

### 4. Create Tests

Create test file in `backend/tests/test_adapters/`:

```python
# test_newsource.py
from app.adapters.newsource import NewSourceAdapter

class TestNewSourceAdapter:
    def test_parse_thread_basic(self):
        # Test with fixture
        pass
```

### 5. Add Fixtures

Save real HTML/RSS samples in `backend/tests/fixtures/newsource_samples.py`.

## Database (MongoDB)

DealBro uses MongoDB. Collections and indexes are created automatically on startup.

- Index definitions: `backend/app/core/database.py` (`create_indexes` / `create_indexes_sync`)
- Default sources seeding: `backend/app/core/database.py` (`init_default_sources` / `init_default_sources_sync`)

## Testing

### Run All Tests

```bash
cd backend
python -m pytest
```

### Run Specific Test File

```bash
python -m pytest tests/test_adapters/test_hostingdiscussion.py
```

### Run with Coverage

```bash
python -m pytest --cov=app --cov-report=html
```

View coverage report at `htmlcov/index.html`.

### Writing Tests

Always use fixtures for HTML/RSS samples:

```python
def test_parser(self):
    from tests.fixtures.samples import SAMPLE_HTML
    
    adapter = MyAdapter("https://example.com", "Test/1.0")
    post, items = adapter.parse_thread(SAMPLE_HTML, "url", "category")
    
    assert post.title == "Expected Title"
    assert len(items) > 0
```

## Adding New API Endpoints

### 1. Define Schema

In `backend/app/schemas/`:

```python
class NewSchema(BaseModel):
    field: str
    
    class Config:
        from_attributes = True
```

### 2. Create Endpoint

In `backend/app/api/`:

```python
@router.get("/new-endpoint", response_model=NewSchema)
async def get_something():
    # Implementation
    return result
```

### 3. Register Router

In `backend/app/main.py`:

```python
from app.api import new_endpoints

app.include_router(new_endpoints.router, prefix="/api", tags=["new"])
```

## Debugging

### Enable Verbose Logging

Edit `.env`:

```
LOG_LEVEL=DEBUG
```

### Test Adapter Manually

```python
from app.adapters.hostingdiscussion import HostingDiscussionAdapter

adapter = HostingDiscussionAdapter(
    base_url="https://hostingdiscussion.com",
    user_agent="Test/1.0"
)

for thread in adapter.discover():
    print(thread)
```

### Check Database

```bash
mongosh "mongodb://localhost:27017/dealbro" --eval "db.deal_posts.find().sort({created_at:-1}).limit(10).toArray()"
```

## Performance Optimization

### Database Indexes

Already created for common queries:
- `deal_posts.posted_at`
- `deal_posts.category`
- `deal_items.price_monthly_normalized`
- `deal_fingerprints.fingerprint`

### Caching

Consider adding Redis for:
- API response caching
- Rate limiting
- Session storage

### Pagination

Always use pagination for large result sets:

```python
deals = query.offset(skip).limit(page_size).all()
```

## Common Issues

### Mongo Connection Failed

Check `MONGODB_URL` in `.env`. Ensure MongoDB is running and reachable.

### Parser Not Extracting Data

Check HTML structure with browser DevTools. Update selectors in adapter.

### Duplicates Not Detected

Verify fingerprint generation. Check that specs are normalized consistently.

### Tests Failing

Ensure fixtures match current HTML structure. Update fixtures when sites change.

## Contributing

1. Create feature branch
2. Write tests for new functionality
3. Ensure all tests pass
4. Update documentation
5. Submit pull request

## Code Style

- Python: Follow PEP 8
- TypeScript: Use Prettier
- Imports: Group by standard library, third-party, local
- Docstrings: Use Google style
