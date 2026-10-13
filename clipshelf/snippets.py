from __future__ import annotations

import json
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

from clipshelf.storage import atomic_write_text

NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
MAX_TEXT_LENGTH = 100_000


class SnippetFormatError(ValueError):
    """Raised when a snippet payload cannot be read back."""


@dataclass(slots=True)
class Snippet:
    name: str
    text: str
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    uses: int = 0

    def render(self, now: float | None = None) -> str:
        stamp = time.localtime(now if now is not None else time.time())
        text = self.text
        text = text.replace("{date}", time.strftime("%Y-%m-%d", stamp))
        text = text.replace("{time}", time.strftime("%H:%M", stamp))
        text = text.replace("{datetime}", time.strftime("%Y-%m-%d %H:%M", stamp))
        return text


def validate_name(name: str) -> str:
    if not isinstance(name, str) or not NAME_PATTERN.match(name):
        raise ValueError(
            "snippet name must start with a letter or digit and may only contain letters, "
            "digits, dots, dashes and underscores (max 64 characters)"
        )
    return name


def validate_text(text: str) -> str:
    if not isinstance(text, str) or not text.strip():
        raise ValueError("snippet text is empty")
    if len(text) > MAX_TEXT_LENGTH:
        raise ValueError(f"snippet text exceeds {MAX_TEXT_LENGTH} characters")
    return text


class SnippetStore:
    """Named, reusable text snippets with simple placeholder rendering."""

    def __init__(self, snippets: list[Snippet] | None = None) -> None:
        self._by_key: dict[str, Snippet] = {}
        for snippet in snippets or []:
            try:
                self._insert(snippet)
            except ValueError:
                continue

    def _insert(self, snippet: Snippet) -> None:
        key = snippet.name.lower()
        if key in self._by_key:
            raise ValueError(f"snippet already exists: {snippet.name}")
        self._by_key[key] = snippet

    def add(self, name: str, text: str, *, replace: bool = False) -> Snippet:
        validate_name(name)
        validate_text(text)
        key = name.lower()
        existing = self._by_key.get(key)
        if existing is not None:
            if not replace:
                raise ValueError(f"snippet already exists: {name}")
            existing.text = text
            existing.updated_at = time.time()
            return existing
        snippet = Snippet(name=name, text=text)
        self._by_key[key] = snippet
        return snippet

    def get(self, name: str) -> Snippet | None:
        return self._by_key.get(name.lower())

    def remove(self, name: str) -> bool:
        return self._by_key.pop(name.lower(), None) is not None

    def rename(self, old: str, new: str) -> bool:
        validate_name(new)
        snippet = self._by_key.get(old.lower())
        if snippet is None:
            return False
        if new.lower() in self._by_key and new.lower() != old.lower():
            raise ValueError(f"snippet already exists: {new}")
        self._by_key.pop(old.lower())
        snippet.name = new
        snippet.updated_at = time.time()
        self._by_key[new.lower()] = snippet
        return True

    def render(self, name: str, now: float | None = None) -> str:
        snippet = self.get(name)
        if snippet is None:
            raise KeyError(name)
        snippet.uses += 1
        return snippet.render(now)

    def __len__(self) -> int:
        return len(self._by_key)

    def __iter__(self):
        return iter(sorted(self._by_key.values(), key=lambda s: s.name.lower()))

    def uses_total(self) -> int:
        return sum(snippet.uses for snippet in self._by_key.values())

    def as_list(self) -> list[dict]:
        return [asdict(snippet) for snippet in self]

    @classmethod
    def from_list(cls, payload: object) -> SnippetStore:
        if not isinstance(payload, list):
            raise SnippetFormatError("snippet data must be a list")
        snippets = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            name = item.get("name")
            text = item.get("text")
            if not isinstance(name, str) or not isinstance(text, str):
                continue
            try:
                snippet = Snippet(
                    name=validate_name(name),
                    text=validate_text(text),
                    created_at=float(item.get("created_at", time.time())),
                    updated_at=float(item.get("updated_at", time.time())),
                    uses=int(item.get("uses", 0)),
                )
            except (TypeError, ValueError):
                continue
            snippets.append(snippet)
        return cls(snippets)


def load_snippets(path: Path) -> SnippetStore:
    if not path.exists():
        return SnippetStore()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return SnippetStore()
    try:
        return SnippetStore.from_list(payload)
    except SnippetFormatError:
        return SnippetStore()


def save_snippets(path: Path, store: SnippetStore) -> int:
    payload = json.dumps(store.as_list(), indent=2, sort_keys=True)
    atomic_write_text(path, payload)
    return len(store)
