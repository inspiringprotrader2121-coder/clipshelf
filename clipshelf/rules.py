from __future__ import annotations

import re

RULE_FLAGS = re.IGNORECASE | re.MULTILINE


class RuleSet:
    """Regex rules deciding which clips must never be recorded."""

    def __init__(self, patterns: list[str] | tuple[str, ...] = ()) -> None:
        if not isinstance(patterns, (list, tuple)):
            raise ValueError("ignore patterns must be a list of regular expressions")
        compiled: list[tuple[str, re.Pattern[str]]] = []
        for pattern in patterns:
            if not isinstance(pattern, str) or not pattern:
                raise ValueError("ignore patterns must be non-empty strings")
            try:
                compiled.append((pattern, re.compile(pattern, RULE_FLAGS)))
            except re.error as exc:
                raise ValueError(f"invalid ignore pattern {pattern!r}: {exc}") from exc
        self._rules = tuple(compiled)

    @property
    def patterns(self) -> list[str]:
        return [pattern for pattern, _ in self._rules]

    def __len__(self) -> int:
        return len(self._rules)

    def __bool__(self) -> bool:
        return bool(self._rules)

    def match(self, text: str) -> str | None:
        """Return the first pattern that matches *text*, or None."""
        for pattern, compiled in self._rules:
            if compiled.search(text):
                return pattern
        return None

    def should_ignore(self, text: str) -> bool:
        return self.match(text) is not None
