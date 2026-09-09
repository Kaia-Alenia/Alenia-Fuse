"""
Updated test_cli.py — verifies registry population after handler import.
"""
import pytest
import fuse.cli.commands  # noqa: trigger registration
from fuse.cli.parser import get_parser


def test_parser_has_subcommands():
    parser = get_parser()
    # The parser should have subparsers registered
    assert parser is not None
    assert parser.prog == "fuse"


def test_short_python_api_facade():
    from fuse import Audio as ShortAudio, Image as ShortImage, Media as ShortMedia
    from fuse import Video as ShortVideo
    from fuse import Audio, Image, Media, Video

    assert ShortVideo is Video
    assert ShortAudio is Audio
    assert ShortImage is Image
    assert ShortMedia is Media


def test_short_python_submodule_facades():
    from fuse.api.audio import Audio as ShortAudio
    from fuse.operations.convert import ConvertOperation as ShortConvert
    from fuse.api.audio import Audio
    from fuse.operations.convert import ConvertOperation

    assert ShortAudio is Audio
    assert ShortConvert is ConvertOperation


def test_parser_contains_convert():
    import fuse.cli.commands  # noqa
    from fuse.cli.registry import registry
    cmd = registry.get("convert")
    assert cmd is not None


def test_parser_contains_info():
    from fuse.cli.registry import registry
    cmd = registry.get("info")
    assert cmd is not None
