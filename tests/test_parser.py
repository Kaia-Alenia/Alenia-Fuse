"""
Tests para el parser CLI de Alenia Porter.
"""
import pytest
from types import SimpleNamespace
from alenia_porter.cli.human_parser import parse_human_syntax


def test_convert_to_syntax():
    result = parse_human_syntax(["convert", "movie.mp4", "to", "webm"])
    assert result is not None
    assert result.command == "convert"
    assert result.args["input"] == "movie.mp4"
    assert result.args["output"].endswith(".webm")


def test_convert_direct_syntax():
    result = parse_human_syntax(["convert", "input.mp4", "output.webm"])
    assert result is not None
    assert result.command == "convert"
    assert result.args["input"] == "input.mp4"
    assert result.args["output"] == "output.webm"


def test_trim_syntax():
    result = parse_human_syntax(["trim", "movie.mp4", "from", "00:01:00", "to", "00:02:00"])
    assert result is not None
    assert result.command == "trim"
    assert result.args["file"] == "movie.mp4"
    assert result.args["start"] == "00:01:00"
    assert result.args["end"] == "00:02:00"


def test_resize_syntax():
    result = parse_human_syntax(["resize", "movie.mp4", "1280x720"])
    assert result is not None
    assert result.command == "resize"
    assert result.args["width"] == 1280
    assert result.args["height"] == 720


def test_speed_syntax_with_x():
    result = parse_human_syntax(["speed", "movie.mp4", "2x"])
    assert result is not None
    assert result.command == "speed"
    assert result.args["factor"] == 2.0


def test_extract_audio_syntax():
    result = parse_human_syntax(["extract", "audio", "from", "movie.mp4"])
    assert result is not None
    assert result.command == "extract-audio"
    assert result.args["file"] == "movie.mp4"


def test_volume_syntax():
    result = parse_human_syntax(["volume", "song.mp3", "+20%"])
    assert result is not None
    assert result.command == "volume"
    assert result.args["value"] == "+20%"


def test_thumbnail_with_timestamp():
    result = parse_human_syntax(["thumbnail", "movie.mp4", "at", "00:00:10"])
    assert result is not None
    assert result.command == "thumbnail"
    assert result.args["timestamp"] == "00:00:10"


def test_unrecognized_returns_none():
    result = parse_human_syntax(["unknowncommand", "arg1"])
    assert result is None


def test_empty_returns_none():
    result = parse_human_syntax([])
    assert result is None
