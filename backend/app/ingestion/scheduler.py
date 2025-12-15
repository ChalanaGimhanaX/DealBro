import time
from datetime import datetime
from typing import List, Dict, Any

from apscheduler.schedulers.blocking import BlockingScheduler

from app.core.database import get_sync_db, init_default_sources_sync
from app.core.config import settings
from app.core.logging import get_logger
from app.adapters import get_adapter_class
from app.services.ingestion import IngestionService
from app.services.llm_extractor import get_llm_extractor
import concurrent.futures

logger = get_logger(__name__)


def run_ingestion():
    """
    Two-phase parallel batch ingestion:
    1. Discover and fetch HTML for all threads
    2. Send to LLM in parallel batches (auto-chunk to avoid token limits)
    3. Store results directly
    """
    db = get_sync_db()
    
    try:
        sources = list(db.sources.find({"enabled": True}))
        
        logger.info(
            "ingestion_started",
            sources=[s["name"] for s in sources],
            timestamp=datetime.now().isoformat()
        )
        
        # Phase 1: Discover and fetch HTML for all threads
        all_threads_with_html = []
        ingestion_service = IngestionService()
        
        for source in sources:
            try:
                adapter = get_adapter_for_source(source)
                if not adapter:
                    continue
                
                for thread in adapter.discover():
                    try:
                        # Fetch HTML immediately
                        html = adapter.fetch_thread_html(thread.url)
                        
                        # Truncate HTML to avoid token limits (keep first 8000 chars)
                        html_truncated = html[:8000] if len(html) > 8000 else html
                        
                        thread_id = f"{source['name']}:{thread.url}"
                        all_threads_with_html.append({
                            'id': thread_id,
                            'title': thread.title,
                            'summary': getattr(thread, 'summary', ''),
                            'html': html_truncated,
                            'url': thread.url,
                            'category': getattr(thread, 'category', 'vps'),
                            'source': source,
                            'full_html': html,  # Keep full HTML for storage
                        })
                        
                        time.sleep(0.2)  # Rate limit
                        
                    except Exception as e:
                        logger.warning("html_fetch_failed", url=thread.url, error=str(e))
                        continue
                    
            except Exception as e:
                logger.error("source_discovery_failed", source=source["name"], error=str(e))
                continue
        
        logger.info("discovery_and_fetch_complete", total_threads=len(all_threads_with_html))
        
        if not all_threads_with_html:
            logger.info("no_threads_fetched")
            return
        
        # Phase 2: Send to LLM in parallel batches (chunk size: 30)
        def chunk_list(lst, n):
            """Yield successive n-sized chunks from lst."""
            for i in range(0, len(lst), n):
                yield lst[i:i + n]
        
        BATCH_SIZE = 30  # Threads per LLM request
        batches = list(chunk_list(all_threads_with_html, BATCH_SIZE))
        
        logger.info("starting_parallel_llm", num_batches=len(batches), batch_size=BATCH_SIZE)
        
        extractor = get_llm_extractor()
        all_valid_deals = {}
        
        # Process batches in parallel (max 3 concurrent LLM requests)
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_to_batch = {
                executor.submit(extractor.batch_validate_and_extract, batch): i 
                for i, batch in enumerate(batches)
            }
            
            for future in concurrent.futures.as_completed(future_to_batch):
                batch_idx = future_to_batch[future]
                try:
                    valid_deals = future.result()
                    all_valid_deals.update(valid_deals)
                    logger.info("batch_complete", batch_idx=batch_idx, valid_count=len(valid_deals))
                except Exception as e:
                    logger.error("batch_failed", batch_idx=batch_idx, error=str(e))
        
        logger.info("llm_validation_complete", total_valid=len(all_valid_deals))
        
        if not all_valid_deals:
            logger.info("no_valid_deals_found")
            return
        
        # Phase 3: Store results directly (check duplicates only for valid deals)
        ingested_count = 0
        
        # Create lookup map
        thread_map = {t['id']: t for t in all_threads_with_html}
        
        for thread_id, llm_data in all_valid_deals.items():
            try:
                thread_info = thread_map.get(thread_id)
                if not thread_info:
                    continue
                
                source = thread_info['source']
                
                # Check if already ingested (only check valid deals)
                if ingestion_service.already_ingested(source, thread_info['url']):
                    logger.info("already_ingested_skipping", url=thread_info['url'])
                    continue
                
                adapter = get_adapter_for_source(source)
                if not adapter:
                    continue
                
                # Parse thread (minimal - just for post structure)
                post, items = adapter.parse_thread(
                    thread_info['full_html'],
                    thread_info['url'],
                    thread_info['category'],
                    thread_info['summary'],
                    thread_info['title']
                )
                
                # Store with LLM data
                post_id = ingestion_service.ingest_thread_with_llm_data(
                    source, post, items, thread_info['full_html'], llm_data
                )
                
                if post_id:
                    ingested_count += 1
                    logger.info("deal_ingested", post_id=post_id, title=thread_info['title'])
                
            except Exception as e:
                logger.error("deal_storage_failed", thread_id=thread_id, error=str(e))
                continue
        
        logger.info(
            "ingestion_completed",
            discovered=len(all_threads_with_html),
            valid=len(all_valid_deals),
            ingested=ingested_count,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error("ingestion_error", error=str(e), exc_info=True)


def discover_source_threads(source: dict) -> List[Dict[str, Any]]:
    """Discover threads from a source (titles + summaries only, no full fetch)."""
    adapter = get_adapter_for_source(source)
    if not adapter:
        return []
    
    threads = []
    ingestion_service = IngestionService()
    
    for thread in adapter.discover():
        # Skip already ingested
        if ingestion_service.already_ingested(source, thread.url):
            continue
            
        threads.append({
            'url': thread.url,
            'title': thread.title,
            'summary': getattr(thread, 'summary', ''),
            'category': getattr(thread, 'category', 'vps'),
        })
    
    logger.info("source_discovered", source=source["name"], threads=len(threads))
    return threads


def get_adapter_for_source(source: dict):
    """Create adapter for a source."""
    adapter_class = get_adapter_class(source["name"])
    if not adapter_class:
        logger.warning("no_adapter_found", source=source["name"])
        return None
    
    rate_limit_attr = f"rate_limit_{source['name']}"
    rate_limit = getattr(settings, rate_limit_attr, 30)
    
    return adapter_class(
        base_url=source["base_url"],
        user_agent=settings.user_agent,
        rate_limit=rate_limit
    )


def main():
    """Main entry point for the scheduler."""
    logger.info(
        "scheduler_starting",
        interval_minutes=settings.ingestion_interval_minutes
    )
    
    # Initialize database and sources
    init_default_sources_sync()
    
    # Create scheduler
    scheduler = BlockingScheduler()
    
    # Schedule ingestion
    scheduler.add_job(
        run_ingestion,
        'interval',
        minutes=settings.ingestion_interval_minutes,
        id='ingestion_job',
        name='Ingest deals from all sources',
        replace_existing=True
    )
    
    # Run once immediately
    print("Running initial ingestion...")
    run_ingestion()
    
    # Start scheduler
    print(f"Scheduler started. Ingestion will run every {settings.ingestion_interval_minutes} minutes.")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("scheduler_stopping")


if __name__ == "__main__":
    main()
