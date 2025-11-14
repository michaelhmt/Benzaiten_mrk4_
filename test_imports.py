#!/usr/bin/env python3
"""Test script to verify all imports work correctly"""

import sys
import os

# Add project root to path
sys.path.insert(0, '/home/user/Benzaiten_mrk4_')

print("Testing imports...")
print("=" * 60)

# Test 1: benzaiten_common imports
print("\n1. Testing benzaiten_common imports...")
try:
    from benzaiten_common.logging_config import get_logger, setup_logging
    print("   ✓ logging_config imported successfully")
except Exception as e:
    print(f"   ✗ logging_config failed: {e}")
    sys.exit(1)

try:
    from benzaiten_common.browser_manager import BrowserManager
    print("   ✓ browser_manager imported successfully")
except Exception as e:
    print(f"   ✗ browser_manager failed: {e}")
    sys.exit(1)

try:
    from benzaiten_common.DataBase import Database_Class
    print("   ✓ DataBase imported successfully")
except Exception as e:
    print(f"   ✗ DataBase failed: {e}")
    sys.exit(1)

# Test 2: webscraper_modules imports
print("\n2. Testing webscraper_modules imports...")
try:
    from webscraper_modules.scraper_baseclass import BaseScraperClass
    print("   ✓ scraper_baseclass imported successfully")
except Exception as e:
    print(f"   ✗ scraper_baseclass failed: {e}")
    sys.exit(1)

try:
    from webscraper_modules.fanfiction_net_scraper import FanfictionNetScraper
    print("   ✓ fanfiction_net_scraper imported successfully")
except Exception as e:
    print(f"   ✗ fanfiction_net_scraper failed: {e}")
    sys.exit(1)

try:
    from webscraper_modules.archive_of_our_own import ArchiveOfOurOwnScraper
    print("   ✓ archive_of_our_own imported successfully")
except Exception as e:
    print(f"   ✗ archive_of_our_own failed: {e}")
    sys.exit(1)

# Test 3: data_tools imports
print("\n3. Testing data_tools imports...")
try:
    from data_tools.collection_class import Collection_data
    print("   ✓ collection_class imported successfully")
except Exception as e:
    print(f"   ✗ collection_class failed: {e}")
    sys.exit(1)

# Test 4: Test logging configuration
print("\n4. Testing logging configuration...")
try:
    logger = get_logger("test")
    logger.info("Test log message")
    print("   ✓ Logging configured successfully")
except Exception as e:
    print(f"   ✗ Logging configuration failed: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("All imports successful! ✓")
print("=" * 60)
