# Changelog

All notable changes to ClipShelf are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- Clipboard history store with dedupe, pinning and size cap
- Fuzzy ranking with recency boost
- Win32 clipboard integration through `ctypes`
- Polling `ClipboardWatcher` background thread
- JSON config with validation and atomic writes
- CLI: `--list`, `--once`, `--config`, `--version`
- Cross-platform CI (lint + test matrix)

## [0.1.0] - 2026-10-12

### Added

- Initial release