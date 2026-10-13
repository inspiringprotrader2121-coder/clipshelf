# ClipShelf

[![CI](https://github.com/inspiringprotrader2121-coder/clipshelf/actions/workflows/ci.yml/badge.svg)](https://github.com/inspiringprotrader2121-coder/clipshelf/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)

A lightweight clipboard history manager for Windows.

ClipShelf records everything you copy into a local, searchable history — no
cloud sync, no account, no telemetry. The core engine, the Python API and the
headless command line are complete today; the tray app with its hotkey popup
is in development (see [Roadmap](#roadmap)).

Maintained by **John Harrison** ([@inspiringprotrader2121-coder](https://github.com/inspiringprotrader2121-coder)).

## Features

- **Clipboard history** with configurable size limit and smart dedupe
- **Fuzzy search** across your whole history, ranked by match quality,
  recency, pins and copy counts — plus regex search when you need it
- **Ignored patterns** — regex rules for secrets and noise never enter history
- **Snippets** — named reusable text with `{date}`/`{time}` placeholders
- **Python API, CLI and export** to JSON, Markdown or CSV; import with
  id-level dedupe; stats and diagnostics built in
- **100% local** — history lives in a JSON file in your own user profile
- **Zero runtime dependencies** — pure Python standard library

## Installation

Until the PyPI release lands, install from the repository:

```bash
pip install "clipshelf @ git+https://github.com/inspiringprotrader2121-coder/clipshelf"
```

Or run from source:

```bash
git clone https://github.com/inspiringprotrader2121-coder/clipshelf.git
cd clipshelf
python -m clipshelf --help
```

## Usage

On Windows, running `clipshelf` with no command starts clipboard capture and
saves history to `%APPDATA%\clipshelf\history.json` (stop with `Ctrl+C`).
On other platforms the same engine is available through the command line and
the Python API.

```python
from clipshelf import ClipboardHistory, rank

history = ClipboardHistory(max_items=500)
history.add("git rebase -i HEAD~3")
history.add("SELECT * FROM users WHERE id = 42")

for entry in rank("git reb", [e.text for e in history.entries]):
    print(entry)
```

### Tray UI (in development)

The tray app with a `Ctrl+Shift+V` search popup is not implemented yet. The
hotkeys below describe the intended behaviour and will be wired up in an
upcoming release:

| Planned hotkey | Action |
| --- | --- |
| `Ctrl+Shift+V` | Open clipboard history popup |
| `Ctrl+C` inside popup | Copy selected entry back to clipboard |
| `Ctrl+P` inside popup | Pin / unpin selected entry |
| `Esc` | Close popup |

## Command line

ClipShelf ships a headless command line for scripts, terminals and machines
where the tray app is unavailable. It works against the same history file
the app uses.

| Command | What it does |
| --- | --- |
| `clipshelf` | Start clipboard capture on Windows (headless banner elsewhere) |
| `clipshelf list [--limit N]` | Print stored clips, newest first (`*` marks pinned) |
| `clipshelf search QUERY [--regex] [--pinned]` | Fuzzy or regex search over history |
| `clipshelf add [TEXT]` | Record a clip (reads stdin when TEXT is omitted) |
| `clipshelf export {json,markdown,csv} [--output FILE] [--pinned-only]` | Export history |
| `clipshelf import FILE [--replace]` | Merge a JSON/CSV export into history |
| `clipshelf stats` | Totals, byte counts and most-copied clips |
| `clipshelf snippets add/list/show/render/remove` | Manage reusable snippets |
| `clipshelf doctor` | Environment and data-file diagnostics |

```bash
clipshelf add "deploy command I keep retyping"
clipshelf search deploy
clipshelf search "#\d{4}" --regex --pinned
clipshelf export markdown --output history.md
clipshelf snippets add sig "Best regards, John" && clipshelf snippets render sig
```

Full reference: [docs/CLI.md](docs/CLI.md).

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full workflow.

## Roadmap

- [ ] Tray icon with a `Ctrl+Shift+V` search popup (Win32, no dependencies)
- [ ] Windows 11 fluent styling for the popup
- [ ] Launch on startup
- [ ] Image and file-copy support
- [ ] PyPI release (`pip install clipshelf`)
- [ ] MSI installer via PyInstaller + Inno Setup

## License

MIT — see [LICENSE](LICENSE).