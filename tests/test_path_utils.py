"""Property-based tests for Windows path handling utilities.

**Feature: bladerf-a4-refactor, Property 10: Windows Path Handling**
**Validates: Requirements 5.3**

This module tests that file paths are correctly handled on Windows,
including path separators and file creation in specified locations.
"""

import os
import tempfile
from pathlib import Path
from datetime import datetime

from hypothesis import given, strategies as st, settings, assume

from path_utils import (
    get_output_directory,
    create_timestamped_filename,
    get_output_filepath,
    create_raw_samples_filepath,
    create_debug_samples_filepath,
    create_decoded_bits_filepath,
    normalize_path,
    is_valid_output_path,
    safe_write_bytes
)


class TestWindowsPathHandling:
    """Property tests for Windows path handling."""
    
    @given(st.text(
        alphabet=st.characters(
            whitelist_categories=('L', 'N'),  # Letters and numbers only
            whitelist_characters='_-'
        ),
        min_size=1,
        max_size=50
    ))
    @settings(max_examples=100)
    def test_normalize_path_produces_valid_path(self, path_segment):
        """
        **Feature: bladerf-a4-refactor, Property 10: Windows Path Handling**
        **Validates: Requirements 5.3**
        
        For any valid path segment, normalize_path SHALL produce a valid Path object.
        """
        # Skip empty strings after filtering
        assume(len(path_segment.strip()) > 0)
        
        result = normalize_path(path_segment)
        
        # Verify result is a Path object
        assert isinstance(result, Path)
        
        # Verify the path string is preserved
        assert path_segment in str(result)
    
    @given(
        st.text(
            alphabet=st.characters(
                whitelist_categories=('L', 'N'),
                whitelist_characters='_-'
            ),
            min_size=1,
            max_size=30
        ),
        st.sampled_from(['bin', 'raw', 'txt', 'dat'])
    )
    @settings(max_examples=100)
    def test_timestamped_filename_format(self, prefix, extension):
        """
        **Feature: bladerf-a4-refactor, Property 10: Windows Path Handling**
        **Validates: Requirements 5.3**
        
        For any prefix and extension, create_timestamped_filename SHALL produce
        a filename with the correct format: prefix_DDMM_HHMM.extension
        """
        assume(len(prefix.strip()) > 0)
        
        # Use a fixed timestamp for predictable testing
        test_time = datetime(2024, 5, 15, 14, 30)
        
        result = create_timestamped_filename(prefix, extension, test_time)
        
        # Verify format
        assert result.startswith(prefix)
        assert result.endswith(f".{extension}")
        assert "_1505_1430." in result  # DDMM_HHMM format

    
    @given(st.floats(min_value=1e6, max_value=100e6, allow_nan=False, allow_infinity=False))
    @settings(max_examples=100)
    def test_raw_samples_filepath_contains_sample_rate(self, sample_rate):
        """
        **Feature: bladerf-a4-refactor, Property 10: Windows Path Handling**
        **Validates: Requirements 5.3**
        
        For any sample rate, create_raw_samples_filepath SHALL produce a path
        containing the integer sample rate value and timestamp.
        """
        result = create_raw_samples_filepath(sample_rate)
        
        # Verify result is a Path object
        assert isinstance(result, Path)
        
        # Verify sample rate is in filename
        expected_rate = str(int(sample_rate))
        assert expected_rate in str(result.name)
        
        # Verify it has .raw extension
        assert result.suffix == ".raw"
    
    @given(st.binary(min_size=1, max_size=1000))
    @settings(max_examples=100)
    def test_safe_write_bytes_creates_file(self, data):
        """
        **Feature: bladerf-a4-refactor, Property 10: Windows Path Handling**
        **Validates: Requirements 5.3**
        
        For any binary data, safe_write_bytes SHALL create a file in the
        specified location with the correct content.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test_output.bin"
            
            # Write data
            result = safe_write_bytes(filepath, data, append=False)
            
            # Verify write was successful
            assert result is True
            
            # Verify file exists
            assert filepath.exists()
            
            # Verify content matches
            with open(filepath, 'rb') as f:
                written_data = f.read()
            assert written_data == data
    
    @given(
        st.binary(min_size=1, max_size=500),
        st.binary(min_size=1, max_size=500)
    )
    @settings(max_examples=100)
    def test_safe_write_bytes_append_mode(self, data1, data2):
        """
        **Feature: bladerf-a4-refactor, Property 10: Windows Path Handling**
        **Validates: Requirements 5.3**
        
        For any two binary data chunks, safe_write_bytes in append mode SHALL
        concatenate the data correctly.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test_append.bin"
            
            # Write first chunk
            result1 = safe_write_bytes(filepath, data1, append=False)
            assert result1 is True
            
            # Append second chunk
            result2 = safe_write_bytes(filepath, data2, append=True)
            assert result2 is True
            
            # Verify combined content
            with open(filepath, 'rb') as f:
                written_data = f.read()
            assert written_data == data1 + data2
    
    @given(st.text(
        alphabet=st.characters(
            whitelist_categories=('L', 'N'),
            whitelist_characters='_-/\\'
        ),
        min_size=1,
        max_size=100
    ))
    @settings(max_examples=100)
    def test_path_with_mixed_separators(self, path_str):
        """
        **Feature: bladerf-a4-refactor, Property 10: Windows Path Handling**
        **Validates: Requirements 5.3**
        
        For any path string with mixed separators (forward and back slashes),
        normalize_path SHALL produce a valid Path object.
        """
        assume(len(path_str.strip()) > 0)
        # Filter out paths that are just separators
        assume(any(c not in '/\\' for c in path_str))
        
        result = normalize_path(path_str)
        
        # Verify result is a Path object
        assert isinstance(result, Path)
        
        # Verify the path can be converted to string without error
        str_result = str(result)
        assert len(str_result) > 0


class TestOutputDirectoryHandling:
    """Tests for output directory handling."""
    
    def test_get_output_directory_default_is_cwd(self):
        """Test that default output directory is current working directory."""
        result = get_output_directory()
        assert result == Path.cwd()
    
    def test_get_output_directory_with_base_dir(self):
        """Test that base_dir is used when provided."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = get_output_directory(tmpdir)
            assert result == Path(tmpdir)
    
    def test_create_debug_samples_filepath_format(self):
        """Test debug samples filepath has correct name with timestamp."""
        result = create_debug_samples_filepath()
        # Should contain "receive_test" and ".raw" extension
        assert "receive_test" in result.name
        assert result.suffix == ".raw"
    
    def test_create_decoded_bits_filepath_format(self):
        """Test decoded bits filepath has correct format."""
        test_time = datetime(2024, 3, 20, 9, 45)
        result = create_decoded_bits_filepath(timestamp=test_time)
        
        assert result.name == "decoded_bits_2003_0945.bin"


class TestPathValidation:
    """Tests for path validation."""
    
    def test_is_valid_output_path_with_valid_path(self):
        """Test that valid paths are recognized."""
        with tempfile.TemporaryDirectory() as tmpdir:
            valid_path = Path(tmpdir) / "output.bin"
            assert is_valid_output_path(valid_path) is True
    
    def test_is_valid_output_path_with_invalid_chars_on_windows(self):
        """Test that invalid Windows characters are detected."""
        if os.name == 'nt':
            invalid_path = Path("test<file>.bin")
            assert is_valid_output_path(invalid_path) is False
