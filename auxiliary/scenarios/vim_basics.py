from __future__ import annotations

from difflib import SequenceMatcher
from typing import Any

from scenarios.base import Scenario


class VimBasicsScenario(Scenario):
    name = "vim_basics"
    description = "Foundational vim operations: delete, insert, navigate, search/replace"

    TASKS = [
        {"id": "delete_line", "initial": (["line one", "line two", "line three"], (2, 1)),
         "instruction": "Delete the current line.", "target": ["line one", "line three"],
         "hint": "Use 'dd'"},
        {"id": "delete_word", "initial": (["hello world today"], (1, 7)),
         "instruction": "Delete the word under cursor.", "target": ["hello today"],
         "hint": "Use 'dw'"},
        {"id": "insert_text", "initial": (["hello world"], (1, 7)),
         "instruction": "Insert 'beautiful ' before cursor.", "target": ["hello beautiful world"],
         "hint": "Use 'i' to insert"},
        {"id": "append_line", "initial": (["first line", "second line"], (1, 1)),
         "instruction": "Add 'third line' at end of file.", "target": ["first line", "second line", "third line"],
         "hint": "Use 'Go' to open line at end"},
        {"id": "goto_change", "initial": (["line 1", "line 2", "line 3", "line 4", "line 5"], (1, 1)),
         "instruction": "Change line 3 to 'CHANGED'.", "target": ["line 1", "line 2", "CHANGED", "line 4", "line 5"],
         "hint": "Use '3G' then 'cc'"},
        {"id": "substitute", "initial": (["foo bar foo"], (1, 1)),
         "instruction": "Replace first 'foo' with 'baz'.", "target": ["baz bar foo"],
         "hint": "Use ':s/foo/baz/'"},
        {"id": "substitute_all", "initial": (["foo bar foo", "foo baz foo"], (1, 1)),
         "instruction": "Replace all 'foo' with 'qux'.", "target": ["qux bar qux", "qux baz qux"],
         "hint": "Use ':%s/foo/qux/g'"},
        {"id": "yank_paste", "initial": (["copy me", "other line"], (1, 1)),
         "instruction": "Copy first line, paste after last.", "target": ["copy me", "other line", "copy me"],
         "hint": "Use 'yy' then 'Gp'"},
        {"id": "change_quotes", "initial": (['say "hello" please'], (1, 6)),
         "instruction": "Change text inside quotes to 'goodbye'.", "target": ['say "goodbye" please'],
         "hint": "Use 'ci\"'"},
        {"id": "join_lines", "initial": (["first", "second"], (1, 1)),
         "instruction": "Join the two lines.", "target": ["first second"],
         "hint": "Use 'J'"},
    ]

    def get_tasks(self) -> list[dict[str, Any]]:
        return self.TASKS

    def setup_task(self, task: dict[str, Any]) -> None:
        buffer, cursor = task["initial"]
        self.vim.start(buffer)
        self.vim.set_cursor(*cursor)

    def check_success(self) -> tuple[bool, float]:
        if not self._task:
            return False, 0.0

        current = "\n".join(self.vim.get_buffer())
        target = "\n".join(self._task["target"])

        if current == target:
            return True, 1.0
        return False, SequenceMatcher(None, current, target).ratio()
