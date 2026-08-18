#!/usr/bin/env python3
"""Codex lifecycle hook adapter for the task-cycle contract.

This adapter owns only the Codex-specific stdin parsing and stdout contract.
All workflow decisions come from ``scripts/task_cycle_core.py`` so the Codex and
Claude adapters can never diverge.

Keep this file parseable by older interpreters. The version guard below runs
before the shared core is imported, so this module must not use syntax that a
too-old interpreter would reject while parsing.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Duplicated from scripts/task_cycle_core.py on purpose: importing the core to
# read it would already have failed on a too-old interpreter.
MINIMUM_PYTHON = (3, 11)


def emit(message: str, *, should_continue: bool = True, reason: str = "") -> None:
    payload: dict[str, object] = {"continue": should_continue, "systemMessage": message}
    if reason:
        payload["stopReason"] = reason
    print(json.dumps(payload, ensure_ascii=False))


def report_unsupported_interpreter() -> int:
    """Block rather than crash. A crashed hook would fail open."""

    try:
        sys.stdin.read()
    except OSError:
        pass
    running = "%d.%d" % (sys.version_info[0], sys.version_info[1])
    required = "%d.%d" % (MINIMUM_PYTHON[0], MINIMUM_PYTHON[1])
    emit(
        "Task-cycle hook needs Python " + required + " or newer but ran on "
        + running + ". Task-cycle enforcement is unreliable until the interpreter "
        "used by .codex/hooks.json is fixed.",
        should_continue=False,
        reason="Unsupported Python interpreter",
    )
    return 0


if sys.version_info < MINIMUM_PYTHON:
    raise SystemExit(report_unsupported_interpreter())

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from task_cycle_core import evaluate, parse_event, resolve_cwd  # noqa: E402


def main() -> int:
    event, error = parse_event(sys.stdin.read())
    if error is not None or event is None:
        emit(f"Task-cycle hook rejected its input: {error}")
        return 0

    cwd_value = resolve_cwd(event)
    if cwd_value is None:
        emit("Task-cycle hook received no usable cwd.")
        return 0

    decision = evaluate(
        cwd_value,
        event.get("hook_event_name"),
        stop_hook_active=event.get("stop_hook_active") is True,
    )

    if decision.kind == "silent":
        return 0
    if decision.kind == "notify":
        emit(decision.message)
        return 0
    emit(decision.message, should_continue=False, reason=decision.reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
