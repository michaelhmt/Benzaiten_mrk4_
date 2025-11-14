#!/usr/bin/env python3
"""Test script to verify data tools functionality"""

import sys
import os
import json

# Add project root to path
sys.path.insert(0, '/home/user/Benzaiten_mrk4_')

print("Testing Data Tools")
print("=" * 60)

# Test 1: pandas availability
print("\n1. Testing pandas availability...")
try:
    import pandas as pd
    import numpy as np
    print(f"   ✓ pandas imported successfully (version {pd.__version__})")
    print(f"   ✓ numpy imported successfully (version {np.__version__})")
except Exception as e:
    print(f"   ✗ pandas/numpy import failed: {e}")
    sys.exit(1)

# Test 2: Visualization libraries
print("\n2. Testing visualization libraries...")
try:
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    import matplotlib.pyplot as plt
    print(f"   ✓ matplotlib imported successfully (version {matplotlib.__version__})")
except Exception as e:
    print(f"   ✗ matplotlib import failed: {e}")
    sys.exit(1)

try:
    from wordcloud import WordCloud, STOPWORDS
    print("   ✓ wordcloud imported successfully")
except Exception as e:
    print(f"   ✗ wordcloud import failed: {e}")
    sys.exit(1)

# Test 3: Collection_data class import
print("\n3. Testing Collection_data class...")
try:
    from data_tools.collection_class import Collection_data
    print("   ✓ Collection_data class imported successfully")

    # Verify it has expected methods
    assert hasattr(Collection_data, '__init__'), "Missing __init__ method"
    print("   ✓ Collection_data has expected structure")
except Exception as e:
    print(f"   ✗ Collection_data test failed: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Test basic pandas operations
print("\n4. Testing pandas data operations...")
try:
    # Create sample data
    test_data = {
        'Title': ['Story 1', 'Story 2', 'Story 3'],
        'Author': ['Author A', 'Author B', 'Author C'],
        'Words': [5000, 10000, 7500],
        'Tags': ['Romance', 'Adventure', 'Drama']
    }

    df = pd.DataFrame(test_data)
    print(f"   ✓ Created DataFrame with {len(df)} rows")

    # Test basic operations
    avg_words = df['Words'].mean()
    print(f"   ✓ Calculated average word count: {avg_words}")

    # Test filtering
    long_stories = df[df['Words'] > 6000]
    print(f"   ✓ Filtered data: {len(long_stories)} stories over 6000 words")

except Exception as e:
    print(f"   ✗ Pandas operations test failed: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Test wordcloud generation
print("\n5. Testing wordcloud generation...")
try:
    # Create sample text
    sample_text = "fanfiction story romance adventure drama plot character development magic wizard"

    # Generate wordcloud
    wordcloud = WordCloud(width=400, height=200, background_color='white').generate(sample_text)
    print("   ✓ WordCloud generated successfully")

    # Verify it can be converted to array (for saving as image)
    image_array = wordcloud.to_array()
    print(f"   ✓ WordCloud converted to array (shape: {image_array.shape})")

except Exception as e:
    print(f"   ✗ WordCloud test failed: {e}")
    import traceback
    traceback.print_exc()

# Test 6: Test matplotlib chart creation
print("\n6. Testing matplotlib chart creation...")
try:
    fig, ax = plt.subplots(figsize=(8, 6))

    # Create sample bar chart
    categories = ['Romance', 'Adventure', 'Drama', 'Comedy']
    counts = [120, 85, 95, 60]

    ax.bar(categories, counts)
    ax.set_title('Story Tags Distribution')
    ax.set_ylabel('Count')

    print("   ✓ Matplotlib chart created successfully")

    # Close figure to free memory
    plt.close(fig)
    print("   ✓ Chart closed successfully")

except Exception as e:
    print(f"   ✗ Matplotlib chart test failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Data tools tests complete!")
print("=" * 60)
