#!/usr/bin/env python3
"""
Test runner for all pycabfile tests

This module runs both unit tests and functional tests for the pycabfile library.
"""

import sys
import unittest
import os
from pathlib import Path

# Add parent directory to path for importing pycabfile
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import functional tests
from test_functional import run_basic_functionality_test, run_comprehensive_test


def run_unit_tests():
    """Run all unit tests."""
    print("=== Running Unit Tests ===")

    # Discover and run unit tests
    test_dir = Path(__file__).parent
    loader = unittest.TestLoader()
    suite = loader.discover(test_dir, pattern="test_*.py")

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


def run_functional_tests():
    """Run all functional tests."""
    print("\n=== Running Functional Tests ===")

    try:
        run_basic_functionality_test()
        print("\n" + "=" * 50)
        run_comprehensive_test()
        return True
    except Exception as e:
        print(f"Functional tests failed: {e}")
        return False


def main():
    """Main test runner."""
    print("=== pycabfile Complete Test Suite ===\n")

    unit_success = run_unit_tests()
    functional_success = run_functional_tests()

    print("\n" + "=" * 60)
    print("TEST SUMMARY:")
    print(f"  Unit Tests: {'PASSED' if unit_success else 'FAILED'}")
    print(f"  Functional Tests: {'PASSED' if functional_success else 'FAILED'}")

    if unit_success and functional_success:
        print("\nALL TESTS PASSED!")
        return 0
    else:
        print("\nSOME TESTS FAILED!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
