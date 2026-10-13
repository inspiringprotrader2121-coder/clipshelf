from __future__ import annotations

import csv
import io
import json
from dataclasses import asdict
from pathlib import Path

from clipshelf.history import ClipEntry

EXPORT_FORMATS = ("json", "markdown", "csv")
IMPORT_FORMATS = ("json", "csv")
FORMAT_ALIASES = {"md": "markdown"}


def normalize_format(name: str) -> str:
    if not isinstance(name, str):
        raise ValueError("format must be a string")
    normalized = FORMAT_ALIASES.get(name.lower(), name.lower())
    if normalized not in EXPORT_FORMATS:
        raise ValueError(f"unsupported format: {name} (use one of {', '.join(EXPORT_FORMATS)})")
    return normalized


def entry_from_dict(item: object) -> ClipEntry | None:
    if not isinstance(item, dict):
        return None
    text = item.get("text")
    if not isinstance(text, str) or not text.strip():
        return None
    kwargs: dict = {"text": text}
    identifier = item.get("id")
    if isinstance(identifier, str) and identifier:
        kwargs["id"] = identifier
    for key in ("created_at", "copied_at"):
        value = item.get(key)
        if isinstance(value, (int, float)) and value > 0:
            kwargs[key] = float(value)
    copies = item.get("copies")
    if isinstance(copies, int) and copies >= 1:
        kwargs["copies"] = copies
    if isinstance(item.get("pinned"), bool):
        kwargs["pinned"] = item["pinned"]
    return ClipEntry(**kwargs)


def entries_from_payload(payload: object) -> list[ClipEntry]:
    if not isinstance(payload, list):
        return []
    entries = []
    for item in payload:
        entry = entry_from_dict(item)
        if entry is not None:
            entries.append(entry)
    return entries


def entries_from_json(text: str) -> list[ClipEntry]:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return []
    return entries_from_payload(payload)


def _float(value: object) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int(value: object) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _bool(value: object) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in ("true", "1", "yes"):
            return True
        if lowered in ("false", "0", "no", ""):
            return False
    return None


def entries_from_csv(text: str) -> list[ClipEntry]:
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames or "text" not in reader.fieldnames:
        return []
    entries = []
    for row in reader:
        entry = entry_from_dict(
            {
                "text": row.get("text") or "",
                "id": row.get("id") or "",
                "created_at": _float(row.get("created_at")),
                "copied_at": _float(row.get("copied_at")),
                "copies": _int(row.get("copies")),
                "pinned": _bool(row.get("pinned")),
            }
        )
        if entry is not None:
            entries.append(entry)
    return entries


def entries_to_json(entries: list[ClipEntry]) -> str:
    return json.dumps([asdict(entry) for entry in entries], indent=2)


def entries_to_markdown(entries: list[ClipEntry], title: str = "ClipShelf history") -> str:
    lines = [f"# {title}", "", f"{len(entries)} clip(s).", ""]
    for index, entry in enumerate(entries, start=1):
        flags = []
        if entry.pinned:
            flags.append("pinned")
        if entry.copies > 1:
            flags.append(f"copied {entry.copies}x")
        suffix = f" ({', '.join(flags)})" if flags else ""
        lines.append(f"## {index}.{suffix}")
        lines.append("")
        for text_line in entry.text.splitlines() or [""]:
            lines.append(f"    {text_line}")
        lines.append("")
    return "\n".join(lines) + "\n"


def entries_to_csv(entries: list[ClipEntry]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["id", "text", "copies", "pinned", "created_at", "copied_at"])
    for entry in entries:
        writer.writerow(
            [
                entry.id,
                entry.text,
                entry.copies,
                entry.pinned,
                f"{entry.created_at:.3f}",
                f"{entry.copied_at:.3f}",
            ]
        )
    return buffer.getvalue()


def export_entries(entries: list[ClipEntry], fmt: str) -> str:
    fmt = normalize_format(fmt)
    if fmt == "json":
        return entries_to_json(entries)
    if fmt == "markdown":
        return entries_to_markdown(entries)
    return entries_to_csv(entries)


def import_entries(text: str, fmt: str) -> list[ClipEntry]:
    fmt = normalize_format(fmt)
    if fmt == "json":
        return entries_from_json(text)
    if fmt == "csv":
        return entries_from_csv(text)
    raise ValueError("markdown import is not supported; use JSON or CSV")


def format_for_path(path: Path) -> str:
    suffix = path.suffix.lower().lstrip(".")
    if suffix in IMPORT_FORMATS:
        return suffix
    raise ValueError(f"cannot tell the format of {path.name!r}; use a .json or .csv file")
