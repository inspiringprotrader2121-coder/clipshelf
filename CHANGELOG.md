# Changelog

All notable changes to ClipShelf are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project adheres to [Semantic Versioning](https://semver.org/).

## [0.2.1] - 2026-10-13

### Fixed

- Saving from the running app no longer overwrites clips added by the CLI or
  another instance: the history file is reloaded and merged before writing
- Imports and restores now skip duplicate **texts** as well as duplicate ids,
  preserving the one-entry-per-text invariant
- The `ignore_whitespace_clips` setting now truly controls blank-clip
  recording (before, blanks were dropped even when the setting was off, and
  could raise when they reached the engine)
- Clipboard watching reports failure after repeated clipboard errors instead
  of stopping silently
- Snippet loading no longer turns a JSON `null` name into a snippet literally
  named "None"
- `clipshelf export --output` reports unwritable destinations cleanly instead
  of raising a traceback

### Changed

- All file writes (config, history, snippets, exports) go through one atomic
  write helper, `clipshelf.storage.atomic_write_text`
- Documentation now distinguishes the implemented engine/CLI from the
  in-development tray UI, and installation points at the repository until the
  PyPI release lands

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