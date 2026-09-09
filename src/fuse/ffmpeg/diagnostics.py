"""Helpers for turning FFmpeg's stderr into useful API error messages."""

import re
from typing import Optional


_ANSI_ESCAPE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
_PROGRESS_LINE = re.compile(r"^\s*(?:frame=|size=|bitrate=|speed=|time=)")
_ERROR_LINE = re.compile(
    r"\b(error|invalid|unable|failed|failure|cannot|could not|not found|unknown|no such|unsupported)\b",
    re.IGNORECASE,
)


def format_ffmpeg_error(stderr: Optional[str], returncode: Optional[int] = None) -> str:
    """Return a readable FFmpeg diagnostic instead of exposing only its exit code."""
    text = _ANSI_ESCAPE.sub("", stderr or "")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    diagnostic_lines = [line for line in lines if not _PROGRESS_LINE.match(line)]

    # FFmpeg writes a long build/configuration banner before the useful part.
    # Prefer the concise lines that actually explain why the command failed.
    error_lines = [line for line in diagnostic_lines if _ERROR_LINE.search(line)]
    if error_lines:
        diagnostic_lines = error_lines

    # Keep errors useful without flooding an API response with the FFmpeg banner.
    if len(diagnostic_lines) > 8:
        diagnostic_lines = diagnostic_lines[-8:]

    if diagnostic_lines:
        return "\n".join(diagnostic_lines)

    if returncode is not None:
        return f"FFmpeg failed (exit code {returncode}) without a diagnostic message."
    return "FFmpeg failed without a diagnostic message."
