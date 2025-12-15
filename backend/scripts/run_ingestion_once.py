"""Run ingestion once manually."""
from app.ingestion.scheduler import run_ingestion

if __name__ == "__main__":
    run_ingestion()
