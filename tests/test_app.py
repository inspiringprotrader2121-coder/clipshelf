import threading
import time

import pytest

from clipshelf.__main__ import main
from clipshelf.app import App, load_history, save_history
from clipshelf.clipboard import ClipboardWatcher, default_clipboard
from clipshelf.config import Config


def wait_for(predicate, timeout=2.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(0.02)
    return False


def test_memory_clipboard_roundtrip():
    clip = default_clipboard()
    assert clip.get_text() == ""
    clip.set_text("hello")
    assert clip.get_text() == "hello"


def test_save_and_load_history(tmp_path):
    config = Config(data_dir=tmp_path)
    app = App(config)
    app.on_clip("first")
    app.on_clip("second")
    count = save_history(config.history_path, app.history)
    assert count == 2
    loaded = load_history(config.history_path)
    assert [e.text for e in loaded] == ["second", "first"]
    assert loaded[0].id == app.history.entries[0].id


def test_load_history_missing_file(tmp_path):
    assert load_history(tmp_path / "nope.json") == []


def test_load_history_corrupt_file(tmp_path):
    path = tmp_path / "history.json"
    path.write_text("{{{", encoding="utf-8")
    assert load_history(path) == []


def test_load_history_skips_bad_entries(tmp_path):
    path = tmp_path / "history.json"
    path.write_text('[{"text": "ok"}, {"text": 5}, "junk"]', encoding="utf-8")
    entries = load_history(path)
    assert [e.text for e in entries] == ["ok"]


def test_on_clip_respects_whitespace_policy(tmp_path):
    app = App(Config(data_dir=tmp_path, ignore_whitespace_clips=True))
    app.on_clip("   ")
    assert len(app.history) == 0
    app.on_clip("real")
    assert len(app.history) == 1


def test_watcher_reports_new_values():
    clip = default_clipboard()
    seen = []
    done = threading.Event()
    watcher = ClipboardWatcher(
        clip, lambda text: (seen.append(text), done.set()), poll_seconds=0.02
    )
    watcher.start()
    clip.set_text("watched value")
    assert done.wait(2.0)
    watcher.stop()
    assert "watched value" in seen


def test_watcher_stop_is_idempotent():
    clip = default_clipboard()
    watcher = ClipboardWatcher(clip, lambda text: None, poll_seconds=0.02)
    watcher.start()
    watcher.stop()
    watcher.stop()


def test_app_start_stop_persists_history(tmp_path):
    config = Config(data_dir=tmp_path)
    app = App(config)
    app.start()
    try:
        app.clipboard.set_text("captured while running")
        assert wait_for(lambda: len(app.history) >= 1)
    finally:
        app.stop()
    saved = load_history(config.history_path)
    assert [e.text for e in saved] == ["captured while running"]


def test_cli_list_and_once(tmp_path):
    config = Config(data_dir=tmp_path)
    config.save(tmp_path / "config.json")
    assert main(["--config", str(tmp_path / "config.json"), "--once"]) == 0
    assert main(["--config", str(tmp_path / "config.json"), "--list"]) == 0


def test_cli_headless_banner_on_non_windows(tmp_path, capsys):
    import sys

    if sys.platform == "win32":
        pytest.skip("Windows runs the interactive loop")
    config = Config(data_dir=tmp_path)
    config.save(tmp_path / "config.json")
    assert main(["--config", str(tmp_path / "config.json")]) == 0
    assert "Windows" in capsys.readouterr().out
