# pycabfile Test Suite

This directory contains comprehensive tests for the pycabfile library.

## Test Structure

### Test Files

- **`test_basic.py`** - Unit tests for core functionality

  - CAB file creation and reading
  - File extraction
  - Context manager support
  - Error handling
  - Binary data handling
  - Unicode filename support

- **`test_functional.py`** - High-level integration tests

  - Basic functionality verification
  - Comprehensive scenario testing
  - Multiple file type handling
  - Large file testing

- **`run_all_tests.py`** - Complete test runner
  - Runs all unit tests
  - Runs all functional tests
  - Provides comprehensive test summary

## Running Tests

### Run All Tests

```bash
cd test
python run_all_tests.py
```

### Run Unit Tests Only

```bash
cd test
python test_basic.py
```

### Run Functional Tests Only

```bash
cd test
python test_functional.py
```

### Run with unittest module

```bash
# From project root
python -m unittest discover test -v

# From test directory
python -m unittest test_basic.TestPyCabFile -v
```

## Test Requirements

- Python 3.10+
- No external dependencies (tests use only standard library)
- Temporary directories are automatically created and cleaned up

## Test Coverage

The test suite covers:

### Core Functionality

- CAB file creation (`CabFile` with write mode)
- CAB file reading (`CabFile` with read mode)
- File listing (`namelist()`)
- File content reading (`read()`)
- File information (`getinfo()`)
- File extraction (`extract()`, `extractall()`)
- Direct string writing (`writestr()`)

### API Compatibility

- zipfile-compatible interface
- Context manager support
- Error handling with appropriate exceptions
- File path handling

### Data Types

- Text files
- Binary files
- Empty files
- Unicode content
- Large files (10KB+)

### Edge Cases

- Non-existent files
- Invalid modes
- Missing archive members
- Resource cleanup

## Expected Output

When all tests pass, you should see:

```
=== pycabfile Complete Test Suite ===

=== Running Unit Tests ===
[Unit test results...]

=== Running Functional Tests ===
[Functional test results...]

============================================================
TEST SUMMARY:
  Unit Tests: PASSED
  Functional Tests: PASSED

ALL TESTS PASSED!
```

## Troubleshooting

### Common Issues

1. **Import Error**: Make sure you're running tests from the correct directory
2. **Permission Error**: Ensure write permissions for temporary directories
3. **File Not Found**: Check that pycabfile module is properly installed/accessible

### Debug Mode

For verbose output, run individual test files directly:

```bash
python test_basic.py
python test_functional.py
```
