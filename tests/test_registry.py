"""
Tests para el CommandRegistry de Alenia Fuse.
"""
import pytest


def test_registry_is_populated():
    """After importing handlers, registry should have all commands."""
    import fuse.cli.commands  # noqa: trigger @register_command
    from fuse.cli.registry import registry

    names = [cmd.name for cmd in registry.get_all()]
    assert "info" in names
    assert "convert" in names
    assert "compress" in names
    assert "resize" in names
    assert "rotate" in names
    assert "fps" in names
    assert "speed" in names
    assert "trim" in names
    assert "mute" in names
    assert "extract-audio" in names
    assert "thumbnail" in names
    assert "gif" in names
    assert "volume" in names
    assert "normalize" in names
    assert "fade" in names
    assert "formats" in names
    assert "codecs" in names
    assert "lang" in names


def test_registry_alias_resolution():
    import fuse.cli.commands  # noqa
    from fuse.cli.registry import registry

    # "analyze" is an alias of "info"
    cmd = registry.get("analyze")
    assert cmd is not None
    assert cmd.name == "info"


def test_parser_builds_without_error():
    import fuse.cli.commands  # noqa
    from fuse.cli.parser import get_parser
    parser = get_parser()
    assert parser is not None


def test_info_is_available():
    import fuse.cli.commands  # noqa
    from fuse.cli.registry import registry
    cmd = registry.get("info")
    assert cmd is not None
    assert callable(cmd.handler)
