import time

import pytest

from clipshelf.history import ClipEntry
from clipshelf.stats import analyze, summary_lines


def entry(text="clip", copies=1, pinned=False, copied_at=None):
    item = ClipEntry(text=text, pinned=pinned)
    item.copies = copies
    if copied_at is not None:
        item.copied_at = copied_at
    return item


def test_empty_history():
    stats = analyze([])
    assert stats.total == 0
    assert stats.pinned == 0
    assert stats.copies_total == 0
    assert stats.bytes_total == 0
    assert stats.oldest is None
    assert stats.newest is None
    assert stats.top == []


def test_totals():
    now = time.time()
    entries = [
        entry("a", copies=3, pinned=True, copied_at=now - 10),
        entry("bb", copies=1, copied_at=now),
    ]
    stats = analyze(entries)
    assert stats.total == 2
    assert stats.pinned == 1
    assert stats.copies_total == 4
    assert stats.chars_total == 3
    assert stats.bytes_total == 3
    assert stats.oldest == now - 10
    assert stats.newest == now


def test_bytes_versus_characters():
    stats = analyze([entry("\u00e9")])
    assert stats.chars_total == 1
    assert stats.bytes_total == 2


def test_top_orders_by_copies_then_recency():
    now = time.time()
    entries = [
        entry("often", copies=5, copied_at=now - 100),
        entry("sometimes", copies=2, copied_at=now),
        entry("never-again", copies=1),
        entry("twice-newer", copies=2, copied_at=now - 1),
    ]
    stats = analyze(entries)
    assert [text for text, _ in stats.top] == ["often", "sometimes", "twice-newer"]


def test_top_excludes_single_copy_and_respects_limit():
    entries = [entry(f"clip-{i}", copies=i + 2) for i in range(6)]
    stats = analyze(entries, top_n=3)
    assert len(stats.top) == 3
    assert analyze([entry("single")]).top == []


def test_top_n_must_be_positive():
    with pytest.raises(ValueError):
        analyze([], top_n=0)


def test_summary_lines_content():
    entries = [entry("hello world", copies=2, pinned=True)]
    lines = summary_lines(analyze(entries))
    assert "clips: 1" in lines
    assert "pinned: 1" in lines
    assert "copies recorded: 2" in lines
    assert any(line.startswith("oldest: ") for line in lines)
    assert "most copied:" in lines
    assert any("x2  hello world" in line for line in lines)


def test_summary_lines_empty_has_no_dates():
    lines = summary_lines(analyze([]))
    assert "clips: 0" in lines
    assert not any(line.startswith("oldest") for line in lines)
    assert "most copied:" not in lines
