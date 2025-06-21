#!/usr/bin/env python3
"""
Functional tests for pycabfile - High-level integration testing
"""

import os
import tempfile
import shutil
import sys
from pathlib import Path

# Add parent directory to path for importing pycabfile
sys.path.insert(0, str(Path(__file__).parent.parent))

from pycabfile import CabFile


def run_basic_functionality_test():
    """Run a basic functionality test to verify the package works."""
    print("Running pycabfile basic functionality test...")

    temp_dir = tempfile.mkdtemp()
    try:
        cab_file = os.path.join(temp_dir, "basic_test.cab")

        # Create test CAB
        print("1. CAB file creation test...")
        with CabFile(cab_file, "w") as cab:
            cab.writestr("hello.txt", "Hello, World!")
            cab.writestr("test.txt", "Test content")
        print("   CAB file creation successful")

        # Read test CAB
        print("2. CAB file reading test...")
        with CabFile(cab_file, "r") as cab:
            files = cab.namelist()
            print(f"   File list: {files}")

            for filename in files:
                content = cab.read(filename)
                print(f"   {filename}: {content.decode('utf-8')}")
        print("   CAB file reading successful")

        # Extract test
        print("3. CAB file extraction test...")
        extract_dir = os.path.join(temp_dir, "extracted")
        with CabFile(cab_file, "r") as cab:
            cab.extractall(extract_dir)

        extracted_files = []
        for root, dirs, files in os.walk(extract_dir):
            for file in files:
                extracted_files.append(os.path.relpath(os.path.join(root, file), extract_dir))
        print(f"   Extracted files: {extracted_files}")
        print("   CAB file extraction successful")

        print("\nAll basic functionality tests passed!")

    except Exception as e:
        print(f"Test failed: {e}")
        raise
    finally:
        shutil.rmtree(temp_dir)


def run_comprehensive_test():
    """Run a comprehensive test covering multiple scenarios."""
    print("Running comprehensive functionality test...")

    temp_dir = tempfile.mkdtemp()
    try:
        # Test 1: Multiple file types
        print("1. Testing multiple file types...")
        cab_file = os.path.join(temp_dir, "multi_test.cab")

        test_data = {
            "text.txt": "This is a text file",
            "binary.bin": bytes(range(50)),
            "empty.txt": "",
            "unicode.txt": "Unicode: αβγδε 中文 🌟",
        }

        # Create CAB with various file types
        with CabFile(cab_file, "w") as cab:
            for filename, content in test_data.items():
                if isinstance(content, str):
                    cab.writestr(filename, content)
                else:
                    cab.writestr(filename, content)

        # Verify contents
        with CabFile(cab_file, "r") as cab:
            files = cab.namelist()
            print(f"   Created files: {files}")

            for filename in files:
                content = cab.read(filename)
                original = test_data[filename]
                if isinstance(original, str):
                    assert content.decode("utf-8") == original
                else:
                    assert content == original
        print("   Multiple file types test passed")

        # Test 2: Large file handling
        print("2. Testing large file handling...")
        large_cab = os.path.join(temp_dir, "large_test.cab")
        large_content = "A" * 10000  # 10KB of data

        with CabFile(large_cab, "w") as cab:
            cab.writestr("large.txt", large_content)

        with CabFile(large_cab, "r") as cab:
            read_content = cab.read("large.txt").decode("utf-8")
            assert read_content == large_content
        print("   Large file handling test passed")

        # Test 3: File information
        print("3. Testing file information retrieval...")
        with CabFile(cab_file, "r") as cab:
            for filename in cab.namelist():
                info = cab.getinfo(filename)
                print(f"   {filename}: size={info.file_size}, compressed={info.compress_size}")
                assert info.filename == filename
                assert info.file_size >= 0
                assert info.compress_size >= 0
        print("   File information test passed")

        print("\nAll comprehensive tests passed!")

    except Exception as e:
        print(f"Comprehensive test failed: {e}")
        raise
    finally:
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    print("=== pycabfile Functional Test Suite ===\n")

    try:
        run_basic_functionality_test()
        print("\n" + "=" * 50)
        run_comprehensive_test()
        print("\n" + "=" * 50)
        print("All functional tests completed successfully!")
    except Exception as e:
        print(f"\nFunctional tests failed: {e}")
        sys.exit(1)
