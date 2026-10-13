import json
from pathlib import Path

import pytest

from clipshelf.history import ClipEntry
from clipshelf.portability import (
    entries_from_csv,
    entries_from_json,
    entries_from_payload,
    entries_to_csv,
    entries_to_json,
    entries_to_markdown,
    export_entries,
    format_for_path,
    import_entries,
    normalize_format,
)


def sample_entry(text="hello", **overrides):
    entry = ClipEntry(text=text)
    for key, value in overrides.items():
        setattr(entry, key, value)
    return entry


def test_entry_from_dict_requires_text():
    assert entries_from_payload([{"text": 5}, {"text": ""}, "junk"]) == []
    assert entries_from_payload([{"text": "   "}])[0].text == "   "


def test_entry_from_dict_coerces_fields():
    entries = entries_from_payload(
        [
            {
                "text": "ok",
                "id": "abcd1234",
                "copies": 3,
                "pinned": True,
                "created_at": 1.5,
                "copied_at": 2.5,
            }
        ]
    )
    entry = entries[0]
    assert entry.id == "abcd1234"
    assert entry.copies == 3
    assert entry.pinned is True
    assert entry.created_at == 1.5
    assert entry.copied_at == 2.5


def test_entry_from_dict_rejects_bad_field_types():
    entry = entries_from_payload([{"text": "ok", "copies": "many", "pinned": "yes"}])[0]
    assert entry.copies == 1
    assert entry.pinned is False


def test_entries_from_json_bad_input():
    assert entries_from_json("{not json") == []
    assert entries_from_json(json.dumps({"text": "not a list"})) == []


def test_json_roundtrip_preserves_everything():
    entry = sample_entry("keep me", pinned=True)
    entry.copies = 4
    text = entries_to_json([entry])
    loaded = entries_from_json(text)[0]
    assert loaded.id == entry.id
    assert loaded.text == "keep me"
    assert loaded.pinned is True
    assert loaded.copies == 4
    assert loaded.created_at == pytest.approx(entry.created_at)


def test_markdown_export_marks_flags():
    pinned = sample_entry("a pinned clip", pinned=True)
    plain = sample_entry("plain")
    markdown = entries_to_markdown([pinned, plain])
    assert markdown.startswith("# ClipShelf history")
    assert "## 1. (pinned)" in markdown
    assert "## 2." in markdown
    assert "    a pinned clip" in markdown


def test_markdown_export_indents_multiline_text():
    binary = sample_entry("line one\n\nline three")
    markdown = entries_to_markdown([binary])
    assert "    line one\n    \n    line three" in markdown


def test_csv_export_has_header_and_rows():
    entry = sample_entry("with,comma", pinned=True)
    entry.copies = 2
    csv_text = entries_to_csv([entry])
    lines = csv_text.strip().splitlines()
    assert lines[0] == "id,text,copies,pinned,created_at,copied_at"
    assert '"with,comma"' in lines[1]
    assert ",2,True," in lines[1]


def test_csv_roundtrip():
    entry = sample_entry("round trip", pinned=True)
    entry.copies = 3
    loaded = entries_from_csv(entries_to_csv([entry]))
    assert len(loaded) == 1
    assert loaded[0].text == "round trip"
    assert loaded[0].pinned is True
    assert loaded[0].copies == 3
    assert loaded[0].id == entry.id


def test_csv_without_text_column_rejected():
    assert entries_from_csv("alpha,beta\n1,2\n") == []


def test_normalize_format_and_alias():
    assert normalize_format("MD") == "markdown"
    with pytest.raises(ValueError):
        normalize_format("yaml")
    with pytest.raises(ValueError):
        normalize_format(5)


def test_export_dispatch():
    entry = sample_entry("x")
    assert entries_from_json(export_entries([entry], "json"))[0].text == "x"
    assert "x" in export_entries([entry], "markdown")
    assert "x" in export_entries([entry], "csv")


def test_import_dispatch():
    entry = sample_entry("y")
    assert import_entries(export_entries([entry], "json"), "json")[0].text == "y"
    assert import_entries(export_entries([entry], "csv"), "csv")[0].text == "y"
    with pytest.raises(ValueError):
        import_entries("text", "markdown")


def test_format_for_path():
    assert format_for_path(Path("x.json")) == "json"
    assert format_for_path(Path("X.CSV")) == "csv"
    with pytest.raises(ValueError):
        format_for_path(Path("x.md"))
