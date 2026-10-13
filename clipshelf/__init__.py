"""ClipShelf - lightweight clipboard history manager for Windows."""

from clipshelf.config import Config
from clipshelf.history import ClipboardHistory, ClipEntry
from clipshelf.rules import RuleSet
from clipshelf.search import rank, rank_entries
from clipshelf.snippets import Snippet, SnippetStore
from clipshelf.stats import Stats, analyze

__version__ = "0.2.1"

__all__ = [
    "ClipEntry",
    "ClipboardHistory",
    "Config",
    "RuleSet",
    "Snippet",
    "SnippetStore",
    "Stats",
    "analyze",
    "rank",
    "rank_entries",
    "__version__",
]
