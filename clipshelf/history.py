from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field

MAX_TEXT_LENGTH = 1_000_000
ENTRY_ID_LEN = 8


@dataclass(slots=True)
class ClipEntry:
    text: str
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:ENTRY_ID_LEN])
    created_at: float = field(default_factory=time.time)
    copied_at: float = field(default_factory=time.time)
    copies: int = 1
    pinned: bool = False

    @property
    def age(self) -> float:
        return max(0.0, time.time() - self.copied_at)

    def one_line(self, limit: int = 80) -> str:
        flat = " ".join(self.text.split())
        if len(flat) <= limit:
            return flat
        return flat[: limit - 1] + "\u2026"


class ClipboardHistory:
    """Ordered clipboard history with dedupe, pinning and a size cap."""

    def __init__(self, max_items: int = 500) -> None:
        if max_items < 1:
            raise ValueError("max_items must be >= 1")
        self.max_items = max_items
        self._entries: list[ClipEntry] = []

    @property
    def entries(self) -> list[ClipEntry]:
        return list(self._entries)

    def __len__(self) -> int:
        return len(self._entries)

    def __iter__(self):
        return iter(self._entries)

    def add(self, text: str) -> ClipEntry:
        if not isinstance(text, str):
            raise TypeError("clip text must be a string")
        text = text.strip("\x00")
        if not text.strip():
            raise ValueError("clip text is empty")
        if len(text) > MAX_TEXT_LENGTH:
            text = text[:MAX_TEXT_LENGTH]

        existing = self.get_by_text(text)
        if existing is not None:
            self._entries.remove(existing)
            existing.copies += 1
            existing.copied_at = time.time()
            self._entries.insert(0, existing)
            self._trim()
            return existing

        entry = ClipEntry(text=text)
        self._entries.insert(0, entry)
        self._trim()
        return entry

    def get(self, entry_id: str) -> ClipEntry | None:
        return next((e for e in self._entries if e.id == entry_id), None)

    def get_by_text(self, text: str) -> ClipEntry | None:
        return next((e for e in self._entries if e.text == text), None)

    def remove(self, entry_id: str) -> bool:
        entry = self.get(entry_id)
        if entry is None:
            return False
        self._entries.remove(entry)
        return True

    def toggle_pin(self, entry_id: str) -> bool:
        entry = self.get(entry_id)
        if entry is None:
            return False
        entry.pinned = not entry.pinned
        return True

    def clear(self, keep_pinned: bool = True) -> int:
        before = len(self._entries)
        self._entries = [e for e in self._entries if e.pinned] if keep_pinned else []
        return before - len(self._entries)

    def restore(self, entries: list[ClipEntry]) -> int:
        count = 0
        for entry in sorted(entries, key=lambda e: e.copied_at, reverse=True):
            if self.get(entry.id) is None and entry.text.strip():
                self._entries.append(entry)
                count += 1
        self._trim()
        return count

    def snapshot(self) -> list[ClipEntry]:
        return sorted(self._entries, key=lambda e: e.copied_at, reverse=True)

    def _trim(self) -> None:
        if len(self._entries) <= self.max_items:
            return
        pinned = [e for e in self._entries if e.pinned]
        unpinned = [e for e in self._entries if not e.pinned]
        keep = max(self.max_items - len(pinned), 0)
        self._entries = sorted(unpinned[:keep] + pinned, key=lambda e: e.copied_at, reverse=True)
