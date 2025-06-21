"""
CAB file handler with zipfile-compatible interface.

This module provides the main CabFile and CabInfo classes for handling CAB files
with an interface similar to Python's zipfile module.
"""

import os
import io
from pathlib import Path
from typing import Union, List, Optional, BinaryIO
import tempfile
import shutil

# Import our own CAB modules
from .cab_structs import CFHEADER, CFFOLDER, CFFILE, CFDATA
from .cab_reader import CabReader, CABException
from .cab_writer import CABManager, CABFolderUnit

# CAB compression constants (similar to zipfile constants)
CAB_STORED = 0  # No compression
CAB_COMPRESSED = 1  # Default compression


class CabInfo:
    """Information about a file stored in a CAB archive."""

    def __init__(self, filename: str = "", file_size: int = 0):
        self.filename = filename
        self.file_size = file_size
        self.date_time = (1980, 1, 1, 0, 0, 0)  # Default date
        self.compress_type = CAB_STORED
        self.compress_size = file_size

    @property
    def is_dir(self) -> bool:
        """True if this archive member is a directory."""
        return self.filename.endswith("/")


class CabFile:
    """
    A CAB file handler with zipfile-compatible interface.

    This class provides methods to read and write CAB files using an interface
    similar to Python's zipfile.ZipFile class.
    """

    def __init__(
        self,
        file: Union[str, Path, BinaryIO],
        mode: str = "r",
        compression: int = CAB_STORED,
        allowCab64: bool = True,
        compresslevel: Optional[int] = None,
    ):
        """
        Open a CAB file for reading or writing.

        Args:
            file: Path to CAB file or file-like object
            mode: Mode to open file ('r' for read, 'w' for write, 'a' for append)
            compression: Compression method (CAB_STORED or CAB_COMPRESSED)
            allowCab64: Allow large CAB files (for compatibility with zipfile interface)
            compresslevel: Compression level (not used in CAB format)
        """
        self.filename = file if isinstance(file, (str, Path)) else None
        self.mode = mode
        self.compression = compression
        self._file_list = []
        self._file_data = {}
        self._temp_dir = None
        self._closed = False

        if mode == "r":
            self._init_read_mode()
        elif mode == "w":
            self._init_write_mode()
        elif mode == "a":
            # For append mode, first read existing files then switch to write mode
            if os.path.exists(self.filename):
                self._init_read_mode()
                # Store existing data
                existing_data = self._file_data.copy()
                existing_list = self._file_list.copy()
            self._init_write_mode()
            if os.path.exists(self.filename):
                # Restore existing data
                self._file_data.update(existing_data)
                self._file_list.extend(existing_list)
        else:
            raise ValueError(f"Invalid mode: {mode}")

    def _init_read_mode(self):
        """Initialize for reading mode."""
        if not os.path.exists(self.filename):
            raise FileNotFoundError(f"CAB file not found: {self.filename}")

        try:
            self._reader = CabReader(self.filename)

            # Extract all files data
            files_data = self._reader.extract_all_files()

            # Build file list and data dictionary
            for filename, data in files_data.items():
                file_info = CabInfo(filename, len(data))
                self._file_list.append(file_info)
                self._file_data[filename] = data

        except Exception as e:
            raise CABException(f"Failed to read CAB file: {e}")

    def _init_write_mode(self):
        """Initialize for writing mode."""
        self._temp_dir = tempfile.mkdtemp()
        self._folder_unit = CABFolderUnit(name="folder")
        self._manager = CABManager()

    def namelist(self) -> List[str]:
        """Return a list of archive members by name."""
        return [info.filename for info in self._file_list]

    def infolist(self) -> List[CabInfo]:
        """Return a list of CabInfo instances for files in the archive."""
        return self._file_list.copy()

    def getinfo(self, name: str) -> CabInfo:
        """Return a CabInfo object for the specified file."""
        for info in self._file_list:
            if info.filename == name:
                return info
        raise KeyError(f"File '{name}' not found in CAB archive")

    def read(self, name: str) -> bytes:
        """Read and return the bytes of the file name in the archive."""
        if self.mode not in ("r", "a"):
            raise ValueError("CAB file must be opened for reading")

        if name not in self._file_data:
            raise KeyError(f"File '{name}' not found in CAB archive")

        return self._file_data[name]

    def open(self, name: str, mode: str = "r") -> BinaryIO:
        """Return file-like object for the specified file in the archive."""
        if mode != "r":
            raise NotImplementedError("Only read mode is supported for CAB files")

        data = self.read(name)
        return io.BytesIO(data)

    def extract(self, member: Union[str, CabInfo], path: Optional[str] = None) -> str:
        """Extract a member from the archive to the current working directory."""
        if isinstance(member, CabInfo):
            member_name = member.filename
        else:
            member_name = member

        if path is None:
            path = os.getcwd()

        # Create directory structure if needed
        full_path = os.path.join(path, member_name)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        # Write file data
        with open(full_path, "wb") as f:
            f.write(self.read(member_name))

        return full_path

    def extractall(self, path: Optional[str] = None, members: Optional[List[str]] = None):
        """Extract all members from the archive to the current working directory."""
        if path is None:
            path = os.getcwd()

        if members is None:
            members = self.namelist()

        for member in members:
            self.extract(member, path)

    def write(
        self,
        filename: Union[str, Path],
        arcname: Optional[str] = None,
        compress_type: Optional[int] = None,
        compresslevel: Optional[int] = None,
    ):
        """Write a file into the archive."""
        if self.mode not in ("w", "a"):
            raise ValueError("CAB file must be opened for writing")

        if arcname is None:
            arcname = os.path.basename(filename)

        # Read file data
        with open(filename, "rb") as f:
            data = f.read()

        self.writestr(arcname, data, compress_type, compresslevel)

    def writestr(
        self,
        zinfo_or_arcname: Union[str, CabInfo],
        data: Union[str, bytes],
        compress_type: Optional[int] = None,
        compresslevel: Optional[int] = None,
    ):
        """Write a string or bytes into the archive."""
        if self.mode not in ("w", "a"):
            raise ValueError("CAB file must be opened for writing")

        if isinstance(zinfo_or_arcname, str):
            arcname = zinfo_or_arcname
        else:
            arcname = zinfo_or_arcname.filename

        if isinstance(data, str):
            data = data.encode("utf-8")

        # Create temporary file
        temp_file = os.path.join(self._temp_dir, arcname)
        os.makedirs(os.path.dirname(temp_file), exist_ok=True)

        with open(temp_file, "wb") as f:
            f.write(data)

        # Add to folder unit (store the actual temp file path and data)
        self._folder_unit.filename_list.append(temp_file)
        self._folder_unit.filedata_list.append(data)

        # Update internal data structures
        file_info = CabInfo(arcname, len(data))
        self._file_list.append(file_info)
        self._file_data[arcname] = data

    def close(self):
        """Close the archive file."""
        if self._closed:
            return

        if self.mode in ("w", "a") and (self._folder_unit.filename_list or self._folder_unit.filedata_list):
            try:
                # Ensure we have actual data to write
                if not self._folder_unit.filedata_list:
                    # Read data from temp files if needed
                    for temp_file in self._folder_unit.filename_list:
                        if os.path.exists(temp_file):
                            with open(temp_file, "rb") as f:
                                self._folder_unit.filedata_list.append(f.read())

                # Create CAB file using the manager
                self._manager.create_cab(cab_folders=[self._folder_unit], cab_name=os.path.basename(self.filename))

                # Write to disk
                output_dir = os.path.dirname(self.filename) or "."
                self._manager.flush_cabset_to_disk(output_dir)

            except Exception as e:
                raise CABException(f"Failed to write CAB file: {e}")

        # Clean up temporary directory
        if self._temp_dir and os.path.exists(self._temp_dir):
            shutil.rmtree(self._temp_dir)

        self._closed = True

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def __del__(self):
        """Destructor to ensure cleanup."""
        if not self._closed:
            self.close()
