#!/usr/bin/env python3
"""
Legacy test file - Use test/ directory for organized testing

This file now redirects to the organized test suite in the test/ directory.
For better test organization, use:
- test/test_basic.py for unit tests
- test/test_functional.py for functional tests  
- test/run_all_tests.py to run all tests
"""

import sys
import os
from pathlib import Path

# Add test directory to path
test_dir = Path(__file__).parent / "test"
sys.path.insert(0, str(test_dir))

try:
    from run_all_tests import main

    print("=" * 60)
    print("NOTICE: This file has been moved to test/ directory")
    print("For better organization, use:")
    print("  - cd test && python run_all_tests.py")
    print("  - cd test && python test_basic.py")
    print("  - cd test && python test_functional.py")
    print("=" * 60)
    print()

    # Run the organized test suite
    sys.exit(main())

except ImportError as e:
    print(f"Error importing test modules: {e}")
    print("Please ensure the test directory contains the proper test files.")
    sys.exit(1)
