#!/usr/bin/env python3
"""Test script to verify UI can be imported and initialized"""

import sys
import os

# Add project root to path
sys.path.insert(0, '/home/user/Benzaiten_mrk4_')

print("Testing UI Components")
print("=" * 60)

# Test 1: PyQt5 availability
print("\n1. Testing PyQt5 availability...")
try:
    from PyQt5 import QtCore, QtGui, QtWidgets
    print("   ✓ PyQt5 imported successfully")
    print(f"   ✓ Qt version: {QtCore.QT_VERSION_STR}")
    print(f"   ✓ PyQt version: {QtCore.PYQT_VERSION_STR}")
except Exception as e:
    print(f"   ✗ PyQt5 import failed: {e}")
    sys.exit(1)

# Test 2: UI widgets imports
print("\n2. Testing UI widget imports...")
try:
    from benzaiten_ui.ui_widgets.author_info import AuthorInfo
    print("   ✓ AuthorInfo widget imported")
except Exception as e:
    print(f"   ✗ AuthorInfo import failed: {e}")
    import traceback
    traceback.print_exc()

try:
    from benzaiten_ui.ui_widgets.story_info import StoryInfo
    print("   ✓ StoryInfo widget imported")
except Exception as e:
    print(f"   ✗ StoryInfo import failed: {e}")
    import traceback
    traceback.print_exc()

try:
    from benzaiten_ui.ui_widgets.tag_info import TagInfo
    print("   ✓ TagInfo widget imported")
except Exception as e:
    print(f"   ✗ TagInfo import failed: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Main UI imports
print("\n3. Testing main UI imports...")
try:
    from benzaiten_ui.collect_data import Ui_MainWindow
    print("   ✓ Ui_MainWindow (data collection UI) imported")
except Exception as e:
    print(f"   ✗ Ui_MainWindow import failed: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Verify .ui files exist
print("\n4. Checking .ui files...")
ui_files = [
    'benzaiten_ui/main_window.ui',
    'benzaiten_ui/Web_Ingester_UI.ui',
    'benzaiten_ui/ui_widgets/Author_info.ui',
    'benzaiten_ui/ui_widgets/story_info.ui',
    'benzaiten_ui/ui_widgets/Tag_info.ui',
]

for ui_file in ui_files:
    full_path = os.path.join('/home/user/Benzaiten_mrk4_', ui_file)
    if os.path.exists(full_path):
        print(f"   ✓ {ui_file} exists")
    else:
        print(f"   ✗ {ui_file} not found")

print("\n" + "=" * 60)
print("UI component tests complete!")
print("Note: Cannot test actual UI startup in headless environment")
print("=" * 60)
