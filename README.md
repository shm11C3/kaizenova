# kaizenova

A portable task-execution loop for AI coding agents, enforced by machine, not
by prose. It targets the two debts that agent-driven development quietly
accumulates:

- **process debt** — the agent skips confirmation, testing, review replies, or
  the retrospective when nothing stops it from ending the turn; and
- **cognitive and intent debt** — the human stops understanding the code the
  agent writes, and the codebase stops reflecting anyone's intent.

kaizenova installs a small state machine, lifecycle hooks for **Claude Code**
and **Codex**, and four canonical skills into your repository. The hooks block
a turn from ending while the task cycle is incomplete; the skills define what
"complete" means.

## The loop

Every task is classified before any implementation:

- **contract-preserving** — the result is already fixed by the request or an
  existing source of truth, and nothing observable changes. Abbreviated path:
  `classification → development → pr → completed`.
- **contract-changing** — anything else. Full path:
  `classification → specification → confirmation → gate → development → pr →
  retrospective → completed`.

Key properties:

- **Human confirmation and an understanding gate** stand between specification
  and implementation of every contract-changing task. The confirmation
  interview targets only the decisions that change the contract or need the
  owner's agreement; the gate verifies *connected* understanding — a system
  sketch and a cross-component trace scenario — not the ability to look an
  answer up in a document.
- **An understanding ledger** carries demonstrated understanding across tasks:
  the gate credits what the human has already shown instead of re-asking it,
  and a task that changes a contract marks the dependent entries stale so the
  next gate re-verifies exactly those. The gate measures the accumulated
  shared model and its decay, not a per-task snapshot.
- **Discoveries** (anything affecting acceptance, safety, correctness, or
  scope) must be resolved in-task or linked to an Issue; the hooks and the CLI
  both refuse to advance past an unresolved one.
- **TDD is required** on the full path, with red-green evidence kept.
- **The retrospective subtracts as well as adds.** Every new rule records the
  evidence that triggered it and its removal condition, and every
  retrospective must review existing rules for removal. Harnesses that only
  add rules become overengineered; this one is built to shrink.
- **Hooks fail closed.** An unreadable or ambiguous state receipt blocks
  instead of silently disabling enforcement.

## Install

Requirements: a git repository, Python 3.11+, and Claude Code and/or Codex.

```bash
python3 install.py /path/to/your/repo
```

The installer copies the template into your repository and never overwrites
existing files. Then:

1. Edit `AGENTS.md` — fill in every `EDIT ME` placeholder: mission, sources of
   truth, the optional project validation stage, and your language rule.
2. Commit the installed files.

## Usage

```bash
python3 scripts/task_cycle.py start --task my-task --title "Add rate limiting"
```

Then ask your agent to work on the task; the `$execute-task-cycle` skill picks
the path from there. The state receipt lives in `.kaizenova/task-cycle.json`;
`python3 scripts/task_cycle.py status` shows it. Hook behavior, and which
parts of it are fixed versus tunable, is documented in
`docs/agents/ENFORCEMENT.md` after installation.

## What's in the template

| Piece | Purpose |
|---|---|
| `.agents/skills/execute-task-cycle` | Canonical task procedure: classification, both paths, TDD, discoveries, PR rules |
| `.agents/skills/gate-shared-understanding` | The understanding gate, designed to test synthesis rather than retrieval |
| `.agents/skills/reflect-and-improve-harness` | Retrospective with mandatory rule-removal review |
| `.agents/skills/review-design-complexity` | Overengineering audit: essential / accidental / speculative / validation-gap |
| `scripts/task_cycle.py`, `scripts/task_cycle_core.py` | State machine CLI and the provider-neutral hook decision core |
| `.claude/`, `.codex/` | Hook adapters, permissions, and approval rules for both providers |
| `scripts/find_relevant_lessons.py` | Bounded, deterministic retrieval over recorded lessons and retrospectives |
| `docs/agents/` | Enforcement reference, understanding ledger, retrospective template, lessons directory |

Claude Code and Codex share one decision core; the adapters own only their
provider's I/O contract, so the two can never diverge on workflow decisions.

## Deliberately not included

No QA phase (declare a project validation stage in `AGENTS.md` if you need
one), no multi-agent delegation tracking, no PR-size metering, no state-file
versioning or migration machinery. The reasoning, including the
overengineering failure modes this design guards against, is in
[docs/DESIGN.md](docs/DESIGN.md).

## Development

```bash
python3 tests/check_task_cycle.py
```

## Acknowledgements

The confirmation interview's decision-tree questioning borrows its spirit from
mattpock's `grill-me` skill. kaizenova deliberately narrows it: instead of
grilling a plan exhaustively, the interview focuses on the decisions that
change the implementation contract or need the owner's agreement.

日本語のREADMEは [README.ja.md](README.ja.md) にあります。
