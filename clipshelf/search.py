from __future__ import annotations

import re
from collections.abc import Iterable

from clipshelf.history import ClipEntry

WORD_SEPARATORS = " \t\n\r-_./\\:;,()[]{}'\""
MAX_QUERY = 64
NO_MATCH = -1
PINNED_BONUS = 15
COPIES_BONUS_STEP = 2
COPIES_BONUS_CAP = 5


def _match_score(query: str, text: str) -> int:
    if not query:
        return 0
    q = query.lower()
    t = text.lower()
    ti = 0
    score = 0
    consecutive = 0
    for ch in q:
        found = t.find(ch, ti)
        if found == NO_MATCH:
            return NO_MATCH
        bonus = 1
        if found == 0 or t[found - 1] in WORD_SEPARATORS:
            bonus += 6
        if found == ti and consecutive:
            consecutive += 1
            bonus += 4 * consecutive
        else:
            consecutive = 1
        score += bonus
        ti = found + 1
    return score


def _recency_bonus(age_seconds: float) -> int:
    if age_seconds < 60:
        return 30
    if age_seconds < 3600:
        return 20
    if age_seconds < 86400:
        return 10
    if age_seconds < 604800:
        return 5
    return 0


def rank(
    query: str,
    items: Iterable[str],
    ages: Iterable[float] | None = None,
    limit: int = 50,
) -> list[str]:
    """Rank *items* by how well they match *query* (fuzzy subsequence match).

    An empty query returns items in their original order. Results with no
    character match are dropped.
    """
    if limit < 1:
        raise ValueError("limit must be >= 1")
    query = query.strip()[:MAX_QUERY]
    items = list(items)
    ages = list(ages) if ages is not None else [0.0] * len(items)
    if len(ages) != len(items):
        raise ValueError("ages must align with items")

    if not query:
        return items[:limit]

    scored: list[tuple[int, str]] = []
    for text, age in zip(items, ages, strict=True):
        score = _match_score(query, text)
        if score == NO_MATCH:
            continue
        scored.append((score + _recency_bonus(age), text))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [text for _, text in scored[:limit]]


def rank_entries(
    entries: Iterable[ClipEntry],
    query: str,
    *,
    pinned_only: bool = False,
    regex: bool = False,
    limit: int = 50,
) -> list[ClipEntry]:
    """Rank clip entries like :func:`rank`, with pinned, copies and regex support.

    Pinned entries get a score bonus and can be filtered to exclusively-pinned
    results. With ``regex=True`` the query is a regular expression (case
    insensitive, multiline) and results are ordered by recency.
    """
    if limit < 1:
        raise ValueError("limit must be >= 1")
    query = query.strip()[:MAX_QUERY]
    entries = list(entries)
    pool = [entry for entry in entries if entry.pinned] if pinned_only else entries

    if regex:
        if not query:
            raise ValueError("regex search needs a pattern")
        try:
            compiled = re.compile(query, re.IGNORECASE | re.MULTILINE)
        except re.error as exc:
            raise ValueError(f"invalid regular expression: {exc}") from exc
        matched = [entry for entry in pool if compiled.search(entry.text)]
        matched.sort(key=lambda entry: entry.copied_at, reverse=True)
        return matched[:limit]

    if not query:
        return pool[:limit]

    scored: list[tuple[int, float, ClipEntry]] = []
    for entry in pool:
        score = _match_score(query, entry.text)
        if score == NO_MATCH:
            continue
        bonus = _recency_bonus(entry.age)
        if entry.pinned:
            bonus += PINNED_BONUS
        bonus += min(max(entry.copies - 1, 0), COPIES_BONUS_CAP) * COPIES_BONUS_STEP
        scored.append((score + bonus, entry.copied_at, entry))

    scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return [entry for _, _, entry in scored[:limit]]
