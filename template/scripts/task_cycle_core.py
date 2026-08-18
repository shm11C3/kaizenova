#!/usr/bin/env python3
"""Provider-neutral decision core for the task-cycle contract.

Both the Codex and Claude lifecycle hook adapters import this module so the
task-cycle enforcement logic has a single source of truth. Adapters own only
the provider-specific stdin parsing and stdout contract; all workflow decisions
live here.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

DecisionKind = Literal["silent", "notify", "block"]

STATE_RELATIVE_PATH = Path(".kaizenova") / "task-cycle.json"

# Adapters repeat this tuple because they must check the interpreter before
# importing this module: a future syntax bump here would turn the import itself
# into a SyntaxError, and the check would never run.
MINIMUM_PYTHON = (3, 11)

# The headings a retrospective must contain. scripts/task_cycle.py validates a
# recorded retrospective against this list, so it lives here once.
RETROSPECTIVE_HEADINGS = (
    "## Evidence",
    "## Friction, Failures, and Surprises",
    "## Discovered Issues",
    "## Lessons",
    "## Harness Changes Applied",
    "## Rules Reviewed for Removal",
)

ACTIVE_PHASES = frozenset(
    {
        "classification",
        "specification",
        "confirmation",
        "gate",
        "development",
        "pr",
        "retrospective",
    }
)


@dataclass(frozen=True)
class Decision:
    """A provider-neutral hook decision.

    - ``silent``: no output; the turn or session continues untouched.
    - ``notify``: informational message; never blocks.
    - ``block``: the workflow is incomplete; the turn should not end yet.
    """

    kind: DecisionKind
    message: str = ""
    reason: str = ""


def find_state_paths(cwd: str) -> list[Path]:
    """Find every task-cycle state above a working directory, nearest first.

    The search walks from ``cwd`` towards the filesystem root. Sessions are
    expected to start at the repository root, but resolving from a subdirectory
    keeps enforcement from silently disappearing when they do not. ``.git``
    deliberately does not bound the search: a linked worktree stores ``.git``
    as a file, so depending on it would make the enforced range hinge on a
    file-versus-directory check.

    Every match is returned rather than the nearest one. Taking only the
    nearest would let a receipt written in a subdirectory override the
    repository's own and silence enforcement, so an ambiguous result must fail
    closed instead.
    """

    start = Path(cwd).resolve()
    found: list[Path] = []
    for directory in (start, *start.parents):
        candidate = directory / STATE_RELATIVE_PATH
        if candidate.exists():
            found.append(candidate)
    return found


def load_state(
    cwd: str,
) -> tuple[
    Literal["missing", "ambiguous", "unreadable", "ok"], dict[str, Any] | None, Path | None
]:
    """Load task-cycle state for a working directory.

    Returns a status, the parsed object, and the repository root the state was
    found in. ``missing`` means there is no active task cycle above this
    directory and hooks should stay silent.
    """

    state_paths = find_state_paths(cwd)
    if not state_paths:
        return "missing", None, None
    if len(state_paths) > 1:
        return "ambiguous", None, state_paths[0].parent.parent
    state_path = state_paths[0]
    root = state_path.parent.parent
    try:
        with state_path.open(encoding="utf-8") as stream:
            payload = json.load(stream)
    except (OSError, json.JSONDecodeError):
        return "unreadable", None, root
    if not isinstance(payload, dict):
        return "unreadable", None, root
    return "ok", payload, root


def is_contract_changing(state: dict[str, Any]) -> bool:
    classification = state.get("classification")
    return (
        isinstance(classification, dict)
        and classification.get("kind") == "contract-changing"
    )


def evaluate(cwd: str, event_name: str | None, *, stop_hook_active: bool) -> Decision:
    """Decide what a lifecycle hook should do for the current task-cycle state.

    This function is pure with respect to the filesystem except for reading the
    task-cycle state and checking whether a recorded retrospective file exists.
    The ordering of checks is deliberately preserved so Codex and Claude behave
    identically.
    """

    status, state, root = load_state(cwd)
    if status == "missing":
        return Decision("silent")
    if status == "ambiguous":
        paths = ", ".join(str(path) for path in find_state_paths(cwd))
        return Decision(
            "block",
            "More than one task-cycle state is visible from this directory: "
            f"{paths}. Remove the nested one; a nearer receipt must not decide "
            "whether the repository's task cycle is enforced.",
            "Ambiguous task-cycle state",
        )
    if status == "unreadable" or state is None or root is None:
        return Decision(
            "block",
            "Task-cycle state is unreadable. Fail closed before implementation or completion.",
            "Unreadable task-cycle state",
        )

    if state.get("status") == "completed":
        return Decision("silent")

    phase = state.get("phase", "unknown")
    task_id = state.get("taskId", "unknown")
    awaiting_human = state.get("awaitingHuman") is True
    returned_to_confirmation = state.get("stage") == "confirmation"

    if event_name == "SessionStart":
        return Decision(
            "notify",
            f"Active task {task_id} is in phase '{phase}'. "
            "Resume it with $execute-task-cycle and keep discoveries resolved "
            "in-task or linked to Issues.",
        )

    wait_is_valid = phase == "classification" or (
        is_contract_changing(state) and phase in ACTIVE_PHASES
    )
    if (awaiting_human and wait_is_valid) or (
        returned_to_confirmation and phase in {"classification", "confirmation", "gate"}
    ):
        return Decision("silent")

    if event_name == "Stop" and stop_hook_active:
        return Decision(
            "notify",
            f"Task {task_id} remains in phase '{phase}'. "
            "The task-cycle reminder already ran once; inspect the state before ending the turn.",
        )

    unresolved = [
        item
        for item in state.get("discoveries", [])
        if isinstance(item, dict)
        and not item.get("issue")
        and not item.get("resolvedInTask")
    ]
    if unresolved:
        labels = ", ".join(str(item.get("id", "unknown")) for item in unresolved)
        return Decision(
            "block",
            f"Task {task_id} has unresolved discoveries: {labels}. "
            "Decide whether each one belongs in this task's scope. Fix it here and "
            "record it with `resolve-discovery`, or link an Issue for deferred work.",
            "Discovered problems must be resolved or linked",
        )

    if phase == "retrospective":
        reflection = state.get("retrospective")
        if isinstance(reflection, str) and (root / reflection).is_file():
            return Decision("silent")
        return Decision(
            "block",
            f"Task {task_id} is awaiting its retrospective. "
            "Use $reflect-and-improve-harness, apply justified harness changes, "
            "run the rule-removal review, and record the retrospective path.",
            "Retrospective is required before task completion",
        )

    return Decision(
        "block",
        f"Task {task_id} is still active in phase '{phase}'. "
        "Continue the selected workflow or record an explicit human wait with "
        "`task_cycle.py wait-human`.",
        "Task workflow is incomplete",
    )


def parse_event(raw: str) -> tuple[dict[str, Any] | None, str | None]:
    """Parse a hook stdin payload.

    Returns ``(event, None)`` on success or ``(None, error_message)`` when the
    payload is not a JSON object, matching the fail-open reminder behavior both
    adapters use for malformed input.
    """

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as error:
        return None, f"invalid hook JSON: {error}"
    if not isinstance(payload, dict):
        return None, "hook payload must be a JSON object"
    return payload, None


def resolve_cwd(event: dict[str, Any]) -> str | None:
    value = event.get("cwd")
    if isinstance(value, str) and value:
        return value
    return None
