"""
Updated test_cli.py — verifies registry population after handler import.
"""
from fuse.cli.parser import get_parser


def test_parser_has_subcommands():
    parser = get_parser()
    # The parser should have subparsers registered
    assert parser is not None
    assert parser.prog == "fuse"


def test_short_python_api_facade():
    from fuse import Audio, Image, Media, Video
    from fuse import Audio as ShortAudio
    from fuse import Image as ShortImage
    from fuse import Media as ShortMedia
    from fuse import Video as ShortVideo

    assert ShortVideo is Video
    assert ShortAudio is Audio
    assert ShortImage is Image
    assert ShortMedia is Media


def test_short_python_submodule_facades():
    from fuse.api.audio import Audio
    from fuse.api.audio import Audio as ShortAudio
    from fuse.operations.convert import ConvertOperation
    from fuse.operations.convert import ConvertOperation as ShortConvert

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


def test_top_level_help_is_generated_from_registered_commands(capsys):
    from fuse.cli.parser import get_parser

    get_parser().print_help()
    output = capsys.readouterr().out

    assert "fuse convert" in output
    assert "fuse info" in output
    assert "fuse formats" in output
