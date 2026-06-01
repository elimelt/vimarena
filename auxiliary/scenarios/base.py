from __future__ import annotations

import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from vim_driver import VimDriver
from terminal_render import raw_observation


class ObservationMode(Enum):
    STRUCTURED = "structured"
    RAW = "raw"


@dataclass
class StepResult:
    observation: dict[str, Any]
    reward: float
    terminated: bool
    truncated: bool
    info: dict[str, Any] = field(default_factory=dict)


class Scenario(ABC):
    name: str = "base"
    description: str = ""

    def __init__(
        self,
        observation_mode: ObservationMode = ObservationMode.STRUCTURED,
        terminal_size: tuple[int, int] = (24, 80),
    ) -> None:
        self.observation_mode = observation_mode
        self.terminal_rows, self.terminal_cols = terminal_size
        self.vim = VimDriver()
        self._task: dict[str, Any] | None = None
        self._step_count = 0
        self._max_steps = 10

    @abstractmethod
    def get_tasks(self) -> list[dict[str, Any]]:
        pass

    @abstractmethod
    def setup_task(self, task: dict[str, Any]) -> None:
        pass

    @abstractmethod
    def check_success(self) -> tuple[bool, float]:
        pass

    def reset(self, seed: int | None = None, task_id: str | None = None) -> dict[str, Any]:
        rng = random.Random(seed)
        tasks = self.get_tasks()

        if task_id:
            self._task = next((t for t in tasks if t["id"] == task_id), None)
            if not self._task:
                raise ValueError(f"Unknown task: {task_id}")
        else:
            self._task = rng.choice(tasks)

        self._step_count = 0
        self._max_steps = self._task.get("max_steps", 10)
        self.setup_task(self._task)
        return self._observe()

    def step(self, action: str) -> StepResult:
        if not self._task:
            raise RuntimeError("Call reset() first")

        self._step_count += 1
        still_running = self.vim.send_keys(action)

        if not still_running:
            success, reward = self.check_success()
            return StepResult(
                observation={"type": "exited", "task": self._task["instruction"]},
                reward=reward,
                terminated=True,
                truncated=False,
                info={"task_id": self._task["id"], "step": self._step_count, "success": success, "exited": True},
            )

        success, reward = self.check_success()
        truncated = self._step_count >= self._max_steps and not success

        return StepResult(
            observation=self._observe(),
            reward=reward,
            terminated=success,
            truncated=truncated,
            info={"task_id": self._task["id"], "step": self._step_count, "success": success},
        )

    def _observe(self) -> dict[str, Any]:
        buffer = self.vim.get_buffer()
        cursor = self.vim.get_cursor()
        mode = self.vim.get_mode()

        if self.observation_mode == ObservationMode.RAW:
            return {
                "type": "raw",
                "terminal": raw_observation(buffer, cursor, mode, self._task.get("context")),
                "task": self._task["instruction"],
            }

        return {
            "type": "structured",
            "task": self._task["instruction"],
            "buffer": buffer,
            "cursor": {"line": cursor[0], "col": cursor[1]},
            "mode": mode,
            "context": self._task.get("context"),
            "hint": self._task.get("hint"),
        }

    def close(self) -> None:
        self.vim.stop()

    def __enter__(self) -> Scenario:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
