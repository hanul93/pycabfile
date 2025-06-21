"""
CAB file writer module

This module provides functionality to create and write CAB files,
managing the file structure and data organization.
"""

import os
import tempfile
from itertools import groupby
from .cab_structs import CABFileFormat, CFHEADER, CFFOLDER, CFFILE, CFDATA
from .cab_reader import CABException


class CABFolderUnit(object):
    """
    Container for a group of files to be stored in a CAB folder

    This class represents a logical folder within a CAB file,
    containing a list of files and their data.
    """

    def __init__(self, name="", filename_list=None):
        """Initialize CAB folder unit"""
        self.filename_list = filename_list or []
        self.name = name
        self.compression = None
        # One-to-one relation between filedata_list and filename_list
        self.filedata_list = []

    def __eq__(self, other):
        """Check equality based on file basenames"""
        if isinstance(other, self.__class__):
            return set(os.path.basename(_) for _ in self.filename_list) & set(
                os.path.basename(_) for _ in other.filename_list
            ) == set(os.path.basename(_) for _ in self.filename_list)
        return False

    def __ne__(self, other):
        """Check inequality"""
        return not self.__eq__(other)


class CABFile(CABFileFormat):
    """
    CAB file representation and management

    This class handles the creation and management of a single CAB file,
    including headers, folders, files, and data blocks.
    """

    @property
    def slack(self):
        """Available space remaining in the CAB file"""
        return self.max_data - self.size

    def __init__(self, parameters=None):
        """Initialize CAB file with given parameters"""
        if parameters is None:
            parameters = {}

        self.cab_filename = parameters.get("cab_filename", "output.cab")
        self.max_data = parameters.get("max_data", 1474 * 1024)  # Default 1.44MB
        self.cabset = parameters.get("cabset", None)
        self.size = 0

        index_in_set = parameters.get("index_in_set", 0)
        cfdata_reserve = parameters.get("cfdata_reserve", 0)
        cfheader_reserve = parameters.get("cfheader_reserve", 0)
        cffolder_reserve = parameters.get("cffolder_reserve", 0)

        # Set flags based on reserve requirements
        flags = CFHEADER.cfhdrRESERVE_PRESENT if any([cfheader_reserve, cffolder_reserve, cfdata_reserve]) else 0

        reserve = {"cbCFHeader": cfheader_reserve, "cbCFFolder": cffolder_reserve, "cbCFData": cfdata_reserve}

        self.cfheader = CFHEADER(flags=flags, reserve=reserve)
        self.cfheader.iCabinet = index_in_set

        self.cffolder_list = []
        self.cffile_list = []
        self.cfdata_list = []

        # Helper for folder ID generation
        self.folder_id = 0

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

    def _create_cffolder(self, folder_name):
        """Create a new CAB folder"""
        new_cffolder = CFFOLDER(self.cfheader, folder_id=self.folder_id)
        new_cffolder.name = folder_name
        self.folder_id += 1
        self.cfheader.add_folder(cffolder=new_cffolder)
        return new_cffolder

    def update_fields(self):
        """Update calculated fields in CAB structures"""
        self._update_uoffFolderStart()
        self._update_coffCabStart()
        self._update_cbCabinet()
        self._update_coffFiles()

    def add_file(self, folder_name, filename, total_len, data):
        """Add a file to the CAB"""
        if self.size == self.max_data:
            raise CABException("CAB file is full")

        if (self.size + len(data)) > self.max_data:
            raise CABException("CAB file doesn't have enough space for the data")

        if isinstance(data, str):
            data = data.encode("utf-8")

        # Find or create folder
        try:
            cffolder = next(_ for _ in self.cffolder_list if _.name == folder_name)
        except StopIteration:
            cffolder = self._create_cffolder(folder_name)
            self.cffolder_list.append(cffolder)

        # Create file entry
        cffile = CFFILE(cffolder=cffolder, total_len=total_len, filename=filename)
        self.cffile_list.append(cffile)

        # Split data into chunks if necessary (max 0x8000 bytes per CFDATA)
        if len(data) > 0x8000:
            data_chunks = [data[i : i + 0x8000] for i in range(0, len(data), 0x8000)]
            for data_chunk in data_chunks:
                cfdata = CFDATA(cffolder=cffolder, data=data_chunk)
                self.cfdata_list.append(cfdata)
                cffolder.add_data(cfdata)
        else:
            cfdata = CFDATA(cffolder=cffolder, data=data)
            self.cfdata_list.append(cfdata)
            cffolder.add_data(cfdata)

        cffolder.add_file(cffile)
        self.update_fields()
        self.size += len(data)

    def _update_uoffFolderStart(self):
        """Update uncompressed byte offset of start of every file's data"""
        for key, group in groupby(self.cffile_list, lambda x: x.cffolder.folder_id):
            offset = 0
            for cffile in group:
                cffile.uoffFolderStart = offset
                offset += cffile.cbFile

    def _update_coffCabStart(self):
        """Update absolute file offset of first CFDATA block for every folder"""
        data_start = (
            len(self.cfheader)
            + sum([len(cffolder) for cffolder in self.cffolder_list])
            + sum([len(cffile) for cffile in self.cffile_list])
        )

        if self.cffolder_list:
            self.cffolder_list[0].coffCabStart = data_start

            for index, cffolder in enumerate(self.cffolder_list[1:]):
                data_start += sum([len(cfdata) for cfdata in self.cffolder_list[index].cfdata_list])
                cffolder.coffCabStart = data_start

    def _update_cbCabinet(self):
        """Update total size of this cabinet file in bytes"""
        self.cfheader.cbCabinet = len(self)

    def _update_coffFiles(self):
        """Update offset of the first CFFILE entry"""
        self.cfheader.coffFiles = len(self.cfheader) + sum([len(cffolder) for cffolder in self.cffolder_list])
        # Also update the files count
        self.cfheader.cFiles = len(self.cffile_list)

    def __bytes__(self):
        """Convert CAB file to binary representation"""
        data = bytes(self.cfheader)

        for cffolder in self.cffolder_list:
            data += bytes(cffolder)

        for cffile in self.cffile_list:
            data += bytes(cffile)

        for cfdata in self.cfdata_list:
            data += bytes(cfdata)

        return data

    def __len__(self):
        """Calculate total CAB file size"""
        return (
            len(self.cfheader)
            + sum([len(cffolder) for cffolder in self.cffolder_list])
            + sum([len(cffile) for cffile in self.cffile_list])
            + sum([len(cfdata) for cfdata in self.cfdata_list])
        )

    def __str__(self):
        """String representation for debugging"""
        return f"CABFile: {self.cab_filename}, {len(self.cffile_list)} files, {self.size} bytes"


class CABSet(object):
    """
    Manager for a set of CAB files

    This class handles the creation and management of multiple CAB files
    that together form a complete cabinet set.
    """

    def __init__(self, parameters=None):
        """Initialize CAB set with parameters"""
        if parameters is None:
            parameters = {}

        self.output_name = parameters.get("output_name", "output_[x].cab")
        self.cab_folders = parameters.get("cab_folders", [])
        self.max_data_per_cab = parameters.get("max_data_per_cab", 1474 * 1024)
        self.cfheader_reserve = parameters.get("cfheader_reserve", 0)
        self.cffolder_reserve = parameters.get("cffolder_reserve", 0)
        self.cfdata_reserve = parameters.get("cfdata_reserve", 0)

        self.cab_list = []
        self.current_cab_index = 0

    def _create_new_cabfile(self):
        """Create a new CAB file in the set"""
        filename = self.output_name.replace("[x]", str(self.current_cab_index))

        parameters = {
            "cab_filename": filename,
            "max_data": self.max_data_per_cab,
            "cabset": self,
            "index_in_set": self.current_cab_index,
            "cfheader_reserve": self.cfheader_reserve,
            "cffolder_reserve": self.cffolder_reserve,
            "cfdata_reserve": self.cfdata_reserve,
        }

        new_cab = CABFile(parameters=parameters)
        self.cab_list.append(new_cab)
        self.current_cab_index += 1

        return new_cab

    def _get_cab_with_free_space(self):
        """Get a CAB file with available space, creating if necessary"""
        if not self.cab_list:
            return self._create_new_cabfile()

        current_cab = self.cab_list[-1]
        if current_cab.slack > 0:
            return current_cab
        else:
            return self._create_new_cabfile()

    def __iter__(self):
        """Iterate over CAB files in the set"""
        return iter(self.cab_list)

    def create_set(self):
        """Create the complete CAB set from folder units"""
        for folder_unit in self.cab_folders:
            for i, filename in enumerate(folder_unit.filename_list):
                # Read file data if not already present
                if i >= len(folder_unit.filedata_list):
                    with open(filename, "rb") as f:
                        file_data = f.read()
                    folder_unit.filedata_list.append(file_data)
                else:
                    file_data = folder_unit.filedata_list[i]

                # Use basename as the archive name
                archive_name = os.path.basename(filename)

                # Find a CAB with enough space
                while True:
                    current_cab = self._get_cab_with_free_space()

                    try:
                        current_cab.add_file(
                            folder_name=folder_unit.name,
                            filename=archive_name,
                            total_len=len(file_data),
                            data=file_data,
                        )
                        break
                    except CABException:
                        # Current CAB is full, create a new one
                        continue


class CABManager(object):
    """
    High-level CAB file manager

    This class provides a simple interface for creating and managing CAB files.
    """

    def __init__(self):
        """Initialize CAB manager"""
        self.cab_set = None
        self.debug_file = "debug.txt"

    def create_cab(
        self,
        cab_folders,
        cab_size=1474 * 1024,
        cfheader_reserve=0,
        cffolder_reserve=0,
        cfdata_reserve=0,
        cab_name="out_[x].cab",
    ):
        """Create a CAB set with specified parameters"""
        parameters = {
            "output_name": cab_name,
            "cab_folders": cab_folders,
            "max_data_per_cab": cab_size,
            "cfheader_reserve": cfheader_reserve,
            "cffolder_reserve": cffolder_reserve,
            "cfdata_reserve": cfdata_reserve,
        }

        self.cab_set = CABSet(parameters=parameters)
        self.cab_set.create_set()

    def flush_cabset_to_disk(self, output_dir=None, debug=False):
        """Write CAB set to disk"""
        if output_dir is None:
            output_dir = os.getcwd()

        if debug:
            with open(os.path.join(output_dir, self.debug_file), "wt") as f:
                for index, cab in enumerate(self.cab_set):
                    f.write(str(cab) + "\n")

        # Write the CAB files
        for index, cab in enumerate(self.cab_set):
            output_path = os.path.join(output_dir, cab.cab_filename)
            with open(output_path, "wb") as f:
                f.write(bytes(cab))
