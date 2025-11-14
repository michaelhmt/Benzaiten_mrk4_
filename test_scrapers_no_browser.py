#!/usr/bin/env python3
"""Test script to verify web scrapers can be instantiated and basic methods work"""

import sys
import os

# Add project root to path
sys.path.insert(0, '/home/user/Benzaiten_mrk4_')

from benzaiten_common.logging_config import get_logger

logger = get_logger(__name__)

print("Testing Web Scrapers (without browser)")
print("=" * 60)

# Test 1: FanfictionNet Scraper instantiation
print("\n1. Testing FanfictionNet Scraper instantiation...")
try:
    from webscraper_modules.fanfiction_net_scraper import FanfictionNetScraper

    # Create scraper instance with minimal params (don't start browser operations)
    test_url = "https://www.fanfiction.net/anime/Digimon/?&srt=1&r=103&p={}"
    scraper = FanfictionNetScraper(url=test_url, goto=1)
    print("   ✓ FanfictionNetScraper class instantiated")

    # Verify it has expected attributes
    assert hasattr(scraper, 'browser_manager'), "Missing browser_manager attribute"
    assert hasattr(scraper, 'get_story_data'), "Missing get_story_data method"
    assert hasattr(scraper, 'get_author_profile'), "Missing get_author_profile method"
    print("   ✓ FanfictionNetScraper has expected methods")

    # Close browser manager if it was started
    if scraper.browser_manager:
        scraper.browser_manager.close()

except Exception as e:
    print(f"   ✗ FanfictionNetScraper test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 2: Archive of Our Own Scraper instantiation
print("\n2. Testing Archive of Our Own Scraper instantiation...")
try:
    from webscraper_modules.archive_of_our_own import ArchiveOfOurOwnScraper

    # Create scraper instance with minimal params
    test_url = "https://archiveofourown.org/tags/Harry%20Potter/works?page={}"
    scraper = ArchiveOfOurOwnScraper(url=test_url, goto=1)
    print("   ✓ ArchiveOfOurOwnScraper class instantiated")

    # Verify it has expected attributes
    assert hasattr(scraper, 'browser_manager'), "Missing browser_manager attribute"
    assert hasattr(scraper, 'get_story_data'), "Missing get_story_data method"
    assert hasattr(scraper, 'get_author_profile'), "Missing get_author_profile method"
    print("   ✓ ArchiveOfOurOwnScraper has expected methods")

    # Close browser manager if it was started
    if scraper.browser_manager:
        scraper.browser_manager.close()

except Exception as e:
    print(f"   ✗ ArchiveOfOurOwnScraper test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: BaseScraperClass
print("\n3. Testing BaseScraperClass...")
try:
    from webscraper_modules.scraper_baseclass import BaseScraperClass

    # Verify it has expected methods
    assert hasattr(BaseScraperClass, 'add_to_ingested_log'), "Missing add_to_ingested_log method"
    assert hasattr(BaseScraperClass, 'check_already_ingested'), "Missing check_already_ingested method"
    print("   ✓ BaseScraperClass has expected methods")

except Exception as e:
    print(f"   ✗ BaseScraperClass test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Test requests-based scraping (no browser needed)
print("\n4. Testing requests-based web scraping...")
try:
    import requests
    from bs4 import BeautifulSoup

    # Test simple HTTP request
    response = requests.get("https://www.example.com", timeout=10)
    print(f"   ✓ HTTP request successful (status {response.status_code})")

    # Test BeautifulSoup parsing
    soup = BeautifulSoup(response.text, 'html.parser')
    title = soup.find('title')
    if title:
        print(f"   ✓ HTML parsing works (found title: {title.text})")
    else:
        print("   ⚠ HTML parsing works but no title found")

except Exception as e:
    print(f"   ✗ Requests-based scraping test failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Web scraper structure tests complete!")
print("Note: Browser-based tests skipped (requires Chrome/ChromeDriver)")
print("=" * 60)
