# Architecture

ClipShelf is deliberately small: a pure-Python core that can be tested
anywhere, wrapped in a thin Windows layer.

## Module map

| Module | Responsibility |
| --- | --- |
| `clipshelf.history` | `ClipEntry` records and `ClipboardHistory`: dedupe by text, pinning, size cap, restore and snapshot |
| `clipshelf.search` | `rank()` for plain text lists, `rank_entries()` for stored entries with pinned/copies bonuses and a regex mode |
| `clipshelf.rules` | `RuleSet`: compiled regex ignore rules used to keep secrets and noise out of history |
| `clipshelf.snippets` | `Snippet` and `SnippetStore`: named reusable text with `{date}`, `{time}`, `{datetime}` rendering |
| `clipshelf.stats` | `analyze()` and `summary_lines()`: totals, byte counts, most-copied clips |
| `clipshelf.portability` | Validation and (de)serialisation for JSON, Markdown and CSV exports |
| `clipshelf.config` | `Config` dataclass, validation, atomic JSON save, platform data dirs |
| `clipshelf.clipboard` | `MemoryClipboard`, the Win32 `WindowsClipboard` (ctypes) and the polling `ClipboardWatcher` |
| `clipshelf.app` | `App`: wires config, history, rules, watcher; `load_history`/`save_history` |
| `clipshelf.__main__` | argparse subcommands; the only place that prints user output |

## Data flow

```
clipboard ──poll──▶ ClipboardWatcher ──▶ App.on_clip
                                          │ whitespace policy
                                          │ RuleSet.should_ignore
                                          ▼
                                   ClipboardHistory.add  (dedupe, pin, cap)
                                          │
                       save_history ◀─────┘        search / export / stats
                                          │                 ▲
                                   history.json         CLI reads the
                                                        same file
```

Every entry point (tray app, CLI) goes through the same history and
portability code, so a clip recorded by the app is identical to one added
with `clipshelf add`.

## Files on disk

All under the data dir (`%APPDATA%\clipshelf` on Windows,
`~/.clipshelf` everywhere else):

| File | Contents |
| --- | --- |
| `history.json` | List of clip entries: `text`, `id`, `created_at`, `copied_at`, `copies`, `pinned` |
| `snippets.json` | List of snippets: `name`, `text`, `created_at`, `updated_at`, `uses` |
| `config.json` | Validated settings, written atomically via a temp file + rename |

Readers are defensive: malformed files or entries are skipped rather than
crashing the app.

## Platform split

The core modules import nothing platform specific. Windows-only behaviour
lives in `clipshelf.clipboard.WindowsClipboard` (raises `OSError` off
Windows) and in `clipshelf.__main__.main`, which starts the tray loop on
Windows and prints a headless banner elsewhere. That is what lets the test
suite run on Linux, macOS and Windows CI from one codebase.

## Testing

`pytest` covers the core (`tests/test_history.py`, `test_search.py`,
`test_rules.py`, `test_snippets.py`, `test_portability.py`, `test_stats.py`),
the wiring (`test_config.py`, `test_app.py`) and the CLI end to end
(`test_cli.py`). `ruff check` and `ruff format --check` gate every push; CI
runs the matrix on Windows, macOS and Linux.