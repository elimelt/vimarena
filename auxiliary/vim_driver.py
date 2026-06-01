from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import time
from typing import Any

import pexpect

VIM_APPIMAGE_URL = "https://github.com/vim/vim-appimage/releases/download/v9.2.0555/Vim-v9.2.0555.glibc2.34-x86_64.AppImage"


def _ensure_vim() -> str:
    """Find or install vim, return path to executable."""
    for editor in ["nvim", "vim", "vi"]:
        path = shutil.which(editor)
        if path:
            return path

    # Install vim AppImage to user cache
    cache_dir = os.path.expanduser("~/.cache/vimarena")
    vim_bin = os.path.join(cache_dir, "squashfs-root/usr/bin/vim")

    if os.path.exists(vim_bin):
        return vim_bin

    os.makedirs(cache_dir, exist_ok=True)
    appimage = os.path.join(cache_dir, "vim.appimage")

    # Use urllib instead of curl for portability
    import urllib.request
    urllib.request.urlretrieve(VIM_APPIMAGE_URL, appimage)
    os.chmod(appimage, 0o755)
    subprocess.run([appimage, "--appimage-extract"], cwd=cache_dir, check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if os.path.exists(vim_bin):
        return vim_bin
    raise RuntimeError("Failed to install vim")


class VimDriver:
    """PTY-based vim driver - works with vim, vi, or nvim. Auto-installs if needed."""

    SPECIAL_KEYS = {
        "<Esc>": "\x1b", "<CR>": "\r", "<Enter>": "\r", "<Return>": "\r",
        "<Tab>": "\t", "<BS>": "\x7f", "<Backspace>": "\x7f", "<Space>": " ", "<Lt>": "<",
    }

    def __init__(self, rows: int = 24, cols: int = 80) -> None:
        self._proc: pexpect.spawn | None = None
        self._tmpfile: str | None = None
        self._rows = rows
        self._cols = cols
        self._last_buffer: list[str] = []
        self._last_cursor: tuple[int, int] = (1, 1)
        self._last_mode: str = "normal"
        self._editor: str | None = None

    @property
    def is_running(self) -> bool:
        return self._proc is not None and self._proc.isalive()

    def start(self, content: list[str] | None = None) -> None:
        self.stop()
        self._editor = _ensure_vim()

        # Create temp file with content
        fd, self._tmpfile = tempfile.mkstemp(suffix=".txt", prefix="vimarena_")
        os.close(fd)
        if content:
            with open(self._tmpfile, "w") as f:
                f.write("\n".join(content))

        # Spawn vim in pty
        cmd = f"{self._editor} -u NONE {self._tmpfile}"
        self._proc = pexpect.spawn(cmd, dimensions=(self._rows, self._cols), encoding="utf-8")
        self._proc.delaybeforesend = 0.01
        time.sleep(0.1)  # Let vim initialize
        self._read_state()

    def stop(self) -> None:
        if self._proc:
            try:
                if self._proc.isalive():
                    self._proc.sendline("\x1b:qa!")
                    self._proc.wait()
            except Exception:
                pass
            self._proc = None
        if self._tmpfile and os.path.exists(self._tmpfile):
            os.remove(self._tmpfile)
            self._tmpfile = None

    def get_buffer(self) -> list[str]:
        if self._tmpfile and os.path.exists(self._tmpfile):
            with open(self._tmpfile) as f:
                return f.read().splitlines()
        return self._last_buffer

    def set_buffer(self, lines: list[str]) -> None:
        if self._tmpfile:
            with open(self._tmpfile, "w") as f:
                f.write("\n".join(lines))
        self._last_buffer = list(lines)
        # Reload in vim
        if self.is_running:
            self.send_keys("\x1b:e!<CR>")

    def get_cursor(self) -> tuple[int, int]:
        return self._last_cursor

    def set_cursor(self, line: int, col: int) -> None:
        if self.is_running:
            self.send_keys(f"\x1b{line}G{col}|")
        self._last_cursor = (line, col)

    def get_mode(self) -> str:
        return self._last_mode

    def get_screen(self) -> str:
        """Get raw terminal screen content."""
        if not self.is_running:
            return ""
        try:
            self._proc.expect([pexpect.TIMEOUT], timeout=0.05)
        except Exception:
            pass
        return self._strip_ansi(self._proc.before or "")

    def send_keys(self, keys: str) -> bool:
        if not self.is_running:
            return False
        translated = self._translate_keys(keys)
        try:
            self._proc.send(translated)
            time.sleep(0.05)  # Let vim process
            self._read_state()
            return self.is_running
        except Exception:
            return False

    def _read_state(self) -> None:
        if not self.is_running:
            return
        # Read current file content
        if self._tmpfile and os.path.exists(self._tmpfile):
            # Force vim to write current state
            try:
                self._proc.send("\x1b:w\r")
                time.sleep(0.05)
                with open(self._tmpfile) as f:
                    self._last_buffer = f.read().splitlines()
            except Exception:
                pass

    def _translate_keys(self, keys: str) -> str:
        for notation, char in self.SPECIAL_KEYS.items():
            keys = keys.replace(notation, char)
        return re.sub(r"<C-([a-zA-Z])>", lambda m: chr(ord(m.group(1).lower()) - ord("a") + 1), keys, flags=re.I)

    @staticmethod
    def _strip_ansi(text: str) -> str:
        return re.sub(r"\x1b\[[0-9;]*[a-zA-Z]|\x1b\][^\x07]*\x07|\x1b[()][AB012]", "", text)

    def __enter__(self) -> VimDriver:
        return self

    def __exit__(self, *args: Any) -> None:
        self.stop()
