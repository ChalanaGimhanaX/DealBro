from datetime import datetime
from fastapi import APIRouter

from app.core.database import get_async_db

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    db = get_async_db()
    
    # Test database connection
    try:
        # Try to ping the database
        await db.command("ping")
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "database": db_status,
        "version": "1.0.0"
    }


@router.get("/ping")
async def ping():
    """Simple ping endpoint."""
    return {"message": "pong"}
