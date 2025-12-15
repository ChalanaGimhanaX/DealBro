"""Test all adapters to see if they can discover threads."""
import sys
from app.adapters.webhostingtalk import WebHostingTalkAdapter
from app.adapters.serverhunter import ServerHunterAdapter
from app.adapters.hostingdiscussion import HostingDiscussionAdapter

def test_adapter(name, adapter):
    print(f"\n{'=' * 60}")
    print(f"Testing {name}")
    print(f"{'=' * 60}")
    
    try:
        threads = list(adapter.discover())
        print(f"✓ Discovered {len(threads)} threads")
        
        if threads:
            print(f"\nFirst 3 threads:")
            for i, thread in enumerate(threads[:3], 1):
                print(f"\n  {i}. {thread.title}")
                print(f"     URL: {thread.url}")
                print(f"     Category: {thread.category}")
                print(f"     ID: {thread.source_thread_id}")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("Testing all adapters...\n")
    
    results = {}
    
    # Test WebHostingTalk
    wht_adapter = WebHostingTalkAdapter()
    results['webhostingtalk'] = test_adapter("WebHostingTalk", wht_adapter)
    
    # Test ServerHunter
    sh_adapter = ServerHunterAdapter()
    results['serverhunter'] = test_adapter("ServerHunter", sh_adapter)
    
    # Test HostingDiscussion
    hd_adapter = HostingDiscussionAdapter(
        base_url="https://hostingdiscussion.com",
        user_agent="Mozilla/5.0"
    )
    results['hostingdiscussion'] = test_adapter("HostingDiscussion", hd_adapter)
    
    # Summary
    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print(f"{'=' * 60}")
    for name, success in results.items():
        status = "✓" if success else "✗"
        print(f"{status} {name}")
    
    # Return exit code
    sys.exit(0 if all(results.values()) else 1)

if __name__ == "__main__":
    main()
