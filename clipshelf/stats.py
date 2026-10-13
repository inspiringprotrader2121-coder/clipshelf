from __future__ import annotations

import time
from dataclasses import dataclass

from clipshelf.history import ClipEntry

TOP_DEFAULT = 5


@dataclass(slots=True)
class Stats:
    total: int
    pinned: int
    copies_total: int
    chars_total: int
    bytes_total: int
    oldest: float | None
    newest: float | None
    top: list[tuple[str, int]]


def analyze(entries: list[ClipEntry], top_n: int = TOP_DEFAULT) -> Stats:
    if top_n < 1:
        raise ValueError("top_n must be >= 1")
    entries = list(entries)
    timestamps = [entry.copied_at for entry in entries]
    repeated = sorted(
        (entry for entry in entries if entry.copies > 1),
        key=lambda entry: (entry.copies, entry.copied_at),
        reverse=True,
    )[:top_n]
    return Stats(
        total=len(entries),
        pinned=sum(1 for entry in entries if entry.pinned),
        copies_total=sum(entry.copies for entry in entries),
        chars_total=sum(len(entry.text) for entry in entries),
        bytes_total=sum(len(entry.text.encode("utf-8")) for entry in entries),
        oldest=min(timestamps) if timestamps else None,
        newest=max(timestamps) if timestamps else None,
        top=[(entry.one_line(60), entry.copies) for entry in repeated],
    )


def _stamp(timestamp: float) -> str:
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(timestamp))


def summary_lines(stats: Stats) -> list[str]:
    lines = [
        f"clips: {stats.total}",
        f"pinned: {stats.pinned}",
        f"copies recorded: {stats.copies_total}",
        f"characters: {stats.chars_total}",
        f"bytes: {stats.bytes_total}",
    ]
    if stats.oldest is not None:
        lines.append(f"oldest: {_stamp(stats.oldest)}")
    if stats.newest is not None:
        lines.append(f"newest: {_stamp(stats.newest)}")
    if stats.top:
        lines.append("most copied:")
        lines.extend(f"  x{count}  {text}" for text, count in stats.top)
    return lines
