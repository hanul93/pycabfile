# coding=utf-8
"""
CAB file format structures and definitions

This module contains the low-level CAB file format structures based on Microsoft's
CAB format specification.
"""

import struct
import datetime
from abc import ABCMeta, abstractmethod
from weakref import WeakKeyDictionary


class DWORDValue(object):
    """A descriptor for DWORD values (32-bit unsigned integer)"""

    def __init__(self):
        self.data = WeakKeyDictionary()

    def __get__(self, obj, type):
        return struct.unpack("<I", self.data.get(obj))[0]

    def __set__(self, obj, value):
        try:
            v = struct.pack("<I", value)
            self.data[obj] = v
        except struct.error as e:
            raise ValueError("Only DWORD values are allowed: %08x" % value)


class WORDValue(object):
    """A descriptor for WORD values (16-bit unsigned integer)"""

    def __init__(self):
        self.data = WeakKeyDictionary()

    def __get__(self, obj, type):
        return struct.unpack("<H", self.data.get(obj))[0]

    def __set__(self, obj, value):
        try:
            # Handle float division results in Python 3
            if isinstance(value, float):
                value = int(value)
            v = struct.pack("<H", value)
            self.data[obj] = v
        except struct.error as e:
            raise ValueError("Only WORD values are allowed: %04x" % value)


class BYTEValue(object):
    """A descriptor for BYTE values (8-bit unsigned integer)"""

    def __init__(self):
        self.data = WeakKeyDictionary()

    def __get__(self, obj, type):
        return struct.unpack("<B", self.data.get(obj))[0]

    def __set__(self, obj, value):
        try:
            v = struct.pack("<B", value)
            self.data[obj] = v
        except struct.error as e:
            raise ValueError("Only BYTE values are allowed: %02x" % value)


class CABFileFormat(object, metaclass=ABCMeta):
    """
    Abstract base class providing common methods for CAB file management
    """

    @abstractmethod
    def get_cfheader(self):
        pass

    @abstractmethod
    def get_cffolder_list(self):
        pass

    @abstractmethod
    def get_cffile_list(self):
        pass

    @abstractmethod
    def get_cfdata_list(self):
        pass


class CFHEADER(object):
    """
    CAB file header structure

    Contains metadata about the CAB file including signature, size,
    folder and file counts, and optional fields.
    """

    # Flag values
    cfhdrPREV_CABINET = 0x0001
    cfhdrNEXT_CABINET = 0x0002
    cfhdrRESERVE_PRESENT = 0x0004

    @property
    def signature(self):
        return self._signature

    @signature.setter
    def signature(self, value):
        if len(value) == 4:
            self._signature = value
        else:
            self._signature = "MSCF"

    # Basic header fields
    reserved1 = DWORDValue()
    cbCabinet = DWORDValue()
    reserved2 = DWORDValue()
    coffFiles = DWORDValue()
    reserved3 = DWORDValue()
    versionMinor = BYTEValue()
    versionMajor = BYTEValue()
    cFolders = WORDValue()
    cFiles = WORDValue()
    flags = WORDValue()
    setID = WORDValue()
    iCabinet = WORDValue()

    # Optional fields
    cbCFHeader = WORDValue()
    cbCFFolder = BYTEValue()
    cbCFData = BYTEValue()

    @property
    def abReserve(self):
        return getattr(self, "_abReserve", b"")

    @abReserve.setter
    def abReserve(self, value):
        self._abReserve = value

    @property
    def szCabinetPrev(self):
        return getattr(self, "_szCabinetPrev", b"")

    @szCabinetPrev.setter
    def szCabinetPrev(self, value):
        self._szCabinetPrev = value

    @property
    def szDiskPrev(self):
        return getattr(self, "_szDiskPrev", b"")

    @szDiskPrev.setter
    def szDiskPrev(self, value):
        self._szDiskPrev = value

    @property
    def szCabinetNext(self):
        return getattr(self, "_szCabinetNext", b"")

    @szCabinetNext.setter
    def szCabinetNext(self, value):
        self._szCabinetNext = value

    @property
    def szDiskNext(self):
        return getattr(self, "_szDiskNext", b"")

    @szDiskNext.setter
    def szDiskNext(self, value):
        self._szDiskNext = value

    def __init__(self, flags=0, reserve=None):
        """Initialize CAB header with default values"""
        if reserve is None:
            reserve = {"cbCFHeader": 0, "cbCFFolder": 0, "cbCFData": 0}

        # Set signature
        self.signature = "MSCF"

        # Set basic fields
        self.reserved1 = 0
        self.cbCabinet = 0
        self.reserved2 = 0
        self.coffFiles = 0
        self.reserved3 = 0
        self.versionMinor = 3
        self.versionMajor = 1
        self.cFolders = 0
        self.cFiles = 0
        self.flags = flags
        self.setID = 0
        self.iCabinet = 0

        # Set optional fields
        self.cbCFHeader = reserve.get("cbCFHeader", 0)
        self.cbCFFolder = reserve.get("cbCFFolder", 0)
        self.cbCFData = reserve.get("cbCFData", 0)

        # Initialize optional byte arrays
        self.abReserve = b""
        self.szCabinetPrev = b""
        self.szDiskPrev = b""
        self.szCabinetNext = b""
        self.szDiskNext = b""

    @classmethod
    def create_from_parameters(cls, parameters=None):
        """Create CFHEADER from parameter dictionary"""
        if parameters is None:
            parameters = {}

        reserve = {
            "cbCFHeader": parameters.get("cbCFHeader", 0),
            "cbCFFolder": parameters.get("cbCFFolder", 0),
            "cbCFData": parameters.get("cbCFData", 0),
        }

        header = cls(flags=parameters.get("flags", 0), reserve=reserve)

        # Set all parameters
        for key, value in parameters.items():
            if hasattr(header, key):
                setattr(header, key, value)

        return header

    def add_folder(self, cffolder):
        """Add a folder and update folder count"""
        self.cFolders += 1

    def __bytes__(self):
        """Convert header to binary representation"""
        data = b"MSCF"  # signature
        data += struct.pack("<I", self.reserved1)
        data += struct.pack("<I", self.cbCabinet)
        data += struct.pack("<I", self.reserved2)
        data += struct.pack("<I", self.coffFiles)
        data += struct.pack("<I", self.reserved3)
        data += struct.pack("<B", self.versionMinor)
        data += struct.pack("<B", self.versionMajor)
        data += struct.pack("<H", self.cFolders)
        data += struct.pack("<H", self.cFiles)
        data += struct.pack("<H", self.flags)
        data += struct.pack("<H", self.setID)
        data += struct.pack("<H", self.iCabinet)

        # Optional fields
        if self.flags & self.cfhdrRESERVE_PRESENT:
            data += struct.pack("<H", self.cbCFHeader)
            data += struct.pack("<B", self.cbCFFolder)
            data += struct.pack("<B", self.cbCFData)
            data += self.abReserve

        if self.flags & self.cfhdrPREV_CABINET:
            data += self.szCabinetPrev
            data += self.szDiskPrev

        if self.flags & self.cfhdrNEXT_CABINET:
            data += self.szCabinetNext
            data += self.szDiskNext

        return data

    def __len__(self):
        """Calculate header size"""
        size = 36  # Basic header size

        if self.flags & self.cfhdrRESERVE_PRESENT:
            size += 4 + len(self.abReserve)

        if self.flags & self.cfhdrPREV_CABINET:
            size += len(self.szCabinetPrev) + len(self.szDiskPrev)

        if self.flags & self.cfhdrNEXT_CABINET:
            size += len(self.szCabinetNext) + len(self.szDiskNext)

        return size

    def __str__(self):
        """String representation for debugging"""
        return f"CFHEADER: {self.cFolders} folders, {self.cFiles} files"


class CFFOLDER(object):
    """CAB folder structure containing compression and data information"""

    # Compression types
    tcompMASK_TYPE = 0x000F
    tcompTYPE_NONE = 0x0000
    tcompTYPE_MSZIP = 0x0001
    tcompTYPE_QUANTUM = 0x0002
    tcompTYPE_LZX = 0x0003

    coffCabStart = DWORDValue()
    cCFData = WORDValue()
    typeCompress = WORDValue()

    @property
    def abReserve(self):
        return getattr(self, "_abReserve", b"")

    @abReserve.setter
    def abReserve(self, value):
        self._abReserve = value

    @property
    def name(self):
        return getattr(self, "_name", "")

    @name.setter
    def name(self, value):
        self._name = value

    def __init__(self, cfheader=None, folder_id=0):
        """Initialize CAB folder"""
        self.cfheader = cfheader
        self.folder_id = folder_id
        self.coffCabStart = 0
        self.cCFData = 0
        self.typeCompress = self.tcompTYPE_NONE
        self.abReserve = b""
        self.name = f"folder_{folder_id}"

        # Lists to track associated files and data
        self.cffile_list = []
        self.cfdata_list = []

    @classmethod
    def create_from_parameters(cls, parameters=None):
        """Create CFFOLDER from parameter dictionary"""
        if parameters is None:
            parameters = {}

        folder = cls()
        for key, value in parameters.items():
            if hasattr(folder, key):
                setattr(folder, key, value)

        return folder

    def add_data(self, cfdata):
        """Add data block and update count"""
        self.cfdata_list.append(cfdata)
        self.cCFData += 1

    def add_file(self, cffile):
        """Add file to this folder"""
        self.cffile_list.append(cffile)

    def __bytes__(self):
        """Convert folder to binary representation"""
        data = struct.pack("<I", self.coffCabStart)
        data += struct.pack("<H", self.cCFData)
        data += struct.pack("<H", self.typeCompress)
        data += self.abReserve
        return data

    def __len__(self):
        """Calculate folder size"""
        return 8 + len(self.abReserve)

    def __str__(self):
        """String representation for debugging"""
        return f"CFFOLDER: {self.name}, {self.cCFData} data blocks"


class CFFILE(object):
    """CAB file entry containing file metadata"""

    # iFolder values
    ifoldTHIS_CABINET = 0x0000
    ifoldCONTINUED_FROM_PREV = 0xFFFD
    ifoldCONTINUED_TO_NEXT = 0xFFFE
    ifoldCONTINUED_PREV_AND_NEXT = 0xFFFF

    # Attribute flags
    _A_RDONLY = 0x01
    _A_HIDDEN = 0x02
    _A_SYSTEM = 0x04
    _A_ARCH = 0x20
    _A_EXEC = 0x40
    _A_NAME_IS_UTF = 0x80

    cbFile = DWORDValue()
    uoffFolderStart = DWORDValue()
    iFolder = WORDValue()
    date = WORDValue()
    time = WORDValue()
    attribs = WORDValue()

    @property
    def szName(self):
        return getattr(self, "_szName", b"")

    @szName.setter
    def szName(self, value):
        if isinstance(value, str):
            value = value.encode("utf-8") + b"\x00"
        self._szName = value

    def __init__(self, cffolder=None, total_len=0, filename=""):
        """Initialize CAB file entry"""
        self.cffolder = cffolder
        self.cbFile = total_len
        self.uoffFolderStart = 0
        self.iFolder = cffolder.folder_id if cffolder else 0

        # Set current date/time
        now = datetime.datetime.now()
        self.date = ((now.year - 1980) << 9) + (now.month << 5) + now.day
        self.time = (now.hour << 11) + (now.minute << 5) + (now.second // 2)

        self.attribs = self._A_ARCH
        self.szName = filename

    @classmethod
    def create_from_parameters(cls, parameters=None):
        """Create CFFILE from parameter dictionary"""
        if parameters is None:
            parameters = {}

        cffile = cls()
        for key, value in parameters.items():
            if hasattr(cffile, key):
                setattr(cffile, key, value)

        return cffile

    def __bytes__(self):
        """Convert file entry to binary representation"""
        data = struct.pack("<I", self.cbFile)
        data += struct.pack("<I", self.uoffFolderStart)
        data += struct.pack("<H", self.iFolder)
        data += struct.pack("<H", self.date)
        data += struct.pack("<H", self.time)
        data += struct.pack("<H", self.attribs)
        data += self.szName
        return data

    def __len__(self):
        """Calculate file entry size"""
        return 16 + len(self.szName)

    def __str__(self):
        """String representation for debugging"""
        name = self.szName.decode("utf-8").rstrip("\x00") if self.szName else "unnamed"
        return f"CFFILE: {name}, {self.cbFile} bytes"


class CFDATA(object):
    """CAB data block containing compressed file data"""

    csum = DWORDValue()
    cbData = WORDValue()
    cbUncomp = WORDValue()

    @property
    def abReserve(self):
        return getattr(self, "_abReserve", b"")

    @abReserve.setter
    def abReserve(self, value):
        self._abReserve = value

    @property
    def ab(self):
        return getattr(self, "_ab", b"")

    @ab.setter
    def ab(self, value):
        self._ab = value

    def __init__(self, cffolder=None, data=b""):
        """Initialize CAB data block"""
        self.cffolder = cffolder
        self.csum = 0  # Checksum (not implemented)

        if isinstance(data, str):
            data = data.encode("utf-8")

        self.ab = data
        self.cbData = len(data)
        self.cbUncomp = len(data)  # No compression for now
        self.abReserve = b""

    @classmethod
    def create_from_parameters(cls, parameters=None):
        """Create CFDATA from parameter dictionary"""
        if parameters is None:
            parameters = {}

        cfdata = cls()
        for key, value in parameters.items():
            if hasattr(cfdata, key):
                setattr(cfdata, key, value)

        return cfdata

    def __bytes__(self):
        """Convert data block to binary representation"""
        data = struct.pack("<I", self.csum)
        data += struct.pack("<H", self.cbData)
        data += struct.pack("<H", self.cbUncomp)
        data += self.abReserve
        data += self.ab
        return data

    def __len__(self):
        """Calculate data block size"""
        return 8 + len(self.abReserve) + len(self.ab)

    def __str__(self):
        """String representation for debugging"""
        return f"CFDATA: {self.cbUncomp} bytes uncompressed, {self.cbData} bytes stored"
