import threading
import time

import pytest

from clipshelf.__main__ import main
from clipshelf.app import App, load_history, save_history
from clipshelf.clipboard import ClipboardWatcher, MemoryClipboard, WindowsClipboard
from clipshelf.config import Config


def wait_for(predicate, timeout=2.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(0.02)
    return False


def test_memory_clipboard_roundtrip():
    clip = MemoryClipboard()
    assert clip.get_text() == ""
    clip.set_text("hello")
    assert clip.get_text() == "hello"


def test_save_and_load_history(tmp_path):
    config = Config(data_dir=tmp_path)
    app = App(config, clipboard=MemoryClipboard())
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
    app = App(Config(data_dir=tmp_path, ignore_whitespace_clips=True), clipboard=MemoryClipboard())
    app.on_clip("   ")
    assert len(app.history) == 0
    app.on_clip("real")
    assert len(app.history) == 1


def test_on_clip_records_whitespace_when_policy_disabled(tmp_path):
    app = App(Config(data_dir=tmp_path, ignore_whitespace_clips=False), clipboard=MemoryClipboard())
    app.on_clip("   ")
    assert len(app.history) == 1


class BrokenClipboard:
    def get_text(self):
        raise OSError("clipboard owned by another process")

    def set_text(self, text):
        raise OSError("clipboard owned by another process")


def test_watcher_reports_failure_once():
    failures = []
    watcher = ClipboardWatcher(
        BrokenClipboard(),
        lambda text: None,
        poll_seconds=0.01,
        on_failure=failures.append,
    )
    watcher.start()
    assert wait_for(lambda: failures)
    watcher.stop()
    assert len(failures) == 1
    assert isinstance(failures[0], OSError)


def test_app_marks_watcher_failure(tmp_path, capsys):
    app = App(Config(data_dir=tmp_path), clipboard=BrokenClipboard())
    app.start()
    try:
        assert wait_for(lambda: app.watcher_failed)
    finally:
        app.stop()
    assert "clipboard watching stopped" in capsys.readouterr().err


def test_watcher_reports_new_values():
    clip = MemoryClipboard()
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
    clip = MemoryClipboard()
    watcher = ClipboardWatcher(clip, lambda text: None, poll_seconds=0.02)
    watcher.start()
    watcher.stop()
    watcher.stop()


def test_app_start_stop_persists_history(tmp_path):
    config = Config(data_dir=tmp_path)
    app = App(config, clipboard=MemoryClipboard())
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
    assert main(["--config", str(tmp_path / "config.json"), "once"]) == 0
    assert main(["--config", str(tmp_path / "config.json"), "list"]) == 0


def test_cli_headless_banner_on_non_windows(tmp_path, capsys):
    import sys

    if sys.platform == "win32":
        pytest.skip("Windows runs the interactive loop")
    config = Config(data_dir=tmp_path)
    config.save(tmp_path / "config.json")
    assert main(["--config", str(tmp_path / "config.json")]) == 0
    assert "Windows" in capsys.readouterr().out


def test_windows_clipboard_requires_windows():
    import sys

    if sys.platform == "win32":
        pytest.skip("Running on Windows")
    with pytest.raises(OSError):
        WindowsClipboard()


def test_on_clip_honors_ignore_rules(tmp_path):
    config = Config(data_dir=tmp_path, ignore_patterns=[r"password\s*="])
    app = App(config, clipboard=MemoryClipboard())
    app.on_clip("password = hunter2")
    assert len(app.history) == 0
    assert app.ignored == 1
    app.on_clip("an ordinary clip")
    assert len(app.history) == 1
    assert app.ignored == 1
