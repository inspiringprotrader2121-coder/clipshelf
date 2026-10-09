import pytest

from clipshelf.search import rank


def test_empty_query_preserves_order():
    assert rank("", ["b", "a", "c"]) == ["b", "a", "c"]


def test_exact_prefix_wins():
    items = ["git rebase", "grep stuff", "hello world"]
    results = rank("git reb", items)
    assert results[0] == "git rebase"


def test_word_start_match_ranks_higher():
    items = ["database connection pool", "drop table users"]
    results = rank("db", items)
    assert results[0] == "database connection pool"


def test_case_insensitive():
    assert rank("OSS", ["open source software"]) == ["open source software"]


def test_no_match_dropped():
    assert rank("zzz", ["abc", "def"]) == []


def test_recency_breaks_ties():
    items = ["alpha one", "alpha two"]
    results = rank("alpha", items, ages=[10, 5000])
    assert results[0] == "alpha one"


def test_limit():
    items = [f"alpha {i}" for i in range(20)]
    assert len(rank("alpha", items, limit=5)) == 5


def test_limit_must_be_positive():
    with pytest.raises(ValueError):
        rank("a", ["abc"], limit=0)


def test_ages_must_align():
    with pytest.raises(ValueError):
        rank("a", ["abc"], ages=[1.0, 2.0])


def test_query_longer_than_max_is_truncated():
    item = "a" * 100
    assert rank("a" * 200, [item]) == [item]


def test_partial_char_match_scores_low():
    items = ["aaa", "xyzzy"]
    results = rank("a", items)
    assert results[0] == "aaa"
