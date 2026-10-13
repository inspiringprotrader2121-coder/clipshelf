from __future__ import annotations

from pathlib import Path

from clipshelf.clipboard import ClipboardWatcher, default_clipboard
from clipshelf.config import Config
from clipshelf.history import ClipboardHistory, ClipEntry
from clipshelf.portability import entries_from_json, entries_to_json
from clipshelf.rules import RuleSet


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
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(entries_to_json(snapshot), encoding="utf-8")
    return len(snapshot)


class App:
    def __init__(self, config: Config | None = None, clipboard=None) -> None:
        self.config = (config or Config.load()).validate()
        self.history = ClipboardHistory(max_items=self.config.max_items)
        self.history.restore(load_history(self.config.history_path))
        self.clipboard = clipboard if clipboard is not None else default_clipboard()
        self.watcher = ClipboardWatcher(self.clipboard, self.on_clip)
        self.rules = RuleSet(self.config.ignore_patterns)
        self._running = False
        self._ignored = 0

    def on_clip(self, text: str) -> None:
        if self.config.ignore_whitespace_clips and not text.strip():
            return
        if self.rules.should_ignore(text):
            self._ignored += 1
            return
        self.history.add(text)

    @property
    def ignored(self) -> int:
        return self._ignored

    def start(self) -> None:
        self._running = True
        self.watcher.start()

    def stop(self) -> None:
        self._running = False
        self.watcher.stop()
        save_history(self.config.history_path, self.history)

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
