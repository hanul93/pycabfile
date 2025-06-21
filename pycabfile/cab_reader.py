"""
CAB file reader module

This module provides functionality to read and parse CAB files,
extracting their structure and content.
"""

import struct
from .cab_structs import CABFileFormat, CFHEADER, CFFOLDER, CFFILE, CFDATA


class CABException(Exception):
    """Exception raised for CAB file related errors"""

    pass


class CabReader(CABFileFormat):
    """
    CAB file reader class

    This class can read valid CAB files and extract their structure
    including headers, folders, files, and data blocks.
    """

    def __init__(self, filename):
        """Initialize CAB reader with filename"""
        self.filename = filename
        self.cfheader = None
        self.cffolder_list = []
        self.cffile_list = []
        self.cfdata_list = []

        self._read_cab()

    def get_cfheader(self):
        """Return the CAB header"""
        return self.cfheader

    def get_cffolder_list(self):
        """Return list of CAB folders"""
        return self.cffolder_list

    def get_cffile_list(self):
        """Return list of CAB files"""
        return self.cffile_list

    def get_cfdata_list(self):
        """Return list of CAB data blocks"""
        return self.cfdata_list

    def _read_dword(self, handle):
        """Read a 32-bit unsigned integer from file"""
        return struct.unpack("<I", handle.read(4))[0]

    def _read_word(self, handle):
        """Read a 16-bit unsigned integer from file"""
        return struct.unpack("<H", handle.read(2))[0]

    def _read_byte(self, handle):
        """Read an 8-bit unsigned integer from file"""
        return struct.unpack("<B", handle.read(1))[0]

    def read_cfheader(self, handle):
        """Read and parse CAB file header"""
        parameters = {}

        # Read signature
        signature = handle.read(4)
        if signature != b"MSCF":
            raise CABException("Not a valid CAB file - invalid signature")

        # Read basic header fields
        parameters["reserved1"] = self._read_dword(handle)
        parameters["cbCabinet"] = self._read_dword(handle)
        parameters["reserved2"] = self._read_dword(handle)
        parameters["coffFiles"] = self._read_dword(handle)
        parameters["reserved3"] = self._read_dword(handle)
        parameters["versionMinor"] = self._read_byte(handle)
        parameters["versionMajor"] = self._read_byte(handle)
        parameters["cFolders"] = self._read_word(handle)
        parameters["cFiles"] = self._read_word(handle)
        parameters["flags"] = self._read_word(handle)
        parameters["setID"] = self._read_word(handle)
        parameters["iCabinet"] = self._read_word(handle)

        # Read optional reserve fields
        if parameters["flags"] & CFHEADER.cfhdrRESERVE_PRESENT:
            parameters["cbCFHeader"] = self._read_word(handle)
            parameters["cbCFFolder"] = self._read_byte(handle)
            parameters["cbCFData"] = self._read_byte(handle)
            parameters["abReserve"] = handle.read(parameters["cbCFHeader"])
        else:
            parameters["cbCFHeader"] = 0
            parameters["cbCFFolder"] = 0
            parameters["cbCFData"] = 0
            parameters["abReserve"] = b""

        # Read previous cabinet info if present
        if parameters["flags"] & CFHEADER.cfhdrPREV_CABINET:
            szCabinetPrev = handle.read(1)
            while szCabinetPrev[-1:] != b"\x00":
                szCabinetPrev += handle.read(1)
            parameters["szCabinetPrev"] = szCabinetPrev

            szDiskPrev = handle.read(1)
            while szDiskPrev[-1:] != b"\x00":
                szDiskPrev += handle.read(1)
            parameters["szDiskPrev"] = szDiskPrev
        else:
            parameters["szCabinetPrev"] = b""
            parameters["szDiskPrev"] = b""

        # Read next cabinet info if present
        if parameters["flags"] & CFHEADER.cfhdrNEXT_CABINET:
            szCabinetNext = handle.read(1)
            while szCabinetNext[-1:] != b"\x00":
                szCabinetNext += handle.read(1)
            parameters["szCabinetNext"] = szCabinetNext

            szDiskNext = handle.read(1)
            while szDiskNext[-1:] != b"\x00":
                szDiskNext += handle.read(1)
            parameters["szDiskNext"] = szDiskNext
        else:
            parameters["szCabinetNext"] = b""
            parameters["szDiskNext"] = b""

        return CFHEADER.create_from_parameters(parameters=parameters)

    def read_folders(self, handle):
        """Read and parse CAB folder entries"""
        result = []
        for i in range(self.cfheader.cFolders):
            parameters = {}
            parameters["coffCabStart"] = self._read_dword(handle)
            parameters["cCFData"] = self._read_word(handle)
            parameters["typeCompress"] = self._read_word(handle)

            # Read reserved area if present
            if self.cfheader.flags & CFHEADER.cfhdrRESERVE_PRESENT:
                parameters["abReserve"] = handle.read(self.cfheader.cbCFFolder)
            else:
                parameters["abReserve"] = b""

            result.append(CFFOLDER.create_from_parameters(parameters=parameters))

        return result

    def read_files(self, handle):
        """Read and parse CAB file entries"""
        result = []
        for i in range(self.cfheader.cFiles):
            parameters = {}
            parameters["cbFile"] = self._read_dword(handle)
            parameters["uoffFolderStart"] = self._read_dword(handle)
            parameters["iFolder"] = self._read_word(handle)
            parameters["date"] = self._read_word(handle)
            parameters["time"] = self._read_word(handle)
            parameters["attribs"] = self._read_word(handle)

            # Read null-terminated filename
            szName = handle.read(1)
            while szName[-1:] != b"\x00":
                szName += handle.read(1)
            parameters["szName"] = szName

            result.append(CFFILE.create_from_parameters(parameters=parameters))

        return result

    def read_data(self, handle):
        """Read and parse CAB data blocks"""
        result = []
        # Calculate total number of data blocks across all folders
        data_count = sum([cffolder.cCFData for cffolder in self.cffolder_list])

        for i in range(data_count):
            parameters = {}
            parameters["csum"] = self._read_dword(handle)
            parameters["cbData"] = self._read_word(handle)
            parameters["cbUncomp"] = self._read_word(handle)

            # Read reserved area if present
            if self.cfheader.flags & CFHEADER.cfhdrRESERVE_PRESENT:
                parameters["abReserve"] = handle.read(self.cfheader.cbCFData)
            else:
                parameters["abReserve"] = b""

            # Read compressed data
            parameters["ab"] = handle.read(parameters["cbData"])

            result.append(CFDATA.create_from_parameters(parameters=parameters))

        return result

    def _read_cab(self):
        """Read and parse the entire CAB file"""
        try:
            with open(self.filename, "rb") as f:
                # Read header first
                self.cfheader = self.read_cfheader(handle=f)

                # Read folders
                self.cffolder_list = self.read_folders(handle=f)

                # Read file entries
                self.cffile_list = self.read_files(handle=f)

                # Read data blocks
                self.cfdata_list = self.read_data(handle=f)

        except Exception as e:
            raise CABException(f"Failed to read CAB file '{self.filename}': {str(e)}")

    def extract_file_data(self, file_index):
        """Extract data for a specific file by index"""
        if file_index >= len(self.cffile_list):
            raise CABException(f"File index {file_index} out of range")

        cffile = self.cffile_list[file_index]
        file_data = b""
        file_data_len = 0

        # Find the starting data block for this file
        # This is a simplified approach - in reality, CAB files can be more complex
        data_index = 0

        # Sum up data blocks until we have all the file data
        while file_data_len < cffile.cbFile and data_index < len(self.cfdata_list):
            current_cfdata = self.cfdata_list[data_index]

            # Take only what we need for this file
            remaining_bytes = cffile.cbFile - file_data_len
            if remaining_bytes >= current_cfdata.cbUncomp:
                # Take the entire data block
                file_data += current_cfdata.ab
                file_data_len += current_cfdata.cbUncomp
            else:
                # Take only the remaining bytes needed
                file_data += current_cfdata.ab[:remaining_bytes]
                file_data_len += remaining_bytes

            data_index += 1

        # Handle the case where we took too much data (shared data blocks)
        if len(file_data) > cffile.cbFile:
            file_data = file_data[: cffile.cbFile]

        return file_data

    def get_file_list(self):
        """Get list of filenames in the CAB"""
        filenames = []
        for cffile in self.cffile_list:
            # Decode filename, removing null terminator
            filename = cffile.szName.decode("utf-8").rstrip("\x00")
            filenames.append(filename)
        return filenames

    def extract_all_files(self):
        """Extract all files and return as dictionary"""
        files_data = {}

        # Simple extraction assuming files are stored sequentially
        data_index = 0

        for file_index, cffile in enumerate(self.cffile_list):
            filename = cffile.szName.decode("utf-8").rstrip("\x00")
            file_data = b""
            file_data_len = 0

            # Extract data for this file
            while file_data_len < cffile.cbFile and data_index < len(self.cfdata_list):
                current_cfdata = self.cfdata_list[data_index]

                remaining_bytes = cffile.cbFile - file_data_len
                if remaining_bytes >= current_cfdata.cbUncomp:
                    file_data += current_cfdata.ab
                    file_data_len += current_cfdata.cbUncomp
                    data_index += 1
                else:
                    file_data += current_cfdata.ab[:remaining_bytes]
                    file_data_len += remaining_bytes
                    # Don't increment data_index as we might need the rest for next file
                    break

            # Ensure we don't have extra data
            if len(file_data) > cffile.cbFile:
                file_data = file_data[: cffile.cbFile]

            files_data[filename] = file_data

        return files_data

    def get_file_info(self, filename):
        """Get information about a specific file"""
        for cffile in self.cffile_list:
            file_name = cffile.szName.decode("utf-8").rstrip("\x00")
            if file_name == filename:
                return {
                    "filename": file_name,
                    "size": cffile.cbFile,
                    "date": cffile.date,
                    "time": cffile.time,
                    "attributes": cffile.attribs,
                }
        return None

    def __str__(self):
        """String representation for debugging"""
        data = str(self.cfheader) + "\n"
        for folder in self.cffolder_list:
            data += str(folder) + "\n"
        for file in self.cffile_list:
            data += str(file) + "\n"
        for data_block in self.cfdata_list:
            data += str(data_block) + "\n"
        return data
