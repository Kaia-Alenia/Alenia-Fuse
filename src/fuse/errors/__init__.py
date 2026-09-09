"""
Alenia Fuse error types — human-readable errors for the user.
"""
from typing import Optional


class FuseError(Exception):
    """Base error for Alenia Fuse operations."""
    def __init__(self, message: str, technical_detail: Optional[str] = None):
        super().__init__(message)
        self.technical_detail = technical_detail

    def __str__(self):
        return self.args[0]


class MediaNotFoundError(FuseError):
    """Raised when the input file does not exist or cannot be read."""
    pass


class MediaAnalysisError(FuseError):
    """Raised when FFprobe cannot analyze the file."""
    pass


class IncompatibleOperationError(FuseError):
    """Raised when an operation is not compatible with the media type."""
    pass


class ConversionError(FuseError):
    """Raised when FFmpeg conversion fails."""
    pass


class FFmpegNotAvailableError(FuseError):
    """Raised when the FFmpeg binary is not found."""
    pass


class UnsupportedFormatError(FuseError):
    """Raised when the target format is not supported."""
    pass


def friendly_error(exc: Exception) -> str:
    """
    Convert any Fuse exception into a user-friendly message.
    Returns a human-readable string.
    """
    if isinstance(exc, MediaNotFoundError):
        return f"File not found: {exc}"
    if isinstance(exc, MediaAnalysisError):
        return f"Cannot analyze file: {exc}"
    if isinstance(exc, IncompatibleOperationError):
        return str(exc)
    if isinstance(exc, ConversionError):
        return f"Conversion failed: {exc}"
    if isinstance(exc, FFmpegNotAvailableError):
        return "FFmpeg is not available. Please ensure the bundled binary is present."
    if isinstance(exc, UnsupportedFormatError):
        return str(exc)
    return f"An unexpected error occurred: {exc}"
