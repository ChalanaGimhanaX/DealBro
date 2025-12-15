# DealBro - Hosting Deals Aggregator

A comprehensive deals aggregator that pulls hosting offers from multiple forum sources.

## Features

- **Multi-Source Ingestion**: Scrapes deals from HostingDiscussion, LowEndTalk, and WebHostingTalk
- **Smart Parsing**: Extracts structured deal items from forum posts
- **Intelligent Deduplication**: Prevents duplicate deals across sources
- **Advanced Filtering**: Filter by price, billing period, category, currency, and location
- **Fixture-Based Testing**: Ensures parser reliability with frozen test cases
- **Compliant Scraping**: Respects robots.txt, rate limits, and site policies

## Architecture

```
DealBro/
├── backend/              # FastAPI application
│   ├── app/
│   │   ├── adapters/    # Source-specific parsers
│   │   ├── api/         # REST endpoints
│   │   ├── core/        # Config, database
│   │   ├── models/      # SQLAlchemy models
│   │   └── services/    # Business logic
│   └── alembic/         # Database migrations
├── frontend/            # Next.js application
├── fixtures/            # Test data (HTML/RSS samples)
└── tests/               # Test suites
```

## Tech Stack

- **Backend**: FastAPI, MongoDB (Motor/PyMongo)
- **Frontend**: Next.js 14, React, TailwindCSS
- **Ingestion**: APScheduler, BeautifulSoup4, feedparser
- **Testing**: pytest, fixtures

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- MongoDB 6+ (or MongoDB Atlas)

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure database
cp .env.example .env
# Edit .env with your MongoDB connection string

# Start the server
python -m uvicorn app.main:app --reload
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

## Usage

### Running the Ingestion Service

```bash
cd backend
python -m app.ingestion.scheduler
```

### API Endpoints

- `GET /api/deals` - List all deals with filters
- `GET /api/deals/{id}` - Get specific deal
- `GET /api/sources` - List all sources
- `GET /api/health` - Health check

### Testing

```bash
cd backend
python -m pytest
```

## Configuration

Edit `backend/.env`:

```
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=dealbro
INGESTION_INTERVAL_MINUTES=30
LOG_LEVEL=INFO
```

## Compliance

- Respects `robots.txt`
- Configurable rate limiting per source
- Custom User-Agent identifying the bot
- Graceful error handling and backoff

## License

MIT
