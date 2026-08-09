from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from .cf_html import build_cf_html, parse_cf_html
from .normalizer import html_to_rtf, normalize_html, plain_text

SUPPORTED_HOSTS = (
    "chatgpt.com", "chat.openai.com", "claude.ai", "gemini.google.com",
    "copilot.microsoft.com", "perplexity.ai", "grok.com", "x.com", "manus.im", "manus.space",
)
MARKER_FORMAT = "AI Clean Paste Transformed"


def is_supported_source(source_url: str) -> bool:
    hostname = (urlparse(source_url).hostname or "").lower()
    return any(hostname == item or hostname.endswith("." + item) for item in SUPPORTED_HOSTS)


@dataclass(frozen=True)
class ClipboardPayload:
    source_url: str
    html: str
    plain: str
    rtf: str


class ClipboardBackend:
    """Windows clipboard boundary; this class never stores clipboard content."""

    def __init__(self) -> None:
        import win32clipboard  # type: ignore
        import win32con  # type: ignore
        self.win32clipboard = win32clipboard
        self.win32con = win32con
        self.html_format = win32clipboard.RegisterClipboardFormat("HTML Format")
        self.rtf_format = win32clipboard.RegisterClipboardFormat("Rich Text Format")
        self.marker_format = win32clipboard.RegisterClipboardFormat(MARKER_FORMAT)

    def read_html(self) -> bytes | str | None:
        clip = self.win32clipboard
        clip.OpenClipboard()
        try:
            if not clip.IsClipboardFormatAvailable(self.html_format):
                return None
            if clip.IsClipboardFormatAvailable(self.marker_format):
                return None
            return clip.GetClipboardData(self.html_format)
        finally:
            clip.CloseClipboard()

    def write(self, payload: ClipboardPayload) -> None:
        clip = self.win32clipboard
        clip.OpenClipboard()
        try:
            clip.EmptyClipboard()
            clip.SetClipboardData(self.win32con.CF_UNICODETEXT, payload.plain)
            clip.SetClipboardData(self.html_format, build_cf_html(payload.html, payload.source_url))
            clip.SetClipboardData(self.rtf_format, payload.rtf.encode("latin-1", errors="replace"))
            clip.SetClipboardData(self.marker_format, b"1")
        finally:
            clip.CloseClipboard()


class CleanPasteAgent:
    def __init__(self, backend: ClipboardBackend | None = None) -> None:
        self.backend = backend or ClipboardBackend()
        self.enabled = True
        self._last_digest = ""

    def process_clipboard(self) -> bool:
        if not self.enabled:
            return False
        raw = self.backend.read_html()
        if raw is None:
            return False
        source_url, fragment = parse_cf_html(raw)
        if not source_url or not is_supported_source(source_url):
            return False
        digest = hashlib.sha256(fragment.encode("utf-8")).hexdigest()
        if digest == self._last_digest:
            return False
        normalized = normalize_html(fragment)
        if not normalized:
            return False
        payload = ClipboardPayload(source_url, normalized, plain_text(normalized), html_to_rtf(normalized))
        self.backend.write(payload)
        self._last_digest = digest
        return True


class ClipboardNotificationWindow:
    """Message-only listener using AddClipboardFormatListener; no polling or key hook."""

    def __init__(self, agent: CleanPasteAgent) -> None:
        import ctypes
        import win32con  # type: ignore
        import win32gui  # type: ignore
        self.agent = agent
        self.win32con = win32con
        self.win32gui = win32gui
        self.user32 = ctypes.windll.user32
        self.message = 0x031D  # WM_CLIPBOARDUPDATE
        klass = win32gui.WNDCLASS()
        klass.lpszClassName = "AICleanPasteClipboardListener"
        klass.lpfnWndProc = self._window_proc
        try:
            atom = win32gui.RegisterClass(klass)
        except Exception:
            atom = win32gui.GetClassInfo(None, klass.lpszClassName)[0]
        self.hwnd = win32gui.CreateWindow(atom, klass.lpszClassName, 0, 0, 0, 0, 0, 0, 0, 0, None)
        if not self.user32.AddClipboardFormatListener(self.hwnd):
            win32gui.DestroyWindow(self.hwnd)
            raise ctypes.WinError()

    def _window_proc(self, hwnd: int, message: int, wparam: int, lparam: int) -> int:
        if message == self.message:
            try:
                self.agent.process_clipboard()
            except Exception:
                # Clipboard contention is expected; preserve the user's clipboard untouched.
                pass
            return 0
        if message == self.win32con.WM_DESTROY:
            self.user32.RemoveClipboardFormatListener(hwnd)
            self.win32gui.PostQuitMessage(0)
            return 0
        return self.win32gui.DefWindowProc(hwnd, message, wparam, lparam)

    def run(self) -> None:
        self.win32gui.PumpMessages()

    def stop(self) -> None:
        self.win32gui.PostMessage(self.hwnd, self.win32con.WM_CLOSE, 0, 0)


def app_data_directory() -> Path:
    return Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "AICleanPaste"
