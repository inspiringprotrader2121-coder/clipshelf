import pytest

from clipshelf.history import ClipEntry
from clipshelf.search import rank, rank_entries


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


def make_entry(text, pinned=False, copies=1, copied_at=0.0):
    entry = ClipEntry(text=text, pinned=pinned)
    entry.copies = copies
    entry.copied_at = copied_at
    entry.created_at = copied_at
    return entry


def test_rank_entries_filters_pinned_only():
    plain = make_entry("alpha plain")
    pinned = make_entry("alpha pinned", pinned=True)
    results = rank_entries([plain, pinned], "alpha", pinned_only=True)
    assert [entry.text for entry in results] == ["alpha pinned"]


def test_rank_entries_pinned_bonus_beats_tie():
    plain = make_entry("todo list")
    pinned = make_entry("todo list", pinned=True)
    results = rank_entries([plain, pinned], "todo")
    assert results[0].pinned is True


def test_rank_entries_copies_bonus():
    once = make_entry("same text")
    often = make_entry("same text", copies=4)
    results = rank_entries([once, often], "same")
    assert results[0].copies == 4


def test_rank_entries_empty_query_keeps_order():
    first = make_entry("one")
    second = make_entry("two")
    assert rank_entries([first, second], "") == [first, second]


def test_rank_entries_limit():
    entries = [make_entry(f"clip {i}") for i in range(10)]
    assert len(rank_entries(entries, "clip", limit=3)) == 3
    with pytest.raises(ValueError):
        rank_entries(entries, "clip", limit=0)


def test_rank_entries_regex_mode():
    entries = [make_entry("order #1234"), make_entry("order #abcd"), make_entry("nothing")]
    results = rank_entries(entries, r"#\d{4}", regex=True)
    assert [entry.text for entry in results] == ["order #1234"]


def test_rank_entries_regex_is_case_insensitive_and_multiline():
    entries = [make_entry("line one\nAPI_KEY=abc")]
    assert rank_entries(entries, "^api_key", regex=True) == entries


def test_rank_entries_regex_orders_by_recency():
    old = make_entry("match old", copied_at=1.0)
    new = make_entry("match new", copied_at=500.0)
    results = rank_entries([old, new], "match", regex=True)
    assert [entry.text for entry in results] == ["match new", "match old"]


def test_rank_entries_bad_regex():
    with pytest.raises(ValueError, match="invalid regular expression"):
        rank_entries([make_entry("x")], "(unclosed", regex=True)


def test_rank_entries_regex_needs_pattern():
    with pytest.raises(ValueError):
        rank_entries([make_entry("x")], "", regex=True)
