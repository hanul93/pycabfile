"""
pycabfile: A Python library for handling Microsoft Cabinet files with zipfile-like interface

This module provides a zipfile-compatible interface for creating and extracting CAB files.
Compatible with Python 3.10+.
"""

__version__ = "1.0.0"

# Import main classes and constants from cabfile module
from .cabfile import CabFile, CabInfo, CAB_STORED, CAB_COMPRESSED
from .cab_reader import CABException

# Main module exports
__all__ = ["CabFile", "CabInfo", "CAB_STORED", "CAB_COMPRESSED", "CABException"]
