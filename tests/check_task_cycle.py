#!/usr/bin/env python3
"""Behavior tests for the task-cycle CLI and the shared hook decision core.

Run directly; this file deliberately avoids a test framework so the harness
stays dependency-free:

    python3 tests/check_task_cycle.py

Each case gets its own temporary repository so failures stay isolated.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "template" / "scripts"
CLI = SCRIPTS / "task_cycle.py"

sys.path.insert(0, str(SCRIPTS))

from task_cycle_core import evaluate  # noqa: E402

FAILURES: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"ok   {name}")
    else:
        print(f"FAIL {name} {detail}")
        FAILURES.append(name)


def run(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CLI), *args],
        cwd=repo,
        capture_output=True,
        text=True,
    )


def make_repo(tmp: str) -> Path:
    repo = Path(tmp) / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    return repo


def state(repo: Path) -> dict:
    return json.loads((repo / ".kaizen" / "task-cycle.json").read_text(encoding="utf-8"))


def write_retrospective(repo: Path) -> str:
    path = repo / "docs" / "agents" / "retrospectives" / "2026-01-01-task.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "# Task Retrospective: test\n\n"
        "## Evidence\n\n## Friction, Failures, and Surprises\n\n"
        "## Discovered Issues\n\n## Lessons\n\n"
        "## Harness Changes Applied\n\n## Rules Reviewed for Removal\n",
        encoding="utf-8",
    )
    return "docs/agents/retrospectives/2026-01-01-task.md"


def test_contract_preserving_path() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo(tmp)
        run(repo, "start", "--task", "t1", "--title", "test")
        check("start begins in classification", state(repo)["phase"] == "classification")

        result = run(
            repo, "classify", "--kind", "contract-preserving",
            "--reason", "fixed by issue", "--decided-by", "agent",
        )
        check("preserving classify -> development", state(repo)["phase"] == "development",
              result.stderr)

        result = run(repo, "advance", "--phase", "gate")
        check("preserving path cannot enter gate", result.returncode != 0)

        run(repo, "advance", "--phase", "pr")
        result = run(repo, "complete")
        check("complete without evidence fails", result.returncode != 0)

        result = run(repo, "complete", "--evidence", "tests pass; review approved")
        check("complete with evidence succeeds", result.returncode == 0, result.stderr)
        check("status is completed", state(repo)["status"] == "completed")


def test_contract_changing_path() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo(tmp)
        run(repo, "start", "--task", "t2", "--title", "test")
        run(
            repo, "classify", "--kind", "contract-changing",
            "--reason", "changes interface", "--decided-by", "agent",
        )
        check("changing classify -> specification", state(repo)["phase"] == "specification")

        result = run(repo, "advance", "--phase", "development")
        check("cannot skip to development", result.returncode != 0)

        run(repo, "advance", "--phase", "confirmation")
        run(repo, "advance", "--phase", "gate")

        run(repo, "discover", "--summary", "found a problem")
        result = run(repo, "gate-pass", "--evidence", "docs/design/1.md")
        check("gate-pass blocks on unresolved discovery", result.returncode != 0)

        run(repo, "resolve-discovery", "--discovery", "D001", "--note", "fixed here")
        result = run(repo, "gate-pass", "--evidence", "decision log in issue")
        check("gate-pass advances to development", state(repo)["phase"] == "development",
              result.stderr)

        result = run(repo, "advance", "--phase", "development")
        check("repeated advance to development is idempotent", result.returncode == 0)

        run(repo, "advance", "--phase", "pr")
        result = run(repo, "complete")
        check("changing task cannot complete from pr", result.returncode != 0)

        run(repo, "advance", "--phase", "retrospective")
        path = write_retrospective(repo)
        result = run(repo, "reflect", "--path", path, "--harness-impact", "none")
        check("reflect records retrospective", result.returncode == 0, result.stderr)
        result = run(repo, "complete")
        check("changing task completes after reflect", result.returncode == 0, result.stderr)


def test_reflect_requires_headings() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo(tmp)
        run(repo, "start", "--task", "t3", "--title", "test")
        run(
            repo, "classify", "--kind", "contract-changing",
            "--reason", "changes interface", "--decided-by", "agent",
        )
        run(repo, "advance", "--phase", "confirmation")
        run(repo, "advance", "--phase", "gate")
        run(repo, "gate-pass", "--evidence", "issue")
        run(repo, "advance", "--phase", "pr")
        run(repo, "advance", "--phase", "retrospective")
        partial = repo / "retro.md"
        partial.write_text("# Retro\n\n## Evidence\n", encoding="utf-8")
        result = run(repo, "reflect", "--path", "retro.md", "--harness-impact", "none")
        check("reflect rejects missing headings", result.returncode != 0)
        check(
            "missing Rules Reviewed for Removal is named",
            "Rules Reviewed for Removal" in result.stderr,
            result.stderr,
        )


def test_escalate() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo(tmp)
        run(repo, "start", "--task", "t4", "--title", "test")
        run(
            repo, "classify", "--kind", "contract-preserving",
            "--reason", "fixed by issue", "--decided-by", "agent",
        )
        run(repo, "escalate", "--reason", "schema change discovered")
        current = state(repo)
        check("escalate returns to specification", current["phase"] == "specification")
        check(
            "escalate records contract-changing",
            current["classification"]["kind"] == "contract-changing",
        )
        check(
            "escalate keeps prior classification history",
            current["classification"]["history"][0]["kind"] == "contract-preserving",
        )


def test_wait_rules() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo(tmp)
        run(repo, "start", "--task", "t5", "--title", "test")
        result = run(repo, "wait-human", "--reason", "classification unclear")
        check("wait allowed during classification", result.returncode == 0, result.stderr)
        run(repo, "resume")
        run(
            repo, "classify", "--kind", "contract-preserving",
            "--reason", "fixed", "--decided-by", "human",
        )
        result = run(repo, "wait-human", "--reason", "should not work")
        check("preserving task cannot wait after classification", result.returncode != 0)


def hook_decision(repo: Path, event: str = "Stop", *, active: bool = False):
    return evaluate(str(repo), event, stop_hook_active=active)


def test_hook_core() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo(tmp)
        check("missing state is silent", hook_decision(repo).kind == "silent")

        run(repo, "start", "--task", "t6", "--title", "test")
        check("active classification blocks", hook_decision(repo).kind == "block")
        check(
            "second stop notifies instead of blocking",
            hook_decision(repo, active=True).kind == "notify",
        )
        check(
            "session start notifies",
            hook_decision(repo, "SessionStart").kind == "notify",
        )

        run(repo, "wait-human", "--reason", "question")
        check("human wait is silent", hook_decision(repo).kind == "silent")
        run(repo, "resume")

        run(
            repo, "classify", "--kind", "contract-changing",
            "--reason", "interface", "--decided-by", "agent",
        )
        run(repo, "wait-human", "--reason", "spec question")
        check("contract-changing wait is silent", hook_decision(repo).kind == "silent")
        run(repo, "resume")

        run(repo, "discover", "--summary", "problem")
        result = run(repo, "advance", "--phase", "confirmation")
        check("advance blocks on unresolved discovery", result.returncode != 0)
        decision = hook_decision(repo)
        check(
            "unresolved discovery blocks with its id",
            decision.kind == "block" and "D001" in decision.message,
            decision.message,
        )
        run(repo, "link-issue", "--discovery", "D001", "--issue", "#12")

        run(repo, "advance", "--phase", "confirmation")
        run(repo, "advance", "--phase", "gate")
        run(repo, "gate-fail", "--reason", "ambiguous rollout")
        check(
            "returned-to-confirmation gate is silent",
            hook_decision(repo).kind == "silent",
        )
        run(repo, "gate-pass", "--evidence", "issue decision log")
        run(repo, "advance", "--phase", "pr")
        run(repo, "advance", "--phase", "retrospective")
        decision = hook_decision(repo)
        check(
            "retrospective without record blocks",
            decision.kind == "block" and "retrospective" in decision.message.lower(),
        )
        path = write_retrospective(repo)
        run(repo, "reflect", "--path", path, "--harness-impact", "none")
        check("recorded retrospective is silent", hook_decision(repo).kind == "silent")

        run(repo, "complete")
        check("completed task is silent", hook_decision(repo).kind == "silent")

        # A nested receipt must fail closed, not win.
        nested = repo / "sub" / ".kaizen"
        nested.mkdir(parents=True)
        (nested / "task-cycle.json").write_text("{}", encoding="utf-8")
        decision = evaluate(str(repo / "sub"), "Stop", stop_hook_active=False)
        check("ambiguous receipts block", decision.kind == "block", decision.message)

        # An unreadable receipt must fail closed.
        (nested / "task-cycle.json").write_text("not json", encoding="utf-8")
        (repo / ".kaizen" / "task-cycle.json").unlink()
        decision = evaluate(str(repo / "sub"), "Stop", stop_hook_active=False)
        check("unreadable receipt blocks", decision.kind == "block", decision.message)


def main() -> int:
    test_contract_preserving_path()
    test_contract_changing_path()
    test_reflect_requires_headings()
    test_escalate()
    test_wait_rules()
    test_hook_core()
    if FAILURES:
        print(f"\n{len(FAILURES)} failing checks: {', '.join(FAILURES)}")
        return 1
    print("\nall checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
