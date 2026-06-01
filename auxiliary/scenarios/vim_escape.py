from __future__ import annotations

from typing import Any

from scenarios.base import Scenario


class VimEscapeScenario(Scenario):
    name = "vim_escape"
    description = "Exit vim correctly from various modes"

    TASKS = [
        {"id": "save_quit_normal", "initial": (["content to save"], (1, 1)), "mode": "normal",
         "instruction": "Save and exit vim.", "hint": "Use ':wq' or 'ZZ'"},
        {"id": "quit_no_save", "initial": (["discard this"], (1, 1)), "mode": "normal",
         "instruction": "Exit without saving.", "hint": "Use ':q!' or 'ZQ'"},
        {"id": "escape_insert_save", "initial": (["typing..."], (1, 8)), "mode": "insert",
         "instruction": "Exit insert mode, save and quit.", "hint": "Press Esc, then :wq"},
        {"id": "escape_insert_quit", "initial": (["wrong text"], (1, 5)), "mode": "insert",
         "instruction": "Exit insert mode, quit without saving.", "hint": "Press Esc, then :q!"},
        {"id": "escape_visual_save", "initial": (["selected text"], (1, 6)), "mode": "visual",
         "instruction": "Exit visual mode, save and quit.", "hint": "Press Esc, then :wq"},
        {"id": "just_quit", "initial": (["read only"], (1, 1)), "mode": "normal",
         "instruction": "Exit vim (unmodified file).", "hint": "Use ':q'"},
    ]

    def get_tasks(self) -> list[dict[str, Any]]:
        return self.TASKS

    def setup_task(self, task: dict[str, Any]) -> None:
        buffer, cursor = task["initial"]
        self.vim.start(buffer)
        self.vim.set_cursor(*cursor)

        mode = task.get("mode", "normal")
        if mode == "insert":
            self.vim.send_keys("i")
        elif mode == "visual":
            self.vim.send_keys("v")
        elif mode == "visual-line":
            self.vim.send_keys("V")

    def check_success(self) -> tuple[bool, float]:
        if not self._task:
            return False, 0.0

        mode = self.vim.get_mode()
        initial_mode = self._task.get("mode", "normal")

        if not self.vim.is_running:
            return True, 1.0

        if mode == "normal" and initial_mode != "normal":
            return False, 0.5

        return False, 0.0
