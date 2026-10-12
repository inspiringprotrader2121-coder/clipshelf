# Contributing to ClipShelf

Thanks for helping out. ClipShelf is a small project, so the bar is simple:
keep it dependency-free, keep tests green.

## Getting started

```bash
git clone https://github.com/inspiringprotrader2121-coder/clipshelf.git
cd clipshelf
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Workflow

1. Open an issue first for anything larger than a typo fix.
2. Fork and branch from `main` (`fix/hotkey-parse`, `feat/image-clips`).
3. Make your change with tests.
4. Run the checks locally:

```bash
ruff check .
ruff format --check .
pytest
```

5. Open a pull request with a short description of the problem and the solution.

## Style

- Python 3.10+, standard library only at runtime.
- `ruff` is the authority; no manual formatting debates.
- Tests live in `tests/` and must describe behavior, not implementation.

## Reporting bugs

Include your Windows version, Python version, and steps to reproduce.
Logs from `clipshelf --list` help when the history file is involved.