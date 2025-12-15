"""
Automatic ingestion scheduler that runs every 6 hours.
Usage: python -m app.ingestion.auto_scheduler
"""
import time
import schedule
from datetime import datetime
from app.ingestion.scheduler import run_ingestion
from app.core.logging import get_logger

logger = get_logger(__name__)


def job():
    """Run the ingestion job."""
    logger.info("scheduled_ingestion_started", timestamp=datetime.now().isoformat())
    try:
        run_ingestion()
        logger.info("scheduled_ingestion_completed", timestamp=datetime.now().isoformat())
    except Exception as e:
        logger.error("scheduled_ingestion_failed", error=str(e), exc_info=True)


def main():
    """Main scheduler loop."""
    print("=" * 60)
    print("DealBro Automatic Ingestion Scheduler")
    print("=" * 60)
    print("Running initial ingestion...")
    
    # Run immediately on start
    job()
    
    # Schedule to run every 6 hours
    schedule.every(6).hours.do(job)
    
    print(f"\nScheduler started at {datetime.now().isoformat()}")
    print("Next run in 6 hours")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    
    # Keep the scheduler running
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nScheduler stopped by user")
