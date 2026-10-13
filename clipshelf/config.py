from __future__ import annotations

import json
import os
import re
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path

from clipshelf.rules import RuleSet

APP_NAME = "clipshelf"
DEFAULT_HOTKEY = "ctrl+shift+v"
VALID_MODIFIERS = {"ctrl", "alt", "shift", "win"}
VALID_KEY_PATTERN = r"^([a-z0-9]|f([1-9]|1[0-9]|2[0-4])|space|tab|esc|enter)$"


def default_data_dir() -> Path:
    if os.name == "nt":
        base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        return Path(base) / APP_NAME
    return Path.home() / ".clipshelf"


@dataclass
class Config:
    hotkey: str = DEFAULT_HOTKEY
    max_items: int = 500
    popup_width: int = 560
    popup_height: int = 420
    ignore_whitespace_clips: bool = True
    ignore_patterns: list[str] = field(default_factory=list)
    launch_on_startup: bool = True
    data_dir: Path = field(default_factory=default_data_dir)

    @property
    def history_path(self) -> Path:
        return self.data_dir / "history.json"

    @property
    def snippets_path(self) -> Path:
        return self.data_dir / "snippets.json"

    def validate(self) -> Config:
        if self.max_items < 1 or self.max_items > 10_000:
            raise ValueError("max_items must be between 1 and 10000")
        if not 240 <= self.popup_width <= 2000:
            raise ValueError("popup_width must be between 240 and 2000")
        if not 160 <= self.popup_height <= 1200:
            raise ValueError("popup_height must be between 160 and 1200")
        parts = self.hotkey.lower().split("+")
        if len(parts) < 2:
            raise ValueError("hotkey must be like 'ctrl+shift+v'")
        *modifiers, key = parts
        if len(set(modifiers)) != len(modifiers):
            raise ValueError("duplicate modifier in hotkey")
        if any(m not in VALID_MODIFIERS for m in modifiers):
            raise ValueError(f"unknown modifier in hotkey: {self.hotkey}")
        if not re.match(VALID_KEY_PATTERN, key):
            raise ValueError(f"unknown key in hotkey: {self.hotkey}")
        RuleSet(self.ignore_patterns)
        return self

    def to_dict(self) -> dict:
        data = asdict(self)
        data["data_dir"] = str(self.data_dir)
        return data

    @classmethod
    def from_dict(cls, data: dict) -> Config:
        known = {f for f in cls.__dataclass_fields__}
        filtered = {k: v for k, v in data.items() if k in known}
        if "data_dir" in filtered:
            filtered["data_dir"] = Path(filtered["data_dir"])
        return cls(**filtered)

    def save(self, path: Path | None = None) -> Path:
        path = path or (self.data_dir / "config.json")
        self.validate()
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(self.to_dict(), indent=2, sort_keys=True)
        fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=".config-", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(payload)
            os.replace(tmp_name, path)
        except BaseException:
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)
            raise
        return path

    @classmethod
    def load(cls, path: Path | str | None = None) -> Config:
        path = Path(path) if path else default_data_dir() / "config.json"
        if not path.exists():
            return cls().validate()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return cls().validate()
        if not isinstance(data, dict):
            return cls().validate()
        try:
            return cls.from_dict(data).validate()
        except (TypeError, ValueError):
            return cls().validate()
