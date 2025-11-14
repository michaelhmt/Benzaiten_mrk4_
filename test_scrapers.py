#!/usr/bin/env python3
"""Test script to verify web scrapers can connect and fetch data"""

import sys
import os
import time

# Add project root to path
sys.path.insert(0, '/home/user/Benzaiten_mrk4_')

from benzaiten_common.browser_manager import BrowserManager
from benzaiten_common.logging_config import get_logger

logger = get_logger(__name__)

print("Testing Web Scrapers")
print("=" * 60)

# Test 1: Browser Manager
print("\n1. Testing BrowserManager...")
try:
    with BrowserManager(headless=True) as browser:
        print("   ✓ Browser started successfully")

        # Try to fetch a simple page
        print("   → Fetching test page...")
        page_source = browser.get_page("https://www.example.com", delay=2)

        if page_source and len(page_source) > 0:
            print(f"   ✓ Page fetched successfully ({len(page_source)} bytes)")
        else:
            print("   ✗ Failed to fetch page content")
            sys.exit(1)

    print("   ✓ Browser closed successfully")
except Exception as e:
    print(f"   ✗ BrowserManager test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 2: FanfictionNet Scraper connectivity
print("\n2. Testing FanfictionNet Scraper connectivity...")
try:
    from webscraper_modules.fanfiction_net_scraper import FanfictionNetScraper

    # Create scraper instance
    scraper = FanfictionNetScraper(headless=True)
    print("   ✓ FanfictionNetScraper initialized")

    # Try to fetch homepage (just to test connectivity)
    print("   → Testing connection to fanfiction.net...")
    with scraper.browser_manager as browser:
        try:
            page = browser.get_page("https://www.fanfiction.net", delay=2)
            if "FanFiction" in page:
                print("   ✓ Successfully connected to fanfiction.net")
            else:
                print("   ⚠ Connected but unexpected content")
        except Exception as e:
            print(f"   ✗ Connection test failed: {e}")

    print("   ✓ FanfictionNetScraper test complete")

except Exception as e:
    print(f"   ✗ FanfictionNetScraper test failed: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Archive of Our Own Scraper connectivity
print("\n3. Testing Archive of Our Own Scraper connectivity...")
try:
    from webscraper_modules.archive_of_our_own import ArchiveOfOurOwnScraper

    # Create scraper instance
    scraper = ArchiveOfOurOwnScraper(headless=True)
    print("   ✓ ArchiveOfOurOwnScraper initialized")

    # Try to fetch homepage (just to test connectivity)
    print("   → Testing connection to archiveofourown.org...")
    with scraper.browser_manager as browser:
        try:
            page = browser.get_page("https://archiveofourown.org", delay=2)
            if "Archive of Our Own" in page or "AO3" in page:
                print("   ✓ Successfully connected to archiveofourown.org")
            else:
                print("   ⚠ Connected but unexpected content")
        except Exception as e:
            print(f"   ✗ Connection test failed: {e}")

    print("   ✓ ArchiveOfOurOwnScraper test complete")

except Exception as e:
    print(f"   ✗ ArchiveOfOurOwnScraper test failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Web scraper tests complete!")
print("=" * 60)
