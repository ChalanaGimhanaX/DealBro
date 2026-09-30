# DealBro — Hosting Deals Aggregator

A full-stack application for collecting hosting offers, extracting structured deal information, and comparing offers through a searchable web interface.

**Stack:** Python · FastAPI · MongoDB · Next.js 14 · React · TypeScript · Tailwind CSS

## Features

- Source-specific adapters for hosting forums and listings.
- Structured offer extraction and fingerprint-based duplicate detection.
- Filtering by price, currency, billing period, category, location, and source.
- Paginated REST API and Next.js interface.
- Parser fixtures and tests for adapters, fingerprinting, and ingestion.

## Architecture

```text
Source adapters → parsing / extraction → deduplication → MongoDB
                                                          ↓
                                                   FastAPI REST API
                                                          ↓
                                                   Next.js frontend
```

The active backend uses MongoDB through Motor/PyMongo. `backend/alembic/` contains legacy SQL migration files and is not part of the current MongoDB setup.

## Local setup

Prerequisites: Python 3.11+, a Node.js version compatible with Next.js 14, and a running MongoDB instance.

```bash
git clone https://github.com/ChalanaGimhanaX/DealBro.git
cd DealBro/backend
python -m venv .venv
```

Activate `.venv\Scripts\Activate.ps1` in PowerShell or `source .venv/bin/activate` on macOS/Linux. Then:

```bash
python -m pip install -r requirements.txt
```

Copy `backend/.env.example` to `backend/.env`. For local MongoDB, use `MONGODB_URL=mongodb://localhost:27017` and `DATABASE_NAME=dealbro`.

```bash
python -m uvicorn app.main:app --reload
```

API: <http://localhost:8000> · Interactive documentation: <http://localhost:8000/docs>

In a second terminal, open the repository's `frontend/` directory:

```bash
npm ci
npm run dev
```

Open <http://localhost:3000>. The frontend defaults to `http://localhost:8000/api`; override `NEXT_PUBLIC_API_URL` in `frontend/.env.local` if needed.

Run the separate ingestion scheduler from `backend/`:

```bash
python -m app.ingestion.scheduler
```

Extraction includes a configurable LLM integration. Supply your own compatible endpoint, model, and key when using that path; no hosted LLM service is included.

## API highlights

| Endpoint | Purpose |
| --- | --- |
| `GET /api/deals` | Search, filter, and paginate offers |
| `GET /api/deals/{deal_id}` | Read an offer |
| `GET /api/sources` | List sources |
| `GET /api/categories` | List categories |
| `GET /api/currencies` | List currencies |
| `GET /api/stats` | Aggregate statistics |
| `GET /api/health` | Health endpoint |

## Development checks

From `backend/`: `python -m pytest`.

From `frontend/`: `npm run lint` and `npm run build`.

These are verification commands, not a claim that all checks pass. Some tests retain SQL-era assumptions and need reconciliation with the MongoDB implementation.

## Code guide

- `backend/app/adapters/`: source-specific parsing.
- `backend/app/services/`: ingestion, extraction, and fingerprints.
- `backend/app/repositories/`: data access.
- `backend/app/api/`: HTTP endpoints.
- `backend/tests/`: fixtures and tests.
- `frontend/src/`: interface, API client, and types.

## Current scope

This is a development project. Source availability and page formats change, so validate adapters before relying on results. Check each source's access rules and configure appropriate request limits. Review dependency versions before production use. Keep database credentials, LLM tokens, and private collected data outside Git.

## Author

[Chalana Gimhana](https://github.com/ChalanaGimhanaX) — backend development, APIs, and automation.
