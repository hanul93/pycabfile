#!/usr/bin/env python3
"""
Example usage of pycabfile - CAB file handling with zipfile-like interface

This script demonstrates how to use pycabfile to create and extract CAB files
using the same interface as Python's zipfile module.
"""

import os
import tempfile
from pycabfile import CabFile, CAB_STORED, CAB_COMPRESSED


def create_sample_files():
    """Create some sample files for testing."""
    temp_dir = tempfile.mkdtemp()

    # Create sample text file
    with open(os.path.join(temp_dir, "sample.txt"), "w", encoding="utf-8") as f:
        f.write("This is a sample text file for testing.\nSupports Unicode characters: àáâãäåæçèéêë")

    # Create sample binary file
    with open(os.path.join(temp_dir, "sample.bin"), "wb") as f:
        f.write(b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f")

    # Create nested directory structure
    nested_dir = os.path.join(temp_dir, "nested")
    os.makedirs(nested_dir, exist_ok=True)

    with open(os.path.join(nested_dir, "nested.txt"), "w") as f:
        f.write("This is a nested file.")

    return temp_dir


def demo_cab_creation():
    """Demonstrate CAB file creation using zipfile-like interface."""
    print("=== CAB File Creation Demo ===")

    # Create sample files
    temp_dir = create_sample_files()
    sample_files = [
        os.path.join(temp_dir, "sample.txt"),
        os.path.join(temp_dir, "sample.bin"),
        os.path.join(temp_dir, "nested", "nested.txt"),
    ]

    # Create CAB file using context manager (recommended)
    cab_filename = "example.cab"
    with CabFile(cab_filename, "w") as cab:
        print(f"Creating CAB file '{cab_filename}'...")

        # Add files to CAB
        for file_path in sample_files:
            if os.path.exists(file_path):
                # Use relative path as archive name
                arcname = os.path.relpath(file_path, temp_dir)
                cab.write(file_path, arcname)
                print(f"  Added: {arcname}")

        # Add data directly as string
        cab.writestr("readme.txt", "This file was written directly to the CAB archive.")
        print("  Added: readme.txt (direct write)")

    print(f"CAB file '{cab_filename}' created successfully!")

    # Clean up temp directory
    import shutil

    shutil.rmtree(temp_dir)

    return cab_filename


def demo_cab_extraction(cab_filename):
    """Demonstrate CAB file extraction using zipfile-like interface."""
    print(f"\n=== CAB File '{cab_filename}' Extraction Demo ===")

    # Open CAB file for reading
    with CabFile(cab_filename, "r") as cab:
        # List all files in CAB
        print("CAB file contents:")
        file_list = cab.namelist()
        for filename in file_list:
            info = cab.getinfo(filename)
            print(f"  {filename} ({info.file_size} bytes)")

        # Read specific file content
        print(f"\n'readme.txt' content:")
        readme_content = cab.read("readme.txt")
        print(f"  {readme_content.decode('utf-8')}")

        # Extract all files to a directory
        extract_dir = "extracted"
        os.makedirs(extract_dir, exist_ok=True)
        print(f"\nExtracting all files to '{extract_dir}' directory...")
        cab.extractall(extract_dir)

        # Verify extracted files
        for root, dirs, files in os.walk(extract_dir):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, extract_dir)
                print(f"  Extracted: {rel_path}")


def demo_cab_append(cab_filename):
    """Demonstrate appending to an existing CAB file."""
    print(f"\n=== CAB File '{cab_filename}' Append Mode Demo ===")

    # Open existing CAB file in append mode
    with CabFile(cab_filename, "a") as cab:
        # Add new content
        cab.writestr("appended.txt", "This file was added to CAB in append mode.")
        print("  Added: appended.txt")

    # Verify the file was added
    with CabFile(cab_filename, "r") as cab:
        file_list = cab.namelist()
        print(f"Updated CAB file contents ({len(file_list)} files):")
        for filename in file_list:
            info = cab.getinfo(filename)
            print(f"  {filename} ({info.file_size} bytes)")


def compare_with_zipfile():
    """Show side-by-side comparison with zipfile usage."""
    print("\n=== Comparison with zipfile Usage ===")

    print("zipfile usage:")
    print(
        """
import zipfile
with zipfile.ZipFile('example.zip', 'w') as zf:
    zf.write('file.txt')
    zf.writestr('data.txt', 'Hello World')

with zipfile.ZipFile('example.zip', 'r') as zf:
    files = zf.namelist()
    content = zf.read('data.txt')
    zf.extractall('output')
    """
    )

    print("pycabfile usage (identical interface):")
    print(
        """
from pycabfile import CabFile
with CabFile('example.cab', 'w') as cf:
    cf.write('file.txt')
    cf.writestr('data.txt', 'Hello World')

with CabFile('example.cab', 'r') as cf:
    files = cf.namelist()
    content = cf.read('data.txt')
    cf.extractall('output')
    """
    )


def main():
    """Main demonstration function."""
    print("pycabfile Library Demo")
    print("=" * 50)

    # Create CAB file
    cab_filename = demo_cab_creation()

    # Extract CAB file
    demo_cab_extraction(cab_filename)

    # Append to CAB file
    demo_cab_append(cab_filename)

    # Show comparison with zipfile
    compare_with_zipfile()

    print(f"\nDemo completed! Generated files:")
    print(f"  - {cab_filename}")
    print(f"  - extracted/ (extracted files)")


if __name__ == "__main__":
    main()
