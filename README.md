<p align="center">
	<img src="https://github.com/hanul93/pycabfile/blob/1.0.1/doc/pycabfile_logo.png" width="256" alt="pycabfile logo">
</p>

<p align="center">
	[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
	![Platform](https://img.shields.io/badge/platform-windows-lightgrey.svg)
	![Platform](https://img.shields.io/badge/platform-linux-lightgrey.svg)
	![Platform](https://img.shields.io/badge/platform-mac-lightgrey.svg)<br>
	![Language](https://img.shields.io/badge/Python-V3.10+-brightgreen)
</p>

## pycabfile

A Python library for handling Microsoft Cabinet files with zipfile-compatible interface

**Python 3.10+ Compatible** - This library provides a zipfile-like interface for creating and extracting CAB files, fully compatible with Python 3.10 and later versions.

## Features

- **zipfile-compatible interface** - Use the same methods as Python's zipfile module
- Create and extract CAB files with simple API
- Support for binary and text files
- Unicode filename support
- Context manager support (with statement)
- No external dependencies required
- **Python 3.10+ support** - Fully compatible with modern Python versions

## Installation

```bash
pip install pycabfile

# or Install from source
pip install git+https://github.com/hanul93/pycabfile.git
```

## Quick Start

The interface is designed to be identical to Python's zipfile module:

### Creating CAB Files

```python
from pycabfile import CabFile

# Create a new CAB file
with CabFile('example.cab', 'w') as cab:
    # Add files from disk
    cab.write('document.txt', 'docs/document.txt')  # arcname is optional
    cab.write('image.jpg')

    # Add data directly
    cab.writestr('readme.txt', 'This is a README file')
    cab.writestr('config.json', '{"version": "1.0"}')
```

### Reading CAB Files

```python
from pycabfile import CabFile

# Read an existing CAB file
with CabFile('example.cab', 'r') as cab:
    # List all files
    file_list = cab.namelist()
    print(f"Files in CAB: {file_list}")

    # Read file content
    content = cab.read('readme.txt')
    print(content.decode('utf-8'))

    # Get file information
    info = cab.getinfo('document.txt')
    print(f"File size: {info.file_size} bytes")

    # Extract files
    cab.extract('document.txt', 'output/')  # Extract single file
    cab.extractall('output/')  # Extract all files
```

### Advanced Usage

```python
from pycabfile import CabFile, CabInfo

# Append to existing CAB file
with CabFile('example.cab', 'a') as cab:
    cab.writestr('appended.txt', 'This was added later')

# Working with file-like objects
with CabFile('example.cab', 'r') as cab:
    with cab.open('document.txt') as f:
        data = f.read()
        print(data.decode('utf-8'))
```

## Comparison with zipfile

The API is designed to be a drop-in replacement for zipfile in most cases:

| zipfile                            | pycabfile                            |
| ---------------------------------- | ------------------------------------ |
| `zipfile.ZipFile('file.zip', 'w')` | `pycabfile.CabFile('file.cab', 'w')` |
| `zf.write('file.txt')`             | `cf.write('file.txt')`               |
| `zf.writestr('name', data)`        | `cf.writestr('name', data)`          |
| `zf.read('name')`                  | `cf.read('name')`                    |
| `zf.namelist()`                    | `cf.namelist()`                      |
| `zf.extractall()`                  | `cf.extractall()`                    |

## Testing

Run the test suite:

```bash
# Basic functionality test
python test_pycabfile.py

# Run example demo
python example.py
```

## Requirements

- Python 3.10+
- No external dependencies required

## Authors

- [Kei Choi](https://github.com/hanul93) (developer)

## License

MIT License

## Technical Details

This library provides a pure Python implementation for handling Microsoft Cabinet files with a zipfile-compatible interface. It implements the CAB format specification from Microsoft to ensure full compatibility with standard CAB files created by other tools.

### CAB Format Information

For more information about the Microsoft Cabinet format:
https://msdn.microsoft.com/en-us/library/bb417343.aspx
