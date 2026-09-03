import pytest
from alenia_porter.cli.parser import get_parser

def test_parser_help():
    parser = get_parser()
    assert parser is not None
