import io
import json
import time

import pytest

from clipshelf.__main__ import main
from clipshelf.app import save_history
from clipshelf.config import Config
from clipshelf.history import ClipboardHistory


def setup_env(tmp_path):
    config = Config(data_dir=tmp_path)
    config.save(tmp_path / "config.json")
    return config, ["--config", str(tmp_path / "config.json")]


def seed(config, texts, pinned=()):
    history = ClipboardHistory(max_items=config.max_items)
    for text in texts:
        entry = history.add(text)
        if text in pinned:
            history.toggle_pin(entry.id)
    save_history(config.history_path, history)
    return history


def test_add_then_list(tmp_path, capsys):
    _, base = setup_env(tmp_path)
    assert main([*base, "add", "hello from the cli"]) == 0
    assert "added" in capsys.readouterr().out
    assert main([*base, "list"]) == 0
    assert "hello from the cli" in capsys.readouterr().out


def test_add_reads_stdin(tmp_path, capsys, monkeypatch):
    _, base = setup_env(tmp_path)
    monkeypatch.setattr("sys.stdin", io.StringIO("piped in clip"))
    assert main([*base, "add"]) == 0
    assert main([*base, "list"]) == 0
    assert "piped in clip" in capsys.readouterr().out


def test_add_empty_fails(tmp_path, capsys):
    _, base = setup_env(tmp_path)
    assert main([*base, "add", "   "]) == 1
    assert "nothing to add" in capsys.readouterr().err


def test_list_limit(tmp_path, capsys):
    config, base = setup_env(tmp_path)
    seed(config, [f"clip {i}" for i in range(5)])
    assert main([*base, "list", "--limit", "2"]) == 0
    output = capsys.readouterr().out
    assert output.count("clip ") == 2


def test_search_marks_pinned(tmp_path, capsys):
    config, base = setup_env(tmp_path)
    seed(config, ["git rebase -i HEAD~3", "run the test suite"], pinned=["run the test suite"])
    assert main([*base, "search", "run"]) == 0
    output = capsys.readouterr().out
    assert output.startswith("* run the test suite")


def test_search_regex(tmp_path, capsys):
    config, base = setup_env(tmp_path)
    seed(config, ["order #1234 shipped", "order #abcd queued"])
    assert main([*base, "search", r"#\d{4}", "--regex"]) == 0
    output = capsys.readouterr().out
    assert "order #1234 shipped" in output
    assert "order #abcd queued" not in output


def test_search_bad_regex(tmp_path, capsys):
    config, base = setup_env(tmp_path)
    seed(config, ["anything"])
    assert main([*base, "search", "(unclosed", "--regex"]) == 1
    assert "invalid regular expression" in capsys.readouterr().err


def test_export_json_to_stdout(tmp_path, capsys):
    config, base = setup_env(tmp_path)
    seed(config, ["export me", "me too"])
    assert main([*base, "export", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert [item["text"] for item in payload] == ["me too", "export me"]


def test_export_to_file_and_pinned_only(tmp_path, capsys):
    config, base = setup_env(tmp_path)
    seed(config, ["keep this", "transient"], pinned=["keep this"])
    out_file = tmp_path / "history.json"
    assert main([*base, "export", "json", "--pinned-only", "--output", str(out_file)]) == 0
    assert "wrote 1 clip(s)" in capsys.readouterr().out
    payload = json.loads(out_file.read_text(encoding="utf-8"))
    assert [item["text"] for item in payload] == ["keep this"]


def test_export_markdown_and_csv(tmp_path, capsys):
    config, base = setup_env(tmp_path)
    seed(config, ["first clip", "second clip"])
    assert main([*base, "export", "markdown", "--output", str(tmp_path / "h.md")]) == 0
    assert "# ClipShelf history" in (tmp_path / "h.md").read_text(encoding="utf-8")
    assert main([*base, "export", "csv", "--output", str(tmp_path / "h.csv")]) == 0
    assert "id,text,copies,pinned" in (tmp_path / "h.csv").read_text(encoding="utf-8")


def test_export_bad_format(tmp_path, capsys):
    _, base = setup_env(tmp_path)
    assert main([*base, "export", "yaml"]) == 1
    assert "unsupported format" in capsys.readouterr().err


def test_import_merges_and_is_idempotent(tmp_path, capsys):
    config, base = setup_env(tmp_path)
    seed(config, ["one", "two"])
    export_file = tmp_path / "history.json"
    assert main([*base, "export", "json", "--output", str(export_file)]) == 0
    capsys.readouterr()

    other = tmp_path / "other"
    other.mkdir()
    _, other_base = setup_env(other)
    assert main([*other_base, "import", str(export_file)]) == 0
    assert "imported 2 new clip(s)" in capsys.readouterr().out
    assert main([*other_base, "import", str(export_file)]) == 0
    assert "imported 0 new clip(s)" in capsys.readouterr().out


def test_import_replace(tmp_path, capsys):
    config, base = setup_env(tmp_path)
    seed(config, ["old one", "old two"])
    source = tmp_path / "source.json"
    source.write_text(
        json.dumps([{"text": "replacement clip", "copies": 1, "pinned": False}]),
        encoding="utf-8",
    )
    assert main([*base, "import", str(source), "--replace"]) == 0
    capsys.readouterr()
    assert main([*base, "list"]) == 0
    output = capsys.readouterr().out
    assert "replacement clip" in output
    assert "old one" not in output


def test_import_missing_file(tmp_path, capsys):
    _, base = setup_env(tmp_path)
    assert main([*base, "import", str(tmp_path / "missing.json")]) == 1
    assert "file not found" in capsys.readouterr().err


def test_import_unsupported_extension(tmp_path, capsys):
    _, base = setup_env(tmp_path)
    bad = tmp_path / "history.md"
    bad.write_text("# not importable", encoding="utf-8")
    assert main([*base, "import", str(bad)]) == 1
    assert "cannot tell the format" in capsys.readouterr().err


def test_stats_output(tmp_path, capsys):
    config, base = setup_env(tmp_path)
    seed(config, ["alpha", "beta", "beta"])
    assert main([*base, "stats"]) == 0
    output = capsys.readouterr().out
    assert "clips: 2" in output
    assert "most copied:" in output


def test_doctor_output(tmp_path, capsys):
    _, base = setup_env(tmp_path)
    assert main([*base, "doctor"]) == 0
    output = capsys.readouterr().out
    assert "clipshelf " in output
    assert "python: " in output
    assert "platform: " in output
    assert "ignore rules: 0" in output


def test_once_creates_history_file(tmp_path):
    config, base = setup_env(tmp_path)
    assert main([*base, "once"]) == 0
    assert config.history_path.exists()


def test_snippets_full_flow(tmp_path, capsys):
    _, base = setup_env(tmp_path)
    assert main([*base, "snippets", "add", "sig", "Best regards, {date}"]) == 0
    assert "saved snippet sig" in capsys.readouterr().out

    assert main([*base, "snippets", "list"]) == 0
    assert "sig" in capsys.readouterr().out

    assert main([*base, "snippets", "show", "sig"]) == 0
    assert "{date}" in capsys.readouterr().out

    assert main([*base, "snippets", "render", "sig"]) == 0
    assert time.strftime("%Y") in capsys.readouterr().out

    assert main([*base, "snippets", "list"]) == 0
    assert "(x1)" in capsys.readouterr().out

    assert main([*base, "snippets", "remove", "sig"]) == 0
    assert "removed snippet sig" in capsys.readouterr().out
    assert main([*base, "snippets", "show", "sig"]) == 1


def test_snippets_defaults_to_list(tmp_path, capsys):
    _, base = setup_env(tmp_path)
    assert main([*base, "snippets"]) == 0
    assert capsys.readouterr().out == ""


def test_snippets_duplicate_needs_force(tmp_path, capsys):
    _, base = setup_env(tmp_path)
    assert main([*base, "snippets", "add", "note", "first"]) == 0
    capsys.readouterr()
    assert main([*base, "snippets", "add", "note", "second"]) == 1
    assert "already exists" in capsys.readouterr().err
    assert main([*base, "snippets", "add", "note", "second", "--force"]) == 0
    assert main([*base, "snippets", "show", "note"]) == 0
    assert "second" in capsys.readouterr().out


def test_snippets_add_stdin(tmp_path, capsys, monkeypatch):
    _, base = setup_env(tmp_path)
    monkeypatch.setattr("sys.stdin", io.StringIO("piped snippet"))
    assert main([*base, "snippets", "add", "piped"]) == 0
    assert main([*base, "snippets", "render", "piped"]) == 0
    assert "piped snippet" in capsys.readouterr().out


def test_unknown_command_exits(tmp_path, capsys):
    _, base = setup_env(tmp_path)
    with pytest.raises(SystemExit) as excinfo:
        main([*base, "frobnicate"])
    assert excinfo.value.code == 2
