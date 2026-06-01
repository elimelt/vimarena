from __future__ import annotations

import os
import re
import tempfile
from typing import Any

import pynvim


class VimDriver:
    """Headless neovim driver for programmatic vim interaction."""

    SPECIAL_KEYS = {
        "<Esc>": "\x1b", "<CR>": "\r", "<Enter>": "\r", "<Return>": "\r",
        "<Tab>": "\t", "<BS>": "\x08", "<Backspace>": "\x08", "<Space>": " ", "<Lt>": "<",
    }
    MODE_NAMES = {
        "n": "normal", "i": "insert", "v": "visual", "V": "visual-line",
        "\x16": "visual-block", "c": "command", "R": "replace", "t": "terminal",
    }

    def __init__(self) -> None:
        self._nvim: pynvim.Nvim | None = None
        self._tmpfile: str | None = None
        self._last_buffer: list[str] = []
        self._last_cursor: tuple[int, int] = (1, 1)
        self._last_mode: str = "normal"

    @property
    def is_running(self) -> bool:
        return self._nvim is not None

    def start(self, content: list[str] | None = None) -> None:
        self.stop()
        fd, self._tmpfile = tempfile.mkstemp(suffix=".txt", prefix="vimarena_")
        os.close(fd)
        if content:
            with open(self._tmpfile, "w") as f:
                f.write("\n".join(content))
        self._nvim = pynvim.attach("child", argv=["nvim", "--headless", "--embed", "-u", "NONE", self._tmpfile])
        self._nvim.feedkeys("\x1b", "n", True)

    def stop(self) -> None:
        if self._nvim:
            try:
                self._nvim.command("qa!")
            except Exception:
                pass
            self._nvim = None
        if self._tmpfile and os.path.exists(self._tmpfile):
            os.remove(self._tmpfile)
            self._tmpfile = None

    def get_buffer(self) -> list[str]:
        if not self._nvim:
            return self._last_buffer
        return list(self._nvim.current.buffer[:])

    def set_buffer(self, lines: list[str]) -> None:
        self._nvim.current.buffer[:] = lines
        self._last_buffer = list(lines)

    def get_cursor(self) -> tuple[int, int]:
        if not self._nvim:
            return self._last_cursor
        row, col = self._nvim.current.window.cursor
        return (row, col + 1)

    def set_cursor(self, line: int, col: int) -> None:
        self._nvim.current.window.cursor = (line, max(0, col - 1))
        self._last_cursor = (line, col)

    def get_mode(self) -> str:
        if not self._nvim:
            return self._last_mode
        mode = self._nvim.api.get_mode()["mode"]
        return self.MODE_NAMES.get(mode, mode)

    def send_keys(self, keys: str) -> bool:
        self._cache_state()
        try:
            self._nvim.feedkeys(self._translate_keys(keys), "t", True)
            self._nvim.command("redraw")
            self._cache_state()
            return True
        except Exception:
            self._nvim = None
            return False

    def _cache_state(self) -> None:
        if not self._nvim:
            return
        try:
            self._last_buffer = list(self._nvim.current.buffer[:])
            row, col = self._nvim.current.window.cursor
            self._last_cursor = (row, col + 1)
            self._last_mode = self.MODE_NAMES.get(self._nvim.api.get_mode()["mode"], "normal")
        except Exception:
            pass

    def _translate_keys(self, keys: str) -> str:
        for notation, char in self.SPECIAL_KEYS.items():
            keys = keys.replace(notation, char)
        return re.sub(r"<C-([a-zA-Z])>", lambda m: chr(ord(m.group(1).lower()) - ord("a") + 1), keys, flags=re.I)

    def __enter__(self) -> VimDriver:
        return self

    def __exit__(self, *args: Any) -> None:
        self.stop()
