from __future__ import annotations

from collections.abc import Iterable

WORD_SEPARATORS = " \t\n\r-_./\\:;,()[]{}'\""
MAX_QUERY = 64
NO_MATCH = -1


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
