import pytest
from app.services.pattern_matcher import PatternMatcher

@pytest.fixture
def matcher():
    return PatternMatcher()

def test_convert_to_bs(matcher):
    assert matcher.convert_to_bs(0) == "S"
    assert matcher.convert_to_bs(4) == "S"
    assert matcher.convert_to_bs(5) == "B"
    assert matcher.convert_to_bs(9) == "B"

def test_alternating_5(matcher):
    # Remember newest first
    history = [
        {"period": "1005", "number": 5}, # B
        {"period": "1004", "number": 1}, # S
        {"period": "1003", "number": 7}, # B
        {"period": "1002", "number": 3}, # S
        {"period": "1001", "number": 9}, # B
    ]
    
    result = matcher.analyze_history(history)
    assert result is not None
    pattern_name, sequence, period = result
    assert pattern_name == "Alternating 5"
    assert sequence == "B - S - B - S - B"
    assert period == "1005"

def test_triple_b(matcher):
    history = [
        {"period": "1003", "number": 5}, # B
        {"period": "1002", "number": 8}, # B
        {"period": "1001", "number": 9}, # B
        {"period": "1000", "number": 1}, # S
    ]
    
    result = matcher.analyze_history(history)
    assert result is not None
    assert result[0] == "Triple B"

def test_long_run_s(matcher):
    history = [
        {"period": "1005", "number": 1}, # S
        {"period": "1004", "number": 2}, # S
        {"period": "1003", "number": 3}, # S
        {"period": "1002", "number": 4}, # S
        {"period": "1001", "number": 0}, # S
        {"period": "1000", "number": 9}, # B
    ]
    
    result = matcher.analyze_history(history)
    assert result is not None
    # Prioritizes long run
    assert result[0] == "Long Run S (5)"

def test_no_match(matcher):
    history = [
        {"period": "1005", "number": 5}, # B
        {"period": "1004", "number": 5}, # B
        {"period": "1003", "number": 1}, # S
        {"period": "1002", "number": 1}, # S
        {"period": "1001", "number": 9}, # B
    ]
    
    result = matcher.analyze_history(history)
    assert result is None
