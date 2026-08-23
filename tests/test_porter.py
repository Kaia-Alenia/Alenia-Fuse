import pytest
from unittest.mock import patch
from alenia_porter.porter import generate_nickname

def test_generate_nickname_format():
    # Test that the output is formatted as adjective-noun
    nickname = generate_nickname()
    
    assert isinstance(nickname, str)
    parts = nickname.split('-')
    assert len(parts) == 2
    assert parts[0].isalpha()
    assert parts[1].isalpha()

@patch('random.choice')
def test_generate_nickname_mocked(mock_choice):
    # Mock random.choice to return predictable values
    mock_choice.side_effect = ['mocked_adj', 'mocked_noun']
    
    nickname = generate_nickname()
    
    assert nickname == 'mocked_adj-mocked_noun'
    assert mock_choice.call_count == 2

def test_generate_nickname_randomness():
    # Test that calling it multiple times generally returns different results
    # (While technically possible to return the same thing twice, the chance is very low)
    # The lists have at least 100 adjectives and 100 nouns -> 10000 combinations
    nicknames = set()
    for _ in range(10):
        nicknames.add(generate_nickname())
    
    # We should have more than 1 unique nickname (most likely 10, but > 1 is safe)
    assert len(nicknames) > 1
