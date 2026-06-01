from __future__ import annotations

from typing import Any, Callable

from scenarios.base import Scenario

COMMITS = [
    ("a1b2c3d", "Add user authentication"),
    ("e4f5g6h", "Fix login bug"),
    ("i7j8k9l", "Update dependencies"),
    ("m0n1o2p", "Add logout feature"),
    ("q3r4s5t", "Fix typo in readme"),
    ("u6v7w8x", "Refactor auth module"),
    ("y9z0a1b", "Add unit tests"),
    ("c2d3e4f", "Update documentation"),
]

REBASE_COMMENTS = [
    "", "# Rebase onto main", "#", "# Commands:",
    "# p, pick = use commit", "# r, reword = use commit, but edit the commit message",
    "# e, edit = use commit, but stop for amending",
    "# s, squash = use commit, but meld into previous commit",
    "# f, fixup = like squash, but discard this commit's log message",
    "# d, drop = remove commit", "#",
    "# These lines can be re-ordered; they are executed from top to bottom.",
    "# If you remove a line here THAT COMMIT WILL BE LOST.",
]

ACTION_EXPANSIONS = {"p ": "pick ", "r ": "reword ", "e ": "edit ", "s ": "squash ", "f ": "fixup ", "d ": "drop "}


def task(
    id: str, n: int, instruction: str, transform: Callable, hint: str | None = None
) -> dict[str, Any]:
    return {"id": id, "num_commits": n, "instruction": instruction, "transform": transform,
            "context": f"git rebase -i HEAD~{n}", "hint": hint}


class GitRebaseScenario(Scenario):
    name = "git_rebase"
    description = "Edit git rebase todo list to reorder, squash, fixup, or drop commits"

    TASKS = [
        task("reorder_simple", 3, "Reorder commits so the last comes first.",
             lambda l: [l[2], l[0], l[1]], "Move last 'pick' line to top"),
        task("squash_last_two", 3, "Squash the last commit into the second-to-last.",
             lambda l: [l[0], l[1], l[2].replace("pick", "squash", 1)], "Change 'pick' to 'squash' on last"),
        task("squash_all", 4, "Squash all commits into the first one.",
             lambda l: [l[0]] + [x.replace("pick", "squash", 1) for x in l[1:]], "Keep first 'pick', rest 'squash'"),
        task("fixup_last", 3, "Fixup the last commit into the previous.",
             lambda l: [l[0], l[1], l[2].replace("pick", "fixup", 1)], "Change 'pick' to 'fixup' on last"),
        task("drop_middle", 3, "Drop the middle commit.",
             lambda l: [l[0], l[2]], "Delete middle line or change to 'drop'"),
        task("reword_first", 3, "Mark first commit for rewording.",
             lambda l: [l[0].replace("pick", "reword", 1), l[1], l[2]], "Change 'pick' to 'reword' on first"),
        task("reorder_and_squash", 4, "Move last commit to second position and squash into first.",
             lambda l: [l[0], l[3].replace("pick", "squash", 1), l[1], l[2]], "Move last to pos 2, change to 'squash'"),
        task("abort", 3, "Abort rebase by deleting all lines.",
             lambda l: [], "Delete all with 'ggdG' then :wq"),
    ]

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._original_todo: list[str] = []

    def get_tasks(self) -> list[dict[str, Any]]:
        return self.TASKS

    def setup_task(self, task: dict[str, Any]) -> None:
        n = task.get("num_commits", 3)
        self._original_todo = [f"pick {h} {m}" for h, m in COMMITS[:n]]
        self.vim.start(self._original_todo + REBASE_COMMENTS)
        self.vim.set_cursor(1, 1)

    def check_success(self) -> tuple[bool, float]:
        if not self._task:
            return False, 0.0

        buffer = self.vim.get_buffer()
        current = [l for l in buffer if l.strip() and not l.startswith("#")]
        expected = self._task["transform"](self._original_todo)

        current_norm = [self._normalize(l) for l in current]
        expected_norm = [self._normalize(l) for l in expected]

        if current_norm == expected_norm:
            return True, 1.0

        if not expected_norm:
            return len(current) == 0, 1.0 if not current else 0.5

        matches = sum(1 for c, e in zip(current_norm, expected_norm) if c == e)
        return False, matches / max(len(expected_norm), 1)

    @staticmethod
    def _normalize(line: str) -> str:
        line = line.strip()
        for short, full in ACTION_EXPANSIONS.items():
            if line.startswith(short):
                return full + line[2:]
        return line
