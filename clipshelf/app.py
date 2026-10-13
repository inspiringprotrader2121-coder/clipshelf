from __future__ import annotations

import sys
from pathlib import Path

from clipshelf.clipboard import ClipboardWatcher, default_clipboard
from clipshelf.config import Config
from clipshelf.history import ClipboardHistory, ClipEntry
from clipshelf.portability import entries_from_json, entries_to_json
from clipshelf.rules import RuleSet
from clipshelf.storage import atomic_write_text


def load_history(path: Path) -> list[ClipEntry]:
    if not path.exists():
        return []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return []
    return entries_from_json(text)


def save_history(path: Path, history: ClipboardHistory) -> int:
    snapshot = history.snapshot()
    atomic_write_text(path, entries_to_json(snapshot))
    return len(snapshot)


class App:
    def __init__(self, config: Config | None = None, clipboard=None) -> None:
        self.config = (config or Config.load()).validate()
        self.history = ClipboardHistory(max_items=self.config.max_items)
        self.history.restore(load_history(self.config.history_path))
        self.clipboard = clipboard if clipboard is not None else default_clipboard()
        self.watcher = ClipboardWatcher(
            self.clipboard, self.on_clip, on_failure=self._on_watcher_failure
        )
        self.rules = RuleSet(self.config.ignore_patterns)
        self._running = False
        self._ignored = 0
        self._watcher_failed = False

    def on_clip(self, text: str) -> None:
        if self.config.ignore_whitespace_clips and not text.strip():
            return
        if self.rules.should_ignore(text):
            self._ignored += 1
            return
        self.history.add(text)

    def _on_watcher_failure(self, exc: Exception) -> None:
        self._watcher_failed = True
        print(
            f"clipshelf: clipboard watching stopped after repeated errors: {exc}", file=sys.stderr
        )

    @property
    def ignored(self) -> int:
        return self._ignored

    @property
    def watcher_failed(self) -> bool:
        return self._watcher_failed

    def start(self) -> None:
        self._running = True
        self.watcher.start()

    def stop(self) -> int:
        self._running = False
        self.watcher.stop()
        return self.save()

    def save(self) -> int:
        """Persist the history, merging in clips other processes wrote meanwhile.

        The tray app keeps its history in memory, so a plain overwrite would
        discard clips added by the CLI or another instance while it ran. The
        file is reloaded first and entries missing from memory are merged in
        (by id and by text) before writing.
        """
        merged = ClipboardHistory(max_items=self.config.max_items)
        merged.restore(self.history.entries)
        merged.restore(load_history(self.config.history_path))
        self.history = merged
        return save_history(self.config.history_path, merged)

    @property
    def running(self) -> bool:
        return self._running


def run_app(config: Config | None = None) -> int:
    import time

    app = App(config)
    app.start()
    try:
        print(f"ClipShelf running - hotkey {app.config.hotkey}, history: {app.config.history_path}")
        while app.running:
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        app.stop()
    return 0
