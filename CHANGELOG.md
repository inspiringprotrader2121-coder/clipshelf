# Changelog

All notable changes to ClipShelf are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project adheres to [Semantic Versioning](https://semver.org/).

## [0.2.0] - 2026-10-13

### Added

- Named snippet store with `{date}`, `{time}` and `{datetime}` placeholder
  rendering
- Clipboard ignore rules (case-insensitive, multiline regex) enforced by the
  watcher before anything is recorded
- History export as JSON, Markdown or CSV, and JSON/CSV import with
  id-level deduplication
- History statistics: totals, byte counts, oldest/newest and most-copied
  clips
- Regex and pinned-aware search over stored entries (`rank_entries`)
- CLI rebuilt around subcommands: `list`, `search`, `add`, `export`,
  `import`, `stats`, `doctor`, `once`, `snippets`
- `docs/CLI.md` command reference and `docs/ARCHITECTURE.md` design notes
- PyInstaller spec for standalone builds under `packaging/`

### Changed

- `Config` gains `ignore_patterns`; history reading and writing now live in
  `clipshelf.portability` so the CLI and the tray app share one code path
- The old flat CLI flags were replaced by subcommands (`clipshelf list`
  instead of `clipshelf --list`)

## [0.1.0] - 2026-10-12

### Added

- Initial release: clipboard history store with dedupe, pinning and size
  cap, fuzzy ranking with a recency boost, Win32 clipboard integration
  through `ctypes`, a polling `ClipboardWatcher`, JSON config with
  validation and atomic writes, and cross-platform CI