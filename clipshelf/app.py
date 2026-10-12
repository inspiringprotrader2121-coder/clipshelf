from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from clipshelf.clipboard import ClipboardWatcher, default_clipboard
from clipshelf.config import Config
from clipshelf.history import ClipboardHistory, ClipEntry


def load_history(path: Path) -> list[ClipEntry]:
    if not path.exists():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(raw, list):
        return []
    entries = []
    for item in raw:
        if not isinstance(item, dict) or not isinstance(item.get("text"), str):
            continue
        try:
            entries.append(ClipEntry(**item))
        except TypeError:
            continue
    return entries


def save_history(path: Path, history: ClipboardHistory) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [asdict(entry) for entry in history.snapshot()]
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return len(payload)


class App:
    def __init__(self, config: Config | None = None, clipboard=None) -> None:
        self.config = (config or Config.load()).validate()
        self.history = ClipboardHistory(max_items=self.config.max_items)
        self.history.restore(load_history(self.config.history_path))
        self.clipboard = clipboard if clipboard is not None else default_clipboard()
        self.watcher = ClipboardWatcher(self.clipboard, self.on_clip)
        self._running = False

    def on_clip(self, text: str) -> None:
        if self.config.ignore_whitespace_clips and not text.strip():
            return
        self.history.add(text)

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
