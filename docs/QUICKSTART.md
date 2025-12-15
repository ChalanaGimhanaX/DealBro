# Quick Start Guide

Get DealBro running in under 10 minutes!

## Prerequisites

- Python 3.11+ installed
- MongoDB 6+ installed and running (or MongoDB Atlas)
- Node.js 18+ installed
- Git

## Step 1: Clone Repository

```bash
git clone https://github.com/yourusername/dealbro.git
cd dealbro
```

## Step 2: Setup Backend

### Install Python Dependencies

```bash
cd backend
python -m venv venv

# On Windows
venv\Scripts\activate

# On Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
```

### Configure Database

```bash
# Copy environment file
cp .env.example .env

# Edit .env with your MongoDB connection string
# Windows: notepad .env
# Linux/Mac: nano .env
```

Update `MONGODB_URL` and `DATABASE_NAME` in `.env`:
```
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=dealbro
```
DealBro creates required indexes and seeds default sources on startup.

## Step 3: Start Backend

### Terminal 1 - API Server

```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
python -m uvicorn app.main:app --reload
```

API will be available at: http://localhost:8000

API docs: http://localhost:8000/docs

### Terminal 2 - Ingestion Service

```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
python -m app.ingestion.scheduler
```

This will start scraping deals every 30 minutes (configurable).

## Step 4: Setup Frontend

Open a new terminal:

```bash
cd frontend
npm install

# Copy environment file
cp .env.local.example .env.local

npm run dev
```

Frontend will be available at: http://localhost:3000

## Step 5: Verify Installation

1. **Check API Health**: Visit http://localhost:8000/api/health
   - Should return `{"status": "healthy"}`

2. **Check Database**: Visit http://localhost:8000/api/sources
   - Should return list of sources

3. **Check Frontend**: Visit http://localhost:3000
   - Should show the deals page (may be empty initially)

4. **Wait for First Ingestion**: After a few minutes, refresh frontend
   - Deals should start appearing

## Common Quick Fixes

### Database Connection Error

```bash
# Make sure MongoDB is running
sudo systemctl status mongod  # Linux
# or check Services on Windows

# Test connection manually
mongosh "mongodb://localhost:27017"
```

### Port Already in Use

Change ports in configuration:
- Backend: Edit `API_PORT` in `.env`
- Frontend: Use `npm run dev -- -p 3001`

### No Deals Appearing

Check ingestion logs in Terminal 2. First ingestion takes 5-10 minutes.

## Next Steps

1. **Read Full Documentation**
   - [README.md](../README.md) - Overview
   - [API.md](API.md) - API documentation
   - [DEVELOPMENT.md](DEVELOPMENT.md) - Development guide

2. **Customize Configuration**
   - Adjust ingestion interval in `.env`
   - Enable/disable sources
   - Configure rate limits

3. **Run Tests**
   ```bash
   cd backend
   python -m pytest
   ```

4. **Add More Sources**
   - See DEVELOPMENT.md for guide on adding adapters

## Need Help?

- Check logs for errors
- Run health check: `python scripts/health_check.py`
- See [DEVELOPMENT.md](DEVELOPMENT.md) for troubleshooting

## Production Deployment

For production deployment, see [DEPLOYMENT.md](DEPLOYMENT.md).

Key differences:
- Use Gunicorn/Uvicorn workers
- Setup Nginx reverse proxy
- Enable SSL with Let's Encrypt
- Setup automated backups
- Configure monitoring

---

**Congratulations!** 🎉 DealBro is now running!

Visit http://localhost:3000 to start browsing deals.
