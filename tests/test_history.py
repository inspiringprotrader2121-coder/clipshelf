import time

import pytest

from clipshelf.history import MAX_TEXT_LENGTH, ClipboardHistory, ClipEntry


def test_add_puts_newest_first():
    h = ClipboardHistory()
    h.add("one")
    h.add("two")
    assert [e.text for e in h.entries] == ["two", "one"]


def test_dedupe_moves_to_front_and_counts():
    h = ClipboardHistory()
    h.add("alpha")
    h.add("beta")
    entry = h.add("alpha")
    assert entry.copies == 2
    assert [e.text for e in h.entries] == ["alpha", "beta"]
    assert len(h) == 2


def test_empty_clip_rejected():
    h = ClipboardHistory()
    with pytest.raises(ValueError):
        h.add("")
    with pytest.raises(ValueError):
        h.add("\x00\x00")
    with pytest.raises(TypeError):
        h.add(42)


def test_whitespace_clip_allowed():
    h = ClipboardHistory()
    entry = h.add("   ")
    assert entry.text == "   "
    assert len(h) == 1


def test_max_items_trims_oldest_unpinned():
    h = ClipboardHistory(max_items=3)
    for word in ["a", "b", "c", "d"]:
        h.add(word)
    assert len(h) == 3
    assert [e.text for e in h.entries] == ["d", "c", "b"]


def test_pinned_survive_rotation():
    h = ClipboardHistory(max_items=3)
    h.add("keep")
    pinned = h.get_by_text("keep")
    h.toggle_pin(pinned.id)
    for word in ["x", "y", "z", "w"]:
        h.add(word)
    assert h.get_by_text("keep") is not None
    assert len(h) == 3


def test_remove_missing_returns_false():
    h = ClipboardHistory()
    h.add("a")
    assert h.remove("nope") is False
    assert h.remove(h.entries[0].id) is True
    assert len(h) == 0


def test_clear_keeps_pinned():
    h = ClipboardHistory()
    h.add("a")
    h.add("b")
    h.toggle_pin(h.get_by_text("a").id)
    removed = h.clear()
    assert removed == 1
    assert [e.text for e in h.entries] == ["a"]


def test_clear_all():
    h = ClipboardHistory()
    h.add("a")
    h.add("b")
    assert h.clear(keep_pinned=False) == 2
    assert len(h) == 0


def test_restore_sorts_by_recency():
    h = ClipboardHistory()
    old = h.add("old")
    new = h.add("new")
    old.copied_at = time.time() - 100
    target = ClipboardHistory()
    target.restore([old, new])
    assert [e.text for e in target.entries] == ["new", "old"]


def test_restore_skips_duplicate_text_with_new_id():
    h = ClipboardHistory()
    h.add("same words")
    duplicate = ClipEntry(text="same words", id="aaaaaaaa")
    assert h.restore([duplicate]) == 0
    assert len(h) == 1


def test_long_text_truncated():
    h = ClipboardHistory()
    entry = h.add("x" * (MAX_TEXT_LENGTH + 10))
    assert len(entry.text) == MAX_TEXT_LENGTH


def test_one_line_flattens_and_truncates():
    h = ClipboardHistory()
    entry = h.add("hello\n  world " + "z" * 100)
    flat = entry.one_line(20)
    assert "\n" not in flat
    assert len(flat) == 20
    assert flat.endswith("\u2026")
