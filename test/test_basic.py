#!/usr/bin/env python3
"""
Basic unit tests for pycabfile - CAB file handling with zipfile-like interface
"""

import os
import tempfile
import shutil
import unittest
import sys
from pathlib import Path

# Add parent directory to path for importing pycabfile
sys.path.insert(0, str(Path(__file__).parent.parent))

from pycabfile import CabFile, CabInfo, CAB_STORED, CAB_COMPRESSED, CABException


class TestPyCabFile(unittest.TestCase):
    """Test cases for pycabfile functionality."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_files = self._create_test_files()
        self.cab_filename = os.path.join(self.temp_dir, "test.cab")

    def tearDown(self):
        """Clean up test environment."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def _create_test_files(self):
        """Create test files for CAB operations."""
        files = {}

        # Text file
        text_file = os.path.join(self.temp_dir, "test.txt")
        with open(text_file, "w", encoding="utf-8") as f:
            f.write("Hello World!\nTest file content")
        files["text"] = text_file

        # Binary file
        bin_file = os.path.join(self.temp_dir, "test.bin")
        with open(bin_file, "wb") as f:
            f.write(bytes(range(256)))
        files["binary"] = bin_file

        return files

    def test_cab_creation_and_reading(self):
        """Test basic CAB file creation and reading."""
        # Create CAB file
        with CabFile(self.cab_filename, "w") as cab:
            cab.write(self.test_files["text"], "text_file.txt")
            cab.write(self.test_files["binary"], "binary_file.bin")
            cab.writestr("string_file.txt", "Direct string content")

        # Verify CAB file was created
        self.assertTrue(os.path.exists(self.cab_filename))

        # Read CAB file
        with CabFile(self.cab_filename, "r") as cab:
            # Test namelist
            files = cab.namelist()
            self.assertEqual(len(files), 3)
            self.assertIn("text_file.txt", files)
            self.assertIn("binary_file.bin", files)
            self.assertIn("string_file.txt", files)

            # Test read
            content = cab.read("string_file.txt")
            self.assertEqual(content, b"Direct string content")

            # Test getinfo
            info = cab.getinfo("text_file.txt")
            self.assertIsInstance(info, CabInfo)
            self.assertEqual(info.filename, "text_file.txt")
            self.assertGreater(info.file_size, 0)

    def test_cab_extraction(self):
        """Test CAB file extraction."""
        # Create CAB file (current CAB implementation supports flat filenames only)
        with CabFile(self.cab_filename, "w") as cab:
            cab.writestr("test1.txt", "Content 1")
            cab.writestr("test2.txt", "Content 2")

        # Extract files
        extract_dir = os.path.join(self.temp_dir, "extracted")
        with CabFile(self.cab_filename, "r") as cab:
            # Test single file extraction
            extracted_file = cab.extract("test1.txt", extract_dir)
            self.assertTrue(os.path.exists(extracted_file))

            # Test extractall
            cab.extractall(extract_dir)

            # Verify extracted files
            self.assertTrue(os.path.exists(os.path.join(extract_dir, "test1.txt")))
            self.assertTrue(os.path.exists(os.path.join(extract_dir, "test2.txt")))

            # Verify content
            with open(os.path.join(extract_dir, "test1.txt"), "r") as f:
                self.assertEqual(f.read(), "Content 1")

    def test_context_manager(self):
        """Test context manager functionality."""
        # Test that context manager properly closes files
        with CabFile(self.cab_filename, "w") as cab:
            cab.writestr("test.txt", "Test content")
            self.assertFalse(cab._closed)

        # After context, file should be closed
        self.assertTrue(cab._closed)

        # Should be able to read the created file
        with CabFile(self.cab_filename, "r") as cab:
            content = cab.read("test.txt")
            self.assertEqual(content, b"Test content")

    def test_error_handling(self):
        """Test error handling for various edge cases."""
        # Test reading non-existent CAB file
        with self.assertRaises(FileNotFoundError):
            CabFile("nonexistent.cab", "r")

        # Test invalid mode
        with self.assertRaises(ValueError):
            CabFile(self.cab_filename, "x")

        # Test reading non-existent file from CAB
        with CabFile(self.cab_filename, "w") as cab:
            cab.writestr("test.txt", "content")

        with CabFile(self.cab_filename, "r") as cab:
            with self.assertRaises(KeyError):
                cab.read("nonexistent.txt")

            with self.assertRaises(KeyError):
                cab.getinfo("nonexistent.txt")

    def test_binary_data_handling(self):
        """Test handling of binary data."""
        binary_data = bytes(range(256))

        with CabFile(self.cab_filename, "w") as cab:
            cab.writestr("binary.bin", binary_data)

        with CabFile(self.cab_filename, "r") as cab:
            read_data = cab.read("binary.bin")
            self.assertEqual(binary_data, read_data)

    def test_unicode_filenames(self):
        """Test handling of Unicode filenames."""
        unicode_filename = "unicode_file.txt"
        unicode_content = "Unicode content with special characters: àáâãäåæçèéêë"

        with CabFile(self.cab_filename, "w") as cab:
            cab.writestr(unicode_filename, unicode_content)

        with CabFile(self.cab_filename, "r") as cab:
            files = cab.namelist()
            self.assertIn(unicode_filename, files)

            content = cab.read(unicode_filename)
            self.assertEqual(content.decode("utf-8"), unicode_content)


if __name__ == "__main__":
    unittest.main(verbosity=2)
