from __future__ import annotations

from typing import Any

from bench_common.env_sdk.base import BaseEnv, StepResult

from scenarios import SCENARIOS, Scenario, ObservationMode


class VimArenaEnv(BaseEnv):
    """VimArena mesocosm environment."""

    DEFAULT_SCENARIO = "git_rebase"

    def __init__(self) -> None:
        self._scenario: Scenario | None = None
        self._scenario_name = self.DEFAULT_SCENARIO
        self._obs_mode = ObservationMode.STRUCTURED

    def reset(
        self,
        seed: int | None = None,
        scenario: str | None = None,
        task_id: str | None = None,
        observation_mode: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        if scenario and scenario != self._scenario_name:
            self._close_scenario()
            self._scenario_name = scenario

        if observation_mode:
            new_mode = ObservationMode(observation_mode)
            if new_mode != self._obs_mode:
                self._obs_mode = new_mode
                self._close_scenario()

        if not self._scenario:
            self._scenario = SCENARIOS[self._scenario_name](observation_mode=self._obs_mode)

        return self._scenario.reset(seed=seed, task_id=task_id)

    def step(self, action: Any) -> StepResult:
        if not self._scenario:
            raise RuntimeError("Call reset() first")
        result = self._scenario.step(str(action))
        return StepResult(
            observation=result.observation,
            reward=result.reward,
            terminated=result.terminated,
            truncated=result.truncated,
            info=result.info,
        )

    def close(self) -> None:
        self._close_scenario()

    def _close_scenario(self) -> None:
        if self._scenario:
            self._scenario.close()
            self._scenario = None

    @classmethod
    def list_scenarios(cls) -> list[str]:
        return list(SCENARIOS.keys())

    @classmethod
    def list_tasks(cls, scenario: str) -> list[str]:
        with SCENARIOS[scenario]() as s:
            return [t["id"] for t in s.get_tasks()]
