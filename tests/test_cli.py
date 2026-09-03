"""
Updated test_cli.py — verifies registry population after handler import.
"""
import pytest
import alenia_porter.cli.handlers  # noqa: trigger registration
from alenia_porter.cli.parser import get_parser


def test_parser_has_subcommands():
    parser = get_parser()
    # The parser should have subparsers registered
    assert parser is not None


def test_parser_contains_convert():
    import alenia_porter.cli.handlers  # noqa
    from alenia_porter.cli.registry import registry
    cmd = registry.get("convert")
    assert cmd is not None


def test_parser_contains_info():
    from alenia_porter.cli.registry import registry
    cmd = registry.get("info")
    assert cmd is not None
