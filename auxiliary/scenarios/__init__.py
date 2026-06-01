from scenarios.base import Scenario, StepResult, ObservationMode
from scenarios.git_rebase import GitRebaseScenario
from scenarios.vim_basics import VimBasicsScenario
from scenarios.vim_escape import VimEscapeScenario

SCENARIOS: dict[str, type[Scenario]] = {
    "git_rebase": GitRebaseScenario,
    "vim_basics": VimBasicsScenario,
    "vim_escape": VimEscapeScenario,
}

__all__ = [
    "Scenario", "StepResult", "ObservationMode", "SCENARIOS",
    "GitRebaseScenario", "VimBasicsScenario", "VimEscapeScenario",
]
