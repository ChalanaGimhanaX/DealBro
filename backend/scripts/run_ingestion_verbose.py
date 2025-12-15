"""Run ingestion with console output."""
import sys
sys.path.insert(0, 'C:/Users/chala/Documents/Projects/DealBro/backend')

import time
from datetime import datetime
import concurrent.futures

from app.core.database import get_sync_db
from app.services.ingestion import IngestionService
from app.services.llm_extractor import get_llm_extractor
from app.ingestion.scheduler import get_adapter_for_source

def run_ingestion_with_output():
    db = get_sync_db()
    
    sources = list(db.sources.find({"enabled": True}))
    
    print(f"\n{'='*60}")
    print(f"INGESTION STARTED")
    print(f"{'='*60}")
    print(f"Enabled sources: {', '.join([s['name'] for s in sources])}")
    
    if not sources:
        print("❌ No enabled sources found")
        return
    
    # Phase 1
    print(f"\n{'='*60}")
    print(f"PHASE 1: Discovering and fetching HTML")
    print(f"{'='*60}")
    
    all_threads_with_html = []
    ingestion_service = IngestionService()
    
    for source in sources:
        print(f"\n📡 {source['name']}...")
        try:
            adapter = get_adapter_for_source(source)
            if not adapter:
                print(f"  ❌ No adapter found")
                continue
            
            thread_count = 0
            for thread in adapter.discover():
                try:
                    html = adapter.fetch_thread_html(thread.url)
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
                        'full_html': html,
                    })
                    
                    thread_count += 1
                    print(f"  ✓ {thread.title[:60]}...")
                    time.sleep(0.2)
                    
                except Exception as e:
                    print(f"  ⚠️  Failed: {str(e)[:50]}")
                    continue
            
            print(f"  ✅ {source['name']}: {thread_count} threads")
                
        except Exception as e:
            print(f"  ❌ Error: {str(e)[:100]}")
            continue
    
    print(f"\n{'='*60}")
    print(f"Phase 1 Complete: {len(all_threads_with_html)} threads")
    print(f"{'='*60}")
    
    if not all_threads_with_html:
        print("❌ No threads fetched")
        return
    
    # Phase 2
    print(f"\n{'='*60}")
    print(f"PHASE 2: LLM Validation (Parallel Batches)")
    print(f"{'='*60}")
    
    def chunk_list(lst, n):
        for i in range(0, len(lst), n):
            yield lst[i:i + n]
    
    BATCH_SIZE = 30
    batches = list(chunk_list(all_threads_with_html, BATCH_SIZE))
    
    print(f"Creating {len(batches)} batches ({BATCH_SIZE} threads each)")
    print(f"Running up to 3 LLM requests in parallel...\n")
    
    extractor = get_llm_extractor()
    all_valid_deals = {}
    
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
                print(f"  ✅ Batch {batch_idx + 1}/{len(batches)}: {len(valid_deals)} deals approved")
            except Exception as e:
                print(f"  ❌ Batch {batch_idx + 1} failed: {str(e)[:50]}")
    
    print(f"\n{'='*60}")
    print(f"Phase 2 Complete: {len(all_valid_deals)} valid deals")
    print(f"{'='*60}")
    
    if not all_valid_deals:
        print("❌ No valid deals found")
        return
    
    # Phase 3
    print(f"\n{'='*60}")
    print(f"PHASE 3: Storing Deals")
    print(f"{'='*60}\n")
    
    ingested_count = 0
    thread_map = {t['id']: t for t in all_threads_with_html}
    
    for thread_id, llm_data in all_valid_deals.items():
        try:
            thread_info = thread_map.get(thread_id)
            if not thread_info:
                continue
            
            source = thread_info['source']
            
            if ingestion_service.already_ingested(source, thread_info['url']):
                print(f"  ⏭️  Already exists: {thread_info['title'][:60]}...")
                continue
            
            adapter = get_adapter_for_source(source)
            if not adapter:
                continue
            
            post, items = adapter.parse_thread(
                thread_info['full_html'],
                thread_info['url'],
                thread_info['category'],
                thread_info['summary'],
                thread_info['title']
            )
            
            post_id = ingestion_service.ingest_thread_with_llm_data(
                source, post, items, thread_info['full_html'], llm_data
            )
            
            if post_id:
                ingested_count += 1
                print(f"  ✅ {thread_info['title'][:60]}...")
            
        except Exception as e:
            print(f"  ❌ Failed: {str(e)[:50]}")
            continue
    
    print(f"\n{'='*60}")
    print(f"INGESTION COMPLETE")
    print(f"{'='*60}")
    print(f"Discovered: {len(all_threads_with_html)} threads")
    print(f"Valid: {len(all_valid_deals)} deals (LLM approved)")
    print(f"Stored: {ingested_count} new deals")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    run_ingestion_with_output()
