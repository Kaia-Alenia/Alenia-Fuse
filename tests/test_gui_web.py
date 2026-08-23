import pytest
from unittest.mock import patch, mock_open
from contextlib import contextmanager
import sys

from legacy.ide.gui_web import image_to_base64

@contextmanager
def dummy_resource_path(path):
    yield f"/dummy/path/{path}"

class TestImageToBase64:
    def test_empty_path(self):
        assert image_to_base64(None) is None
        assert image_to_base64("") is None

    @patch("legacy.ide.gui_web.porter.resource_path")
    @patch("os.path.exists")
    def test_file_not_exists(self, mock_exists, mock_resource_path):
        mock_resource_path.side_effect = dummy_resource_path
        mock_exists.return_value = False
        assert image_to_base64("dummy.png") is None

    @patch("legacy.ide.gui_web.porter.resource_path")
    @patch("os.path.exists")
    @patch("builtins.open", new_callable=mock_open, read_data=b"dummy_image_data")
    def test_png_image(self, mock_file, mock_exists, mock_resource_path):
        mock_resource_path.side_effect = dummy_resource_path
        mock_exists.return_value = True
        
        result = image_to_base64("image.png")
        assert result == "data:image/png;base64,ZHVtbXlfaW1hZ2VfZGF0YQ=="

    @patch("legacy.ide.gui_web.porter.resource_path")
    @patch("os.path.exists")
    @patch("builtins.open", new_callable=mock_open, read_data=b"dummy_image_data")
    def test_jpeg_image(self, mock_file, mock_exists, mock_resource_path):
        mock_resource_path.side_effect = dummy_resource_path
        mock_exists.return_value = True
        
        result = image_to_base64("image.jpeg")
        assert result == "data:image/jpeg;base64,ZHVtbXlfaW1hZ2VfZGF0YQ=="
        
        result_jpg = image_to_base64("image.jpg")
        assert result_jpg == "data:image/jpeg;base64,ZHVtbXlfaW1hZ2VfZGF0YQ=="

    @patch("legacy.ide.gui_web.porter.resource_path")
    @patch("os.path.exists")
    @patch("builtins.open", new_callable=mock_open, read_data=b"dummy_image_data")
    def test_gif_image(self, mock_file, mock_exists, mock_resource_path):
        mock_resource_path.side_effect = dummy_resource_path
        mock_exists.return_value = True
        
        result = image_to_base64("image.gif")
        assert result == "data:image/gif;base64,ZHVtbXlfaW1hZ2VfZGF0YQ=="

    @patch("legacy.ide.gui_web.porter.resource_path")
    @patch("os.path.exists")
    @patch("builtins.open")
    def test_exception_handling(self, mock_file, mock_exists, mock_resource_path):
        mock_resource_path.side_effect = dummy_resource_path
        mock_exists.return_value = True
        mock_file.side_effect = Exception("Failed to read")
        
        result = image_to_base64("image.png")
        assert result is None
