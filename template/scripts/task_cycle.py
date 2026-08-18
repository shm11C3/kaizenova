#!/usr/bin/env python3
"""Manage the local state for one implementation task cycle."""

from __future__ import annotations

import argparse
import fcntl
import json
import re
import subprocess
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from task_cycle_core import RETROSPECTIVE_HEADINGS

PHASES = (
    "specification",
    "confirmation",
    "gate",
    "development",
    "pr",
    "retrospective",
    "completed",
)


def now() -> str:
    return datetime.now(UTC).isoformat()


def repo_root() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=True,
        capture_output=True,
        text=True,
    )
    # Resolved so later relative_to comparisons cannot fail on a symlinked path.
    return Path(result.stdout.strip()).resolve()


def state_path(root: Path) -> Path:
    return root / ".kaizenova" / "task-cycle.json"


@contextmanager
def task_cycle_lock(root: Path) -> Iterator[None]:
    """Serialize every receipt mutation within one repository."""

    directory = state_path(root).parent
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / "task-cycle.lock").open("a", encoding="utf-8") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def load_state(root: Path) -> dict[str, Any]:
    path = state_path(root)
    if not path.exists():
        raise SystemExit("No active task cycle. Run `task_cycle.py start` first.")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        # Recovering from a corrupt receipt is exactly when a readable error
        # matters, so do not let the decoder traceback reach the human.
        raise SystemExit(f"Cannot read {path}: {error}") from error
    if not isinstance(value, dict):
        raise SystemExit(f"{path} must contain a JSON object.")
    return value


def save_state(root: Path, state: dict[str, Any]) -> None:
    path = state_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    state["updatedAt"] = now()
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def require_phase(state: dict[str, Any], phase: str) -> None:
    if state.get("phase") != phase:
        raise SystemExit(f"Expected phase '{phase}', found '{state.get('phase')}'.")


def classification_kind(state: dict[str, Any]) -> str | None:
    classification = state.get("classification")
    if isinstance(classification, dict):
        kind = classification.get("kind")
        if isinstance(kind, str):
            return kind
    return None


def archive_state(root: Path, state: dict[str, Any]) -> Path:
    """Keep the previous task's receipt, which `.kaizenova/` alone would overwrite."""

    history = state_path(root).parent / "history"
    history.mkdir(parents=True, exist_ok=True)
    stamp = str(state.get("completedAt") or state.get("updatedAt") or now())
    safe_stamp = re.sub(r"[^0-9A-Za-z]+", "-", stamp)
    safe_task = re.sub(r"[^0-9A-Za-z._-]+", "-", str(state.get("taskId", "unknown")))
    archived = history / f"{safe_task}-{safe_stamp}.json"
    archived.write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return archived


def cmd_start(args: argparse.Namespace, root: Path) -> None:
    path = state_path(root)
    if path.exists():
        existing = load_state(root)
        if existing.get("status") != "completed":
            raise SystemExit(
                f"Task {existing.get('taskId')} is already active in phase {existing.get('phase')}."
            )
        archived = archive_state(root, existing)
        print(f"Archived previous task receipt: {archived.relative_to(root)}")
    state = {
        "version": 1,
        "taskId": args.task,
        "title": args.title,
        "issue": args.issue,
        "status": "active",
        "phase": "classification",
        "classification": None,
        "awaitingHuman": False,
        "gate": {"passed": False, "evidence": None},
        "discoveries": [],
        "retrospective": None,
        "startedAt": now(),
    }
    save_state(root, state)
    print(json.dumps(state, ensure_ascii=False, indent=2))


def cmd_status(_: argparse.Namespace, root: Path) -> None:
    print(json.dumps(load_state(root), ensure_ascii=False, indent=2))


def cmd_classify(args: argparse.Namespace, root: Path) -> None:
    state = load_state(root)
    require_phase(state, "classification")
    reason = args.reason.strip()
    if not reason:
        raise SystemExit("--reason must explain the task's contract impact.")
    state["classification"] = {
        "kind": args.kind,
        "reason": reason,
        "decidedBy": args.decided_by,
        "decidedAt": now(),
        "history": [],
    }
    next_phase = (
        "development" if args.kind == "contract-preserving" else "specification"
    )
    state["phase"] = next_phase
    state["awaitingHuman"] = False
    state.pop("waitReason", None)
    save_state(root, state)
    print(f"Classified task as {args.kind}; advanced to {next_phase}")


def cmd_escalate(args: argparse.Namespace, root: Path) -> None:
    state = load_state(root)
    if state.get("phase") not in {"development", "pr"}:
        raise SystemExit(
            "A contract-preserving task can escalate only during development or pr."
        )
    if classification_kind(state) != "contract-preserving":
        raise SystemExit("Only a contract-preserving task can escalate.")
    reason = args.reason.strip()
    if not reason:
        raise SystemExit("--reason must explain the discovered contract change.")
    classification = state["classification"]
    prior = {key: value for key, value in classification.items() if key != "history"}
    history = list(classification.get("history") or [])
    history.append(prior)
    state["classification"] = {
        "kind": "contract-changing",
        "reason": reason,
        "decidedBy": "agent",
        "decidedAt": now(),
        "history": history,
    }
    state["phase"] = "specification"
    state["awaitingHuman"] = False
    state.pop("waitReason", None)
    save_state(root, state)
    print("Escalated task to contract-changing; returned to specification")


def cmd_advance(args: argparse.Namespace, root: Path) -> None:
    state = load_state(root)
    current = state.get("phase")
    target = args.phase
    if (
        current == target == "development"
        and (state.get("gate") or {}).get("passed") is True
    ):
        # Idempotent compatibility: gate-pass already advanced the receipt.
        print("Task is already in development")
        return
    if current not in PHASES:
        raise SystemExit(f"Unknown phase: {current}")
    if classification_kind(state) == "contract-preserving":
        next_phase = {"development": "pr"}.get(str(current))
        if target != next_phase:
            raise SystemExit(
                f"The abbreviated workflow cannot advance {current} -> {target}."
            )
    if PHASES.index(target) != PHASES.index(current) + 1:
        raise SystemExit(f"Phase must advance one step: {current} -> {target}")
    if target == "development":
        if classification_kind(state) != "contract-changing":
            raise SystemExit(
                "The full workflow requires a contract-changing classification."
            )
        if not (state.get("gate") or {}).get("passed"):
            raise SystemExit(
                "The understanding gate must pass before development "
                "for a contract-changing task. Use `gate-pass`."
            )
    if unresolved_discoveries(state):
        raise SystemExit(
            "Every discovery must be resolved in this task with `resolve-discovery` "
            "or linked to an Issue before advancing."
        )
    state["phase"] = target
    state["awaitingHuman"] = False
    save_state(root, state)
    print(f"Advanced {current} -> {target}")


def cmd_wait(args: argparse.Namespace, root: Path) -> None:
    state = load_state(root)
    phase = state.get("phase")
    changing = classification_kind(state) == "contract-changing"
    if phase != "classification" and not (changing and phase in PHASES[:-1]):
        raise SystemExit(
            "Human wait is valid during classification or any active phase of a "
            "contract-changing task."
        )
    state["awaitingHuman"] = True
    state["waitReason"] = args.reason
    save_state(root, state)
    print(f"Waiting for human: {args.reason}")


def cmd_resume(_: argparse.Namespace, root: Path) -> None:
    state = load_state(root)
    state["awaitingHuman"] = False
    state.pop("waitReason", None)
    save_state(root, state)
    print("Task resumed")


def cmd_gate_pass(args: argparse.Namespace, root: Path) -> None:
    """Record that the gate passed and advance atomically to development.

    The gate exists to keep the developer's intent reflected in the codebase and
    to reduce understanding and intent debt. It is not an audit, so this command
    does not collect proof of who approved the work. `--evidence` points at the
    document holding the decisions and their reasons; that document, not this
    state file, is what a future reader needs.

    Pass and transition are one command: keeping them as separate successful
    commands allowed implementation to start against a stale gate receipt.
    """

    state = load_state(root)
    require_phase(state, "gate")
    if classification_kind(state) != "contract-changing":
        raise SystemExit(
            "The understanding gate requires a contract-changing classification."
        )

    evidence = args.evidence.strip()
    if not evidence:
        raise SystemExit("--evidence must point at the recorded decisions and reasons.")
    if unresolved_discoveries(state):
        raise SystemExit(
            "Every discovery must be resolved in this task with `resolve-discovery` "
            "or linked to an Issue before the understanding gate can pass."
        )

    decision_log: str | None = None
    if args.decision_log:
        document = (root / args.decision_log).resolve()
        try:
            document.relative_to(root)
        except ValueError as error:
            raise SystemExit("The decision log must be inside the repository.") from error
        if not document.is_file():
            raise SystemExit(f"Decision log does not exist: {document}")
        decision_log = str(document.relative_to(root))

    gate = dict(state.get("gate") or {})
    gate.update(
        {
            "passed": True,
            "evidence": evidence,
            "decisionLog": decision_log,
            "passedAt": now(),
        }
    )
    state["gate"] = gate
    state["awaitingHuman"] = False
    state.pop("waitReason", None)
    state.pop("stage", None)
    state["phase"] = "development"
    save_state(root, state)
    print("Understanding gate passed; advanced gate -> development")


def cmd_gate_fail(args: argparse.Namespace, root: Path) -> None:
    """Record a failed gate attempt and return to confirmation.

    A failed gate signals that the specification is ambiguous, not that the
    human is at fault. The phase sequence stays monotonic; `stage` records that
    the task is back in confirmation so the reason survives for the PR and the
    retrospective.
    """

    state = load_state(root)
    require_phase(state, "gate")
    gate = dict(state.get("gate") or {})
    gate["passed"] = False
    attempts = list(gate.get("attempts") or [])
    attempts.append({"failedAt": now(), "reason": args.reason})
    gate["attempts"] = attempts
    state["gate"] = gate
    state["stage"] = "confirmation"
    save_state(root, state)
    print(f"Recorded gate attempt {len(attempts)}; returned to confirmation")


def cmd_discover(args: argparse.Namespace, root: Path) -> None:
    state = load_state(root)
    discovery_id = f"D{len(state.get('discoveries', [])) + 1:03d}"
    state.setdefault("discoveries", []).append(
        {
            "id": discovery_id,
            "summary": args.summary,
            "blocking": args.blocking,
            "issue": None,
            "discoveredAt": now(),
        }
    )
    save_state(root, state)
    print(discovery_id)


def find_discovery(state: dict[str, Any], discovery_id: str) -> dict[str, Any]:
    for discovery in state.get("discoveries", []):
        if discovery.get("id") == discovery_id:
            return discovery
    raise SystemExit(f"Unknown discovery: {discovery_id}")


def unresolved_discoveries(state: dict[str, Any]) -> list[dict[str, Any]]:
    """Discoveries that are neither fixed in this task nor linked to an Issue."""

    return [
        item
        for item in state.get("discoveries", [])
        if not item.get("issue") and not item.get("resolvedInTask")
    ]


def cmd_resolve_discovery(args: argparse.Namespace, root: Path) -> None:
    """Record that a discovery was fixed in this task rather than deferred.

    An Issue is for deferred work only. Without this command, a problem being
    fixed in the same PR would still need an Issue to track work already done.
    """

    state = load_state(root)
    note = args.note.strip()
    if not note:
        raise SystemExit("--note must say how the discovery was resolved in this task.")
    discovery = find_discovery(state, args.discovery)
    discovery["resolvedInTask"] = True
    discovery["resolution"] = note
    discovery["resolvedAt"] = now()
    save_state(root, state)
    print(f"Resolved {args.discovery} in this task")


def cmd_link_issue(args: argparse.Namespace, root: Path) -> None:
    state = load_state(root)
    if not re.match(r"^(https?://\S+|#\d+)$", args.issue):
        raise SystemExit("Issue must be a tracker URL or #number.")
    discovery = find_discovery(state, args.discovery)
    discovery["issue"] = args.issue
    discovery["issueLinkedAt"] = now()
    save_state(root, state)
    print(f"Linked {args.discovery} -> {args.issue}")


def cmd_reflect(args: argparse.Namespace, root: Path) -> None:
    state = load_state(root)
    require_phase(state, "retrospective")
    reflection = (root / args.path).resolve()
    try:
        reflection.relative_to(root)
    except ValueError as error:
        raise SystemExit("Retrospective must be inside the repository.") from error
    if not reflection.is_file():
        raise SystemExit(f"Retrospective does not exist: {reflection}")
    text = reflection.read_text(encoding="utf-8")
    missing = [heading for heading in RETROSPECTIVE_HEADINGS if heading not in text]
    if missing:
        raise SystemExit(f"Retrospective is missing headings: {', '.join(missing)}")
    state["retrospective"] = str(reflection.relative_to(root))
    state["harnessImpact"] = args.harness_impact
    save_state(root, state)
    print(f"Recorded retrospective: {state['retrospective']}")


def mark_completed(root: Path, state: dict[str, Any]) -> None:
    state["phase"] = "completed"
    state["status"] = "completed"
    state["completedAt"] = now()
    state["awaitingHuman"] = False
    save_state(root, state)
    print(f"Completed task {state.get('taskId')}")


def cmd_complete(args: argparse.Namespace, root: Path) -> None:
    state = load_state(root)
    if classification_kind(state) == "contract-preserving":
        require_phase(state, "pr")
        if unresolved_discoveries(state):
            raise SystemExit(
                "Every discovery must be resolved in this task or linked to an Issue."
            )
        evidence = (args.evidence or "").strip()
        if not evidence:
            raise SystemExit(
                "--evidence must record validation, review replies, and review status."
            )
        state["completionEvidence"] = evidence
        mark_completed(root, state)
        return

    require_phase(state, "retrospective")
    if unresolved_discoveries(state):
        raise SystemExit(
            "Every discovery must be resolved in this task or linked to an Issue."
        )
    reflection = state.get("retrospective")
    if not isinstance(reflection, str) or not (root / reflection).is_file():
        raise SystemExit("Record a valid retrospective before completing the task.")
    mark_completed(root, state)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    commands = result.add_subparsers(dest="command", required=True)

    start = commands.add_parser("start")
    start.add_argument("--task", required=True)
    start.add_argument("--title", required=True)
    start.add_argument("--issue")
    start.set_defaults(handler=cmd_start)

    status = commands.add_parser("status")
    status.set_defaults(handler=cmd_status)

    classify = commands.add_parser("classify")
    classify.add_argument(
        "--kind",
        required=True,
        choices=("contract-preserving", "contract-changing"),
    )
    classify.add_argument("--reason", required=True)
    classify.add_argument(
        "--decided-by",
        required=True,
        choices=("agent", "human"),
    )
    classify.set_defaults(handler=cmd_classify)

    escalate = commands.add_parser("escalate")
    escalate.add_argument("--reason", required=True)
    escalate.set_defaults(handler=cmd_escalate)

    advance = commands.add_parser("advance")
    advance.add_argument("--phase", required=True, choices=PHASES[1:-1])
    advance.set_defaults(handler=cmd_advance)

    wait = commands.add_parser("wait-human")
    wait.add_argument("--reason", required=True)
    wait.set_defaults(handler=cmd_wait)

    resume = commands.add_parser("resume")
    resume.set_defaults(handler=cmd_resume)

    gate = commands.add_parser("gate-pass")
    gate.add_argument(
        "--evidence",
        required=True,
        help="Where the decisions and their reasons are recorded.",
    )
    gate.add_argument(
        "--decision-log",
        help="Optional repo-relative path to the document holding the decision log.",
    )
    gate.set_defaults(handler=cmd_gate_pass)

    gate_fail = commands.add_parser("gate-fail")
    gate_fail.add_argument(
        "--reason",
        required=True,
        help="What was misunderstood or ambiguous, so the specification can be fixed.",
    )
    gate_fail.set_defaults(handler=cmd_gate_fail)

    discover = commands.add_parser("discover")
    discover.add_argument("--summary", required=True)
    discover.add_argument("--blocking", action="store_true")
    discover.set_defaults(handler=cmd_discover)

    resolve = commands.add_parser("resolve-discovery")
    resolve.add_argument("--discovery", required=True)
    resolve.add_argument(
        "--note",
        required=True,
        help="How the discovery was resolved in this task.",
    )
    resolve.set_defaults(handler=cmd_resolve_discovery)

    link = commands.add_parser("link-issue")
    link.add_argument("--discovery", required=True)
    link.add_argument("--issue", required=True)
    link.set_defaults(handler=cmd_link_issue)

    reflect = commands.add_parser("reflect")
    reflect.add_argument("--path", required=True)
    reflect.add_argument(
        "--harness-impact",
        required=True,
        choices=("applied", "issue-filed", "none"),
    )
    reflect.set_defaults(handler=cmd_reflect)

    complete = commands.add_parser("complete")
    complete.add_argument(
        "--evidence",
        help="Validation and review evidence for a contract-preserving task.",
    )
    complete.set_defaults(handler=cmd_complete)
    return result


def main() -> int:
    args = parser().parse_args()
    root = repo_root()
    if args.command == "status":
        args.handler(args, root)
    else:
        with task_cycle_lock(root):
            args.handler(args, root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
