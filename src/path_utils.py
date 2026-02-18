"""Path utilities for Windows-compatible file handling.

This module provides cross-platform path handling utilities for the
DJI DroneID Live Receiver, ensuring Windows compatibility.

**Validates: Requirements 5.3, 7.3**
"""

from pathlib import Path
from datetime import datetime
from typing import Optional
import os


def get_output_directory(base_dir: Optional[str] = None) -> Path:
    """Get the output directory for saving files.
    
    Args:
        base_dir: Optional base directory path. If None, uses current directory.
        
    Returns:
        Path object for the output directory
        
    **Validates: Requirements 5.3**
    """
    if base_dir is None:
        return Path.cwd()
    return Path(base_dir)


def create_timestamped_filename(prefix: str, extension: str, 
                                 timestamp: Optional[datetime] = None) -> str:
    """Create a filename with timestamp.
    
    Args:
        prefix: Filename prefix (e.g., "decoded_bits")
        extension: File extension without dot (e.g., "bin")
        timestamp: Optional datetime, uses current time if None
        
    Returns:
        Filename string with timestamp (e.g., "decoded_bits_0501_1430.bin")
        
    **Validates: Requirements 7.3**
    """
    if timestamp is None:
        timestamp = datetime.now()
    
    # Format: prefix_DDMM_HHMM.extension
    time_str = f"{timestamp.day:02d}{timestamp.month:02d}_{timestamp.hour:02d}{timestamp.minute:02d}"
    return f"{prefix}_{time_str}.{extension}"


def get_output_filepath(filename: str, base_dir: Optional[str] = None) -> Path:
    """Get full output file path with Windows-compatible handling.
    
    Args:
        filename: The filename to use
        base_dir: Optional base directory path
        
    Returns:
        Full Path object for the output file
        
    **Validates: Requirements 5.3**
    """
    output_dir = get_output_directory(base_dir)
    return output_dir / filename


def create_raw_samples_filepath(sample_rate: float,
                                timestamp: Optional[datetime] = None, 
                                base_dir: Optional[str] = None) -> Path:
    """Create filepath for raw sample output with timestamp.
    
    Args:
        sample_rate: Sample rate in Hz
        timestamp: Optional datetime for filename
        base_dir: Optional base directory path
        
    Returns:
        Path object for raw samples file
        
    **Validates: Requirements 5.3, 7.3**
    """
    prefix = f"ext_drone_id_{int(sample_rate)}"
    filename = create_timestamped_filename(prefix, "raw", timestamp)
    return get_output_filepath(filename, base_dir)


def create_debug_samples_filepath(timestamp: Optional[datetime] = None,
                                  base_dir: Optional[str] = None) -> Path:
    """Create filepath for debug sample output with timestamp.
    
    Args:
        timestamp: Optional datetime for filename
        base_dir: Optional base directory path
        
    Returns:
        Path object for debug samples file
        
    **Validates: Requirements 5.3**
    """
    filename = create_timestamped_filename("receive_test", "raw", timestamp)
    return get_output_filepath(filename, base_dir)


def create_decoded_bits_filepath(timestamp: Optional[datetime] = None,
                                  base_dir: Optional[str] = None) -> Path:
    """Create filepath for decoded bits output.
    
    Args:
        timestamp: Optional datetime for filename
        base_dir: Optional base directory path
        
    Returns:
        Path object for decoded bits file
        
    **Validates: Requirements 5.3, 7.3**
    """
    filename = create_timestamped_filename("decoded_bits", "bin", timestamp)
    return get_output_filepath(filename, base_dir)


def normalize_path(path_str: str) -> Path:
    """Normalize a path string to a Path object with Windows compatibility.
    
    Args:
        path_str: Path string that may contain forward or back slashes
        
    Returns:
        Normalized Path object
        
    **Validates: Requirements 5.3**
    """
    # Path handles both forward and back slashes automatically
    return Path(path_str)


def ensure_parent_directory(filepath: Path) -> Path:
    """Ensure the parent directory of a filepath exists.
    
    Args:
        filepath: Path to a file
        
    Returns:
        The same filepath (for chaining)
        
    **Validates: Requirements 5.3**
    """
    filepath.parent.mkdir(parents=True, exist_ok=True)
    return filepath


def is_valid_output_path(path: Path) -> bool:
    """Check if a path is valid for output on the current platform.
    
    Args:
        path: Path to validate
        
    Returns:
        True if the path is valid for output, False otherwise
        
    **Validates: Requirements 5.3**
    """
    try:
        # Check if path is absolute or can be resolved
        resolved = path.resolve()
        
        # Check for invalid characters on Windows
        if os.name == 'nt':
            invalid_chars = '<>:"|?*'
            path_str = str(path.name)  # Check filename only
            if any(c in path_str for c in invalid_chars):
                return False
        
        # Check if parent directory exists or can be created
        parent = resolved.parent
        if parent.exists():
            return parent.is_dir()
        
        # If parent doesn't exist, check if we can create it
        return True
        
    except (OSError, ValueError):
        return False


def safe_write_bytes(filepath: Path, data: bytes, append: bool = True) -> bool:
    """Safely write bytes to a file with Windows compatibility.
    
    Args:
        filepath: Path to write to
        data: Bytes to write
        append: If True, append to file; if False, overwrite
        
    Returns:
        True if write was successful, False otherwise
        
    **Validates: Requirements 5.3, 7.3**
    """
    try:
        mode = 'ab' if append else 'wb'
        with open(filepath, mode) as f:
            f.write(data)
        return True
    except (OSError, IOError):
        return False


def create_empty_file(filepath: Path) -> bool:
    """Create an empty file to reserve the filename.
    
    Args:
        filepath: Path to create
        
    Returns:
        True if creation was successful, False otherwise
        
    **Validates: Requirements 5.3**
    """
    try:
        filepath.touch(exist_ok=True)
        return True
    except (OSError, IOError):
        return False
