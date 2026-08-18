#!/usr/bin/env python3
"""Claude Code lifecycle hook adapter for the task-cycle contract.

This adapter owns only the Claude-specific stdin parsing and stdout contract.
All workflow decisions come from ``scripts/task_cycle_core.py`` so the Codex and
Claude adapters share one source of truth.

Claude hook output contract used here:

- Block the Stop event with ``{"decision": "block", "reason": ...}`` on stdout,
  exit 0. Claude then forces continuation and re-runs Stop with
  ``stop_hook_active`` true, which the core turns into a non-blocking reminder.
- Provide SessionStart context with
  ``{"hookSpecificOutput": {"hookEventName": "SessionStart",
  "additionalContext": ...}}``.
- Exit 0 with no output to allow the event to proceed untouched.

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


def session_start_context(message: str) -> str:
    return json.dumps(
        {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": message,
            }
        },
        ensure_ascii=False,
    )


def report_unsupported_interpreter() -> int:
    """Block rather than crash. A crashed hook would fail open."""

    event_name = None
    try:
        payload = json.loads(sys.stdin.read())
        if isinstance(payload, dict):
            event_name = payload.get("hook_event_name")
    except (json.JSONDecodeError, OSError):
        pass
    running = "%d.%d" % (sys.version_info[0], sys.version_info[1])
    required = "%d.%d" % (MINIMUM_PYTHON[0], MINIMUM_PYTHON[1])
    message = (
        "Task-cycle hook needs Python " + required + " or newer but ran on "
        + running + ". Task-cycle enforcement is unreliable until the interpreter "
        "used by .claude/settings.json is fixed."
    )
    if event_name == "SessionStart":
        print(session_start_context(message))
    else:
        print(json.dumps({"decision": "block", "reason": message}, ensure_ascii=False))
    return 0


if sys.version_info < MINIMUM_PYTHON:
    raise SystemExit(report_unsupported_interpreter())

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from task_cycle_core import evaluate, parse_event, resolve_cwd  # noqa: E402


def main() -> int:
    event, error = parse_event(sys.stdin.read())
    if error is not None or event is None:
        # Fail open with a visible warning, mirroring the Codex adapter.
        print(f"Task-cycle hook rejected its input: {error}", file=sys.stderr)
        return 0

    cwd_value = resolve_cwd(event)
    if cwd_value is None:
        print("Task-cycle hook received no usable cwd.", file=sys.stderr)
        return 0

    event_name = event.get("hook_event_name")
    decision = evaluate(
        cwd_value,
        event_name,
        stop_hook_active=event.get("stop_hook_active") is True,
    )

    if decision.kind == "silent":
        return 0

    if decision.kind == "notify":
        if event_name == "SessionStart":
            print(session_start_context(decision.message))
        else:
            # Non-blocking reminder; Claude Stop has no message channel unless it
            # blocks, so surface it on stderr without stopping the turn.
            print(decision.message, file=sys.stderr)
        return 0

    # decision.kind == "block"
    if event_name == "SessionStart":
        # SessionStart cannot block a session; degrade to added context.
        print(session_start_context(decision.message))
        return 0

    print(json.dumps({"decision": "block", "reason": decision.message}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
