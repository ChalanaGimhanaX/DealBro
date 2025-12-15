#!/usr/bin/env python3
"""
Health monitoring script for DealBro.

Checks:
- MongoDB connectivity
- API responsiveness
- Recent ingestion activity
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta

import requests
from pymongo import MongoClient

# Ensure imports + .env resolution work no matter where the script is run from.
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)
os.chdir(BACKEND_DIR)

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def check_database() -> dict:
    """Check MongoDB connectivity and basic stats."""
    try:
        client = MongoClient(settings.mongodb_url, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        db = client[settings.database_name]

        cutoff = datetime.utcnow() - timedelta(hours=24)
        recent_posts = db.deal_posts.count_documents({"created_at": {"$gte": cutoff}})
        enabled_sources = db.sources.count_documents({"enabled": True})

        return {
            "status": "healthy",
            "recent_posts_24h": recent_posts,
            "enabled_sources": enabled_sources,
        }
    except Exception as exc:
        logger.error("database_check_failed", error=str(exc))
        return {"status": "unhealthy", "error": str(exc)}


def check_api() -> dict:
    """Check API responsiveness."""
    try:
        api_url = f"http://{settings.api_host}:{settings.api_port}/api/health"
        response = requests.get(api_url, timeout=5)

        if response.status_code == 200:
            data = response.json()
            return {
                "status": "healthy",
                "response_time_ms": response.elapsed.total_seconds() * 1000,
                "api_version": data.get("version"),
            }

        return {"status": "unhealthy", "http_status": response.status_code}
    except Exception as exc:
        logger.error("api_check_failed", error=str(exc))
        return {"status": "unhealthy", "error": str(exc)}


def check_ingestion() -> dict:
    """Check ingestion staleness."""
    try:
        client = MongoClient(settings.mongodb_url, serverSelectionTimeoutMS=5000)
        db = client[settings.database_name]

        last = db.deal_posts.find_one({}, sort=[("created_at", -1)], projection={"created_at": 1})
        if not last or not last.get("created_at"):
            return {"status": "no_data", "message": "No posts found in database"}

        last_ingestion: datetime = last["created_at"]
        time_since = datetime.utcnow() - last_ingestion
        is_stale = time_since > timedelta(hours=2)

        return {
            "status": "stale" if is_stale else "healthy",
            "last_ingestion": last_ingestion.isoformat(),
            "hours_since": time_since.total_seconds() / 3600,
        }
    except Exception as exc:
        logger.error("ingestion_check_failed", error=str(exc))
        return {"status": "unhealthy", "error": str(exc)}


def main() -> int:
    print("=" * 60)
    print("DealBro Health Check")
    print("=" * 60)
    print(f"Time: {datetime.utcnow().isoformat()}")
    print()

    print("Database Check:")
    db_status = check_database()
    print(f"  Status: {db_status['status']}")
    if db_status["status"] == "healthy":
        print(f"  Recent posts (24h): {db_status['recent_posts_24h']}")
        print(f"  Enabled sources: {db_status['enabled_sources']}")
    else:
        print(f"  Error: {db_status.get('error')}")
    print()

    print("API Check:")
    api_status = check_api()
    print(f"  Status: {api_status['status']}")
    if api_status["status"] == "healthy":
        print(f"  Response time: {api_status['response_time_ms']:.2f}ms")
        print(f"  Version: {api_status.get('api_version')}")
    else:
        print(f"  Error: {api_status.get('error') or api_status.get('http_status')}")
    print()

    print("Ingestion Check:")
    ing_status = check_ingestion()
    print(f"  Status: {ing_status['status']}")
    if "last_ingestion" in ing_status:
        print(f"  Last ingestion: {ing_status['last_ingestion']}")
        print(f"  Hours since: {ing_status['hours_since']:.1f}")
    elif "message" in ing_status:
        print(f"  Message: {ing_status['message']}")
    else:
        print(f"  Error: {ing_status.get('error')}")
    print()

    all_healthy = (
        db_status["status"] == "healthy"
        and api_status["status"] == "healthy"
        and ing_status["status"] in ["healthy", "no_data"]
    )

    print("=" * 60)
    print(f"Overall Status: {'HEALTHY' if all_healthy else 'DEGRADED'}")
    print("=" * 60)

    return 0 if all_healthy else 1


if __name__ == "__main__":
    raise SystemExit(main())
