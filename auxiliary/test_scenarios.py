#!/usr/bin/env python3
import sys
sys.path.insert(0, ".")

from scenarios import GitRebaseScenario, VimBasicsScenario, VimEscapeScenario, ObservationMode
from env import VimArenaEnv

SOLUTIONS = {
    "git_rebase": {
        "reorder_simple": "3GddggP",
        "squash_last_two": "3Gcwsquash<Esc>",
        "squash_all": "2Gcwsquash<Esc>j0cwsquash<Esc>j0cwsquash<Esc>",
        "fixup_last": "3Gcwfixup<Esc>",
        "drop_middle": "2Gdd",
        "reword_first": "1Gcwreword<Esc>",
        "abort": "ggdG",
    },
    "vim_basics": {
        "delete_line": "dd",
        "delete_word": "dw",
        "insert_text": "ibeautiful <Esc>",
        "append_line": "Gothird line<Esc>",
        "goto_change": "3GccCHANGED<Esc>",
        "substitute": ":s/foo/baz/<CR>",
        "substitute_all": ":%s/foo/qux/g<CR>",
        "yank_paste": "yyGp",
        "change_quotes": 'ci"goodbye<Esc>',
        "join_lines": "J",
    },
}


def test_scenario(scenario_cls, solutions):
    name = scenario_cls.name
    print(f"\n{'='*50}\n{name}\n{'='*50}")
    passed = 0
    with scenario_cls() as scenario:
        for task in scenario.get_tasks():
            tid = task["id"]
            if tid not in solutions:
                continue
            scenario.reset(task_id=tid)
            result = scenario.step(solutions[tid])
            ok = result.reward == 1.0
            passed += ok
            print(f"{'✓' if ok else '✗'} {tid}: {result.reward:.2f}")
    return passed, len(solutions)


def test_raw_mode():
    print(f"\n{'='*50}\nraw observation mode\n{'='*50}")
    with GitRebaseScenario(observation_mode=ObservationMode.RAW) as s:
        obs = s.reset(task_id="squash_last_two")
        print(f"type: {obs['type']}")
        print(obs["terminal"][:300])


def test_env():
    print(f"\n{'='*50}\nVimArenaEnv\n{'='*50}")
    env = VimArenaEnv()
    obs = env.reset(scenario="vim_basics", task_id="delete_line")
    result = env.step("dd")
    print(f"delete_line: reward={result.reward}")
    obs = env.reset(scenario="git_rebase", observation_mode="raw")
    print(f"raw mode: {obs['type']}")
    env.close()
    print("✓ env ok")


if __name__ == "__main__":
    total_passed, total_tests = 0, 0
    p, t = test_scenario(GitRebaseScenario, SOLUTIONS["git_rebase"])
    total_passed += p
    total_tests += t
    p, t = test_scenario(VimBasicsScenario, SOLUTIONS["vim_basics"])
    total_passed += p
    total_tests += t
    test_raw_mode()
    test_env()
    print(f"\n{'='*50}\n{total_passed}/{total_tests} tests passed\n{'='*50}")
