import json
import time

import pytest

from clipshelf.snippets import Snippet, SnippetStore, load_snippets, save_snippets


def test_add_and_get():
    store = SnippetStore()
    store.add("sig", "Best regards,\nJohn")
    assert store.get("sig").text == "Best regards,\nJohn"
    assert len(store) == 1


def test_names_are_case_insensitive():
    store = SnippetStore()
    store.add("Sig", "x")
    assert store.get("SIG") is not None
    with pytest.raises(ValueError):
        store.add("sig", "y")


def test_replace_overwrites():
    store = SnippetStore()
    store.add("sig", "old")
    snippet = store.add("sig", "new", replace=True)
    assert snippet.text == "new"
    assert len(store) == 1


def test_invalid_names_rejected():
    store = SnippetStore()
    for name in ["", "with space", "-leading", "a" * 65, "sla/sh"]:
        with pytest.raises(ValueError):
            store.add(name, "text")


def test_empty_text_rejected():
    with pytest.raises(ValueError):
        SnippetStore().add("ok", "   \n ")


def test_remove():
    store = SnippetStore()
    store.add("a", "1")
    assert store.remove("A") is True
    assert store.remove("a") is False


def test_rename():
    store = SnippetStore()
    store.add("old", "value")
    assert store.rename("OLD", "new") is True
    assert store.get("old") is None
    assert store.get("new").text == "value"
    assert store.rename("missing", "another") is False


def test_rename_conflict_rejected():
    store = SnippetStore()
    store.add("a", "1")
    store.add("b", "2")
    with pytest.raises(ValueError):
        store.rename("a", "b")


def test_iteration_is_sorted():
    store = SnippetStore()
    store.add("zeta", "z")
    store.add("alpha", "a")
    assert [s.name for s in store] == ["alpha", "zeta"]


def test_render_replaces_placeholders():
    store = SnippetStore()
    store.add("stamp", "on {date} at {time} ({datetime})")
    stamp = time.mktime((2026, 10, 13, 9, 5, 0, 0, 0, -1))
    assert store.render("stamp", now=stamp) == "on 2026-10-13 at 09:05 (2026-10-13 09:05)"


def test_render_counts_uses():
    store = SnippetStore()
    store.add("s", "x")
    store.render("s")
    store.render("s")
    assert store.get("s").uses == 2
    assert store.uses_total() == 2


def test_render_unknown_raises():
    with pytest.raises(KeyError):
        SnippetStore().render("nope")


def test_roundtrip(tmp_path):
    path = tmp_path / "snippets.json"
    store = SnippetStore()
    store.add("a", "one")
    store.add("b", "two")
    assert save_snippets(path, store) == 2
    loaded = load_snippets(path)
    assert [s.name for s in loaded] == ["a", "b"]
    assert loaded.get("a").text == "one"


def test_load_missing_and_corrupt(tmp_path):
    assert len(load_snippets(tmp_path / "none.json")) == 0
    bad = tmp_path / "snippets.json"
    bad.write_text("{not json", encoding="utf-8")
    assert len(load_snippets(bad)) == 0


def test_from_list_skips_bad_entries():
    payload = [
        {"name": "good", "text": "ok"},
        {"name": "bad name", "text": "no"},
        {"name": "no-text"},
        "junk",
    ]
    store = SnippetStore.from_list(payload)
    assert [s.name for s in store] == ["good"]


def test_direct_constructor_skips_duplicates():
    store = SnippetStore([Snippet(name="a", text="1"), Snippet(name="A", text="2")])
    assert len(store) == 1
    assert store.get("a").text == "1"


def test_as_list_is_json_ready():
    store = SnippetStore()
    store.add("a", "one")
    payload = json.loads(json.dumps(store.as_list()))
    assert payload[0]["name"] == "a"
    assert payload[0]["text"] == "one"
