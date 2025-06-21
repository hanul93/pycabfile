"""
Utility functions for CAB file operations

This module provides various helper functions for working with CAB files.
"""

import os


class Utils(object):
    """Collection of utility functions for CAB operations"""

    @staticmethod
    def get_file_size(fileobject):
        """Get file size from file object"""
        current_pos = fileobject.tell()
        fileobject.seek(0, 2)  # Seek to end
        size = fileobject.tell()
        fileobject.seek(current_pos)  # Restore original position
        return size

    @staticmethod
    def normalize_path(path):
        """Normalize file path for cross-platform compatibility"""
        return os.path.normpath(path).replace("\\", "/")

    @staticmethod
    def ensure_directory_exists(directory):
        """Ensure directory exists, creating if necessary"""
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

    @staticmethod
    def safe_filename(filename):
        """Make filename safe for filesystem use"""
        # Remove or replace problematic characters
        unsafe_chars = '<>:"/\\|?*'
        safe_name = filename
        for char in unsafe_chars:
            safe_name = safe_name.replace(char, "_")

        # Limit length
        if len(safe_name) > 255:
            name, ext = os.path.splitext(safe_name)
            safe_name = name[: 255 - len(ext)] + ext

        return safe_name
