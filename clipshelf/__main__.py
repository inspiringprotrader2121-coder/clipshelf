from __future__ import annotations

import argparse
import sys

from clipshelf import __version__
from clipshelf.app import App, load_history, save_history
from clipshelf.config import Config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="clipshelf", description="Clipboard history for Windows")
    parser.add_argument("--version", action="version", version=f"clipshelf {__version__}")
    parser.add_argument("--once", action="store_true", help="snapshot history and exit")
    parser.add_argument("--list", action="store_true", dest="list_history", help="print history")
    parser.add_argument("--config", dest="config_path", help="path to config.json")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = Config.load(args.config_path) if args.config_path else Config.load()
    config.validate()

    if args.list_history:
        entries = load_history(config.history_path)
        for entry in entries:
            print(entry.one_line())
        return 0

    if args.once:
        app = App(config)
        return 0 if save_history(config.history_path, app.history) >= 0 else 1

    if sys.platform != "win32":
        print("ClipShelf is built for Windows; use --list/--once in headless mode.")
        return 0
    from clipshelf.app import run_app

    return run_app(config)


if __name__ == "__main__":
    raise SystemExit(main())
