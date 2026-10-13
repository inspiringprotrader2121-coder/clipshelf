# ClipShelf

A lightweight clipboard history manager for Windows.

ClipShelf sits in your system tray, remembers everything you copy, and lets
you bring any previous clip back with a single hotkey — no cloud sync, no
account, no telemetry.

Maintained by **John Harrison** ([@inspiringprotrader2121-coder](https://github.com/inspiringprotrader2121-coder)).

## Features

- **Infinite clipboard history** with configurable size limit and smart dedupe
- **Fuzzy search** across your whole history, ranked by match quality and recency
- **Pin important clips** so they survive history rotation
- **Global hotkey** (`Ctrl+Shift+V`) opens the search popup from anywhere
- **100% local** — history lives in a JSON file in your own user profile
- **Zero runtime dependencies** — pure Python standard library

## Installation

```bash
pip install clipshelf
```

Or run from source:

```bash
git clone https://github.com/inspiringprotrader2121-coder/clipshelf.git
cd clipshelf
python -m clipshelf
```

## Usage

| Hotkey | Action |
| --- | --- |
| `Ctrl+Shift+V` | Open clipboard history popup |
| `Ctrl+C` inside popup | Copy selected entry back to clipboard |
| `Ctrl+P` inside popup | Pin / unpin selected entry |
| `Esc` | Close popup |

On launch, ClipShelf restores your history from
`%APPDATA%\clipshelf\history.json` and starts watching the clipboard.

```python
from clipshelf import ClipboardHistory, rank

history = ClipboardHistory(max_items=500)
history.add("git rebase -i HEAD~3")
history.add("SELECT * FROM users WHERE id = 42")

for entry in rank("git reb", [e.text for e in history.entries]):
    print(entry)
```

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full workflow.

## Roadmap

- [ ] Windows 11 fluent styling for the search popup
- [ ] Image and file-copy support
- [ ] Optional tray quick-menu of the last 10 clips
- [ ] MSI installer via PyInstaller + Inno Setup

## License

MIT — see [LICENSE](LICENSE).