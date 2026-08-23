import hashlib
import os
import tempfile
from unittest.mock import patch, mock_open

import pytest

from alenia_porter.media_engine import get_file_hash


def test_get_file_hash_success():
    """Test getting hash of a valid file."""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"test data")
        temp_path = f.name
    
    try:
        expected_hash = hashlib.sha256(b"test data").hexdigest()
        actual_hash = get_file_hash(temp_path)
        assert actual_hash == expected_hash
    finally:
        os.remove(temp_path)

def test_get_file_hash_file_not_found():
    """Test getting hash of a file that does not exist."""
    with patch("builtins.open", side_effect=FileNotFoundError):
        assert get_file_hash("nonexistent_file.txt") is None

def test_get_file_hash_permission_error():
    """Test getting hash of a file with permission error."""
    with patch("builtins.open", side_effect=PermissionError):
        assert get_file_hash("no_permission_file.txt") is None

def test_get_file_hash_io_error():
    """Test getting hash of a file with IO error."""
    with patch("builtins.open", side_effect=IOError):
        assert get_file_hash("io_error_file.txt") is None

from alenia_porter.media_engine import load_cache

def test_load_cache_success():
    with patch('os.path.exists', return_value=True):
        m = mock_open(read_data='{"test": "data"}')
        with patch('builtins.open', m):
            result = load_cache("/fake/dir")
            assert result == {"test": "data"}

def test_load_cache_not_exists():
    with patch('os.path.exists', return_value=False):
        result = load_cache("/fake/dir")
        assert result == {}

def test_load_cache_malformed_json():
    with patch('os.path.exists', return_value=True):
        m = mock_open(read_data='{malformed_json')
        with patch('builtins.open', m):
            result = load_cache("/fake/dir")
            assert result == {}

def test_load_cache_io_error():
    with patch('os.path.exists', return_value=True):
        with patch('builtins.open', side_effect=IOError("test error")):
            result = load_cache("/fake/dir")
            assert result == {}
