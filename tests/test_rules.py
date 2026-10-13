import pytest

from clipshelf.rules import RuleSet


def test_empty_ruleset_matches_nothing():
    rules = RuleSet()
    assert not rules
    assert rules.match("anything") is None
    assert rules.should_ignore("anything") is False


def test_simple_match():
    rules = RuleSet([r"password\s*="])
    assert rules.should_ignore("password = hunter2")
    assert not rules.should_ignore("my username is john")


def test_matching_is_case_insensitive():
    rules = RuleSet([r"secret"])
    assert rules.should_ignore("TOP SECRET STUFF")


def test_multiline_anchors_work():
    rules = RuleSet(["^BEGIN PRIVATE KEY"])
    text = "notes\nBEGIN PRIVATE KEY-----\nabc"
    assert rules.should_ignore(text)


def test_first_match_returned():
    rules = RuleSet(["alpha", "beta", "gamma"])
    assert rules.match("xx gamma xx") == "gamma"


def test_patterns_property():
    rules = RuleSet(["a", "b"])
    assert rules.patterns == ["a", "b"]
    assert len(rules) == 2


def test_invalid_pattern_rejected():
    with pytest.raises(ValueError, match="invalid ignore pattern"):
        RuleSet(["(unclosed"])


def test_non_string_pattern_rejected():
    with pytest.raises(ValueError):
        RuleSet([42])
    with pytest.raises(ValueError):
        RuleSet("not-a-list")


def test_empty_pattern_rejected():
    with pytest.raises(ValueError):
        RuleSet([""])
