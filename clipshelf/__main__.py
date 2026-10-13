from __future__ import annotations

import argparse
import platform
import sys
from pathlib import Path

from clipshelf import __version__
from clipshelf.app import App, load_history, run_app, save_history
from clipshelf.config import Config
from clipshelf.history import ClipboardHistory, ClipEntry
from clipshelf.portability import export_entries, format_for_path, import_entries
from clipshelf.search import rank_entries
from clipshelf.snippets import load_snippets, save_snippets
from clipshelf.stats import analyze, summary_lines

ENTRY_WIDTH = 120


def render_entry(entry: ClipEntry, width: int = ENTRY_WIDTH) -> str:
    marker = "*" if entry.pinned else " "
    return f"{marker} {entry.one_line(width)}"


def preview(text: str, width: int = 60) -> str:
    flat = " ".join(text.split())
    if len(flat) <= width:
        return flat
    return flat[: width - 1] + "\u2026"


def cmd_list(args, config: Config) -> int:
    entries = load_history(config.history_path)
    limit = args.limit if args.limit > 0 else len(entries)
    for entry in entries[:limit]:
        print(render_entry(entry))
    return 0


def cmd_search(args, config: Config) -> int:
    entries = load_history(config.history_path)
    try:
        results = rank_entries(
            entries,
            args.query,
            pinned_only=args.pinned,
            regex=args.regex,
            limit=args.limit,
        )
    except ValueError as exc:
        print(f"clipshelf: {exc}", file=sys.stderr)
        return 1
    for entry in results:
        print(render_entry(entry))
    return 0


def cmd_add(args, config: Config) -> int:
    text = args.text if args.text is not None else sys.stdin.read()
    text = text.strip("\r\n")
    if not text.strip():
        print("clipshelf: nothing to add (empty input)", file=sys.stderr)
        return 1
    history = ClipboardHistory(max_items=config.max_items)
    history.restore(load_history(config.history_path))
    entry = history.add(text)
    save_history(config.history_path, history)
    print(f"added {entry.id}")
    return 0


def cmd_export(args, config: Config) -> int:
    entries = load_history(config.history_path)
    if args.pinned_only:
        entries = [entry for entry in entries if entry.pinned]
    try:
        content = export_entries(entries, args.format)
    except ValueError as exc:
        print(f"clipshelf: {exc}", file=sys.stderr)
        return 1
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(f"wrote {len(entries)} clip(s) to {path}")
    else:
        print(content, end="")
    return 0


def cmd_import(args, config: Config) -> int:
    path = Path(args.path)
    if not path.exists():
        print(f"clipshelf: file not found: {path}", file=sys.stderr)
        return 1
    try:
        fmt = format_for_path(path)
    except ValueError as exc:
        print(f"clipshelf: {exc}", file=sys.stderr)
        return 1
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"clipshelf: cannot read {path}: {exc}", file=sys.stderr)
        return 1
    imported = import_entries(text, fmt)
    history = ClipboardHistory(max_items=config.max_items)
    if not args.replace:
        history.restore(load_history(config.history_path))
    added = history.restore(imported)
    save_history(config.history_path, history)
    print(f"imported {added} new clip(s) from {path}")
    return 0


def cmd_stats(args, config: Config) -> int:
    for line in summary_lines(analyze(load_history(config.history_path))):
        print(line)
    return 0


def cmd_doctor(args, config: Config) -> int:
    mode = (
        "full app (Windows)"
        if sys.platform == "win32"
        else "headless (no tray app on this platform)"
    )
    config_file = Path(args.config_path) if args.config_path else config.data_dir / "config.json"
    print(f"clipshelf {__version__}")
    print(f"python: {platform.python_version()}")
    print(f"platform: {platform.system().lower()} ({platform.machine()})")
    print(f"mode: {mode}")
    print(f"data dir: {config.data_dir}")
    print(f"config: {'found' if config_file.exists() else 'defaults'} ({config_file})")
    print(f"history: {len(load_history(config.history_path))} clip(s) ({config.history_path})")
    print(f"snippets: {len(load_snippets(config.snippets_path))} ({config.snippets_path})")
    print(f"ignore rules: {len(config.ignore_patterns)}")
    return 0


def cmd_once(args, config: Config) -> int:
    App(config).save()
    return 0


def cmd_snippets(args, config: Config) -> int:
    store = load_snippets(config.snippets_path)
    command = args.snippet_command or "list"

    if command == "list":
        for snippet in store:
            print(f"{snippet.name}  (x{snippet.uses})  {preview(snippet.text)}")
        return 0

    if command == "add":
        text = args.text if args.text is not None else sys.stdin.read()
        text = text.strip("\r\n")
        try:
            store.add(args.name, text, replace=getattr(args, "force", False))
        except ValueError as exc:
            print(f"clipshelf: {exc}", file=sys.stderr)
            return 1
        save_snippets(config.snippets_path, store)
        print(f"saved snippet {args.name}")
        return 0

    if command == "remove":
        if not store.remove(args.name):
            print(f"clipshelf: no such snippet: {args.name}", file=sys.stderr)
            return 1
        save_snippets(config.snippets_path, store)
        print(f"removed snippet {args.name}")
        return 0

    if command == "show":
        snippet = store.get(args.name)
        if snippet is None:
            print(f"clipshelf: no such snippet: {args.name}", file=sys.stderr)
            return 1
        print(snippet.text)
        return 0

    if command == "render":
        try:
            rendered = store.render(args.name)
        except KeyError:
            print(f"clipshelf: no such snippet: {args.name}", file=sys.stderr)
            return 1
        save_snippets(config.snippets_path, store)
        print(rendered)
        return 0

    return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="clipshelf", description="Clipboard history manager for Windows"
    )
    parser.add_argument("--version", action="version", version=f"clipshelf {__version__}")
    parser.add_argument("--config", dest="config_path", help="path to a config.json file")
    sub = parser.add_subparsers(dest="command")

    p = sub.add_parser("list", help="print stored clipboard history")
    p.add_argument("--limit", type=int, default=0, help="print at most N entries (0 = all)")
    p.set_defaults(handler=cmd_list)

    p = sub.add_parser("search", help="search history with fuzzy or regex matching")
    p.add_argument("query")
    p.add_argument("--regex", action="store_true", help="treat the query as a regular expression")
    p.add_argument("--pinned", action="store_true", help="search pinned clips only")
    p.add_argument("--limit", type=int, default=20)
    p.set_defaults(handler=cmd_search)

    p = sub.add_parser("add", help="record a clip from an argument or stdin")
    p.add_argument("text", nargs="?", default=None)
    p.set_defaults(handler=cmd_add)

    p = sub.add_parser("export", help="export history as json, markdown or csv")
    p.add_argument("format")
    p.add_argument("--output", default=None, help="write to a file instead of stdout")
    p.add_argument("--pinned-only", dest="pinned_only", action="store_true")
    p.set_defaults(handler=cmd_export)

    p = sub.add_parser("import", help="merge a json or csv export back into history")
    p.add_argument("path")
    p.add_argument("--replace", action="store_true", help="discard the current history first")
    p.set_defaults(handler=cmd_import)

    p = sub.add_parser("stats", help="print history statistics")
    p.set_defaults(handler=cmd_stats)

    p = sub.add_parser("doctor", help="print environment and data diagnostics")
    p.set_defaults(handler=cmd_doctor)

    p = sub.add_parser("once", help="load and re-save the history file (snapshot)")
    p.set_defaults(handler=cmd_once)

    snippets = sub.add_parser("snippets", help="manage reusable named snippets")
    snippet_sub = snippets.add_subparsers(dest="snippet_command")

    sp = snippet_sub.add_parser("list", help="list snippets")
    sp.set_defaults(handler=cmd_snippets)

    sp = snippet_sub.add_parser("add", help="add or replace a snippet")
    sp.add_argument("name")
    sp.add_argument("text", nargs="?", default=None)
    sp.add_argument("--force", action="store_true", help="overwrite an existing snippet")
    sp.set_defaults(handler=cmd_snippets)

    sp = snippet_sub.add_parser("remove", help="delete a snippet")
    sp.add_argument("name")
    sp.set_defaults(handler=cmd_snippets)

    sp = snippet_sub.add_parser("show", help="print a snippet's raw text")
    sp.add_argument("name")
    sp.set_defaults(handler=cmd_snippets)

    sp = snippet_sub.add_parser("render", help="print a snippet with placeholders filled in")
    sp.add_argument("name")
    sp.set_defaults(handler=cmd_snippets)

    snippets.set_defaults(handler=cmd_snippets)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = Config.load(args.config_path) if args.config_path else Config.load()
    config.validate()

    if args.command is None:
        if sys.platform != "win32":
            print("ClipShelf is built for Windows; use --help for the headless commands.")
            return 0
        return run_app(config)

    return args.handler(args, config)


if __name__ == "__main__":
    raise SystemExit(main())
