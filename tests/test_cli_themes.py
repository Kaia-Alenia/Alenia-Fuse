import os
import json
import pytest
from unittest.mock import patch, mock_open, MagicMock
from alenia_porter.cli import load_themes


@pytest.fixture
def mock_resource_path():
    with patch('alenia_porter.porter.resource_path') as mock_rp:
        yield mock_rp


def test_load_themes_no_files_fallback(mock_resource_path):
    # Simulate os.path.exists returning False (no themes path)
    with patch('os.path.exists', return_value=False):
        # mock_resource_path context manager returns a dummy path
        mock_ctx = MagicMock()
        mock_ctx.__enter__.return_value = '/fake/assets/themes'
        mock_resource_path.return_value = mock_ctx
        
        themes = load_themes()
        
        assert "Default Theme" in themes
        assert themes["Default Theme"]["name"] == "Default Theme"
        assert themes["Default Theme"]["bg_main"] == "#1e1e1e"


def test_load_themes_valid_files(mock_resource_path):
    # Simulate finding valid JSON files
    with patch('os.path.exists', return_value=True), \
         patch('glob.glob', return_value=['/fake/assets/themes/theme1.json', '/fake/assets/themes/theme2.json']):
        
        mock_ctx = MagicMock()
        mock_ctx.__enter__.return_value = '/fake/assets/themes'
        mock_resource_path.return_value = mock_ctx
        
        mock_data_1 = '{"name": "Theme One", "bg_main": "#111111"}'
        mock_data_2 = '{"name": "Theme Two", "bg_main": "#222222"}'
        
        def mock_open_impl(file, *args, **kwargs):
            if file == '/fake/assets/themes/theme1.json':
                return mock_open(read_data=mock_data_1).return_value
            elif file == '/fake/assets/themes/theme2.json':
                return mock_open(read_data=mock_data_2).return_value
            return mock_open().return_value

        with patch('builtins.open', new_callable=lambda: mock_open_impl):
            themes = load_themes()
            
            assert len(themes) == 2
            assert "Theme One" in themes
            assert themes["Theme One"]["bg_main"] == "#111111"
            assert "Theme Two" in themes
            assert themes["Theme Two"]["bg_main"] == "#222222"


def test_load_themes_invalid_files_graceful_fallback(mock_resource_path):
    # Simulate finding files, but one is valid and the other is invalid (corrupt JSON)
    with patch('os.path.exists', return_value=True), \
         patch('glob.glob', return_value=['/fake/assets/themes/valid.json', '/fake/assets/themes/invalid.json']):
        
        mock_ctx = MagicMock()
        mock_ctx.__enter__.return_value = '/fake/assets/themes'
        mock_resource_path.return_value = mock_ctx
        
        mock_data_valid = '{"name": "Valid Theme", "bg_main": "#111111"}'
        mock_data_invalid = 'NOT JSON'
        
        def mock_open_impl(file, *args, **kwargs):
            if file == '/fake/assets/themes/valid.json':
                return mock_open(read_data=mock_data_valid).return_value
            elif file == '/fake/assets/themes/invalid.json':
                return mock_open(read_data=mock_data_invalid).return_value
            return mock_open().return_value

        with patch('builtins.open', new_callable=lambda: mock_open_impl):
            themes = load_themes()
            
            assert len(themes) == 1
            assert "Valid Theme" in themes
            assert "invalid" not in themes
            assert themes["Valid Theme"]["bg_main"] == "#111111"

def test_load_themes_all_invalid_files(mock_resource_path):
    # Simulate finding files, but all are invalid. Fallback should kick in.
    with patch('os.path.exists', return_value=True), \
         patch('glob.glob', return_value=['/fake/assets/themes/invalid.json']):
        
        mock_ctx = MagicMock()
        mock_ctx.__enter__.return_value = '/fake/assets/themes'
        mock_resource_path.return_value = mock_ctx
        
        mock_data_invalid = 'NOT JSON'
        
        def mock_open_impl(file, *args, **kwargs):
            return mock_open(read_data=mock_data_invalid).return_value

        with patch('builtins.open', new_callable=lambda: mock_open_impl):
            themes = load_themes()
            
            assert len(themes) == 1
            assert "Default Theme" in themes
            assert themes["Default Theme"]["name"] == "Default Theme"
