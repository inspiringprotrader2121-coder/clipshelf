from __future__ import annotations

import sys
import threading
from collections.abc import Callable

CLIPBOARD_POLL_SECONDS = 0.25
MAX_ERRORS = 3
CF_UNICODETEXT = 13
GMEM_MOVEABLE = 0x0002


class MemoryClipboard:
    """In-memory clipboard used for tests and non-Windows development."""

    def __init__(self) -> None:
        self._text = ""
        self._lock = threading.Lock()

    def get_text(self) -> str:
        with self._lock:
            return self._text

    def set_text(self, text: str) -> None:
        with self._lock:
            self._text = text


class WindowsClipboard:
    """Thin ctypes wrapper around the Win32 clipboard API."""

    def __init__(self) -> None:
        if sys.platform != "win32":
            raise OSError("WindowsClipboard requires Windows")
        import ctypes

        self._ctypes = ctypes

    def _user32(self):
        import ctypes

        return ctypes.WinDLL("user32", use_last_error=True)

    def _kernel32(self):
        import ctypes

        return ctypes.WinDLL("kernel32", use_last_error=True)

    def get_text(self) -> str:
        ctypes = self._ctypes
        user32 = self._user32()
        kernel32 = self._kernel32()
        if not user32.OpenClipboard(None):
            raise OSError("OpenClipboard failed")
        try:
            handle = user32.GetClipboardData(CF_UNICODETEXT)
            if not handle:
                return ""
            pointer = kernel32.GlobalLock(handle)
            if not pointer:
                return ""
            try:
                return ctypes.c_wchar_p(pointer).value or ""
            finally:
                kernel32.GlobalUnlock(handle)
        finally:
            user32.CloseClipboard()

    def set_text(self, text: str) -> None:
        ctypes = self._ctypes
        user32 = self._user32()
        kernel32 = self._kernel32()
        if not user32.OpenClipboard(None):
            raise OSError("OpenClipboard failed")
        try:
            user32.EmptyClipboard()
            size = (len(text) + 1) * ctypes.sizeof(ctypes.c_wchar)
            handle = kernel32.GlobalAlloc(GMEM_MOVEABLE, size)
            if not handle:
                raise OSError("GlobalAlloc failed")
            pointer = kernel32.GlobalLock(handle)
            if not pointer:
                raise OSError("GlobalLock failed")
            try:
                ctypes.memmove(pointer, text + "\0", size)
            finally:
                kernel32.GlobalUnlock(handle)
            if not user32.SetClipboardData(CF_UNICODETEXT, handle):
                raise OSError("SetClipboardData failed")
        finally:
            user32.CloseClipboard()


def default_clipboard():
    if sys.platform == "win32":
        return WindowsClipboard()
    return MemoryClipboard()


class ClipboardWatcher:
    """Polls the clipboard and reports new text values to a callback."""

    def __init__(
        self,
        clipboard,
        on_change: Callable[[str], None],
        poll_seconds: float = CLIPBOARD_POLL_SECONDS,
    ) -> None:
        self._clipboard = clipboard
        self._on_change = on_change
        self._poll_seconds = poll_seconds
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="clipshelf-watcher", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None

    def _run(self) -> None:
        last: str | None = None
        errors = 0
        while not self._stop.is_set():
            try:
                current = self._clipboard.get_text()
                errors = 0
            except OSError:
                errors += 1
                if errors >= MAX_ERRORS:
                    break
                current = None
            if current and current != last and current.strip():
                last = current
                self._on_change(current)
            self._stop.wait(self._poll_seconds)
