"""ClipShelf - lightweight clipboard history manager for Windows."""

from clipshelf.config import Config
from clipshelf.history import ClipboardHistory, ClipEntry
from clipshelf.search import rank

__version__ = "0.1.0"

__all__ = ["ClipEntry", "ClipboardHistory", "Config", "rank", "__version__"]
