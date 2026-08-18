# kaizenova

English | [日本語](README.ja.md)

[![Tests](https://img.shields.io/github/actions/workflow/status/shm11C3/kaizenova/test.yml?style=flat-square&label=tests)](https://github.com/shm11C3/kaizenova/actions/workflows/test.yml)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Dependencies](https://img.shields.io/badge/dependencies-none-brightgreen.svg?style=flat-square)](#)
[![Agents](https://img.shields.io/badge/agents-Claude%20Code%20%7C%20Codex-D97757.svg?style=flat-square)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](LICENSE)

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

### Requirements

- a git repository to install into (the installer writes to the repository root);
- Python 3.11 or newer, available as `python3` (check with `python3 --version`);
- Claude Code and/or Codex — hooks are installed for both, and each provider
  ignores the other's files.

No third-party packages are needed; the harness uses the standard library only.

### 1. Get kaizenova

kaizenova is not published as a package. Clone it once, anywhere outside the
repository you want to install into, and run its installer from there.

```bash
git clone https://github.com/shm11C3/kaizenova.git
```

### 2. Run the installer

```bash
python3 kaizenova/install.py /path/to/your/repo
```

The target path must be the **root** of a git repository. The installer copies
`template/` into it and **never overwrites an existing file** — anything
already present is reported as "left in place" so you can merge it by hand.
That also makes re-running the installer the supported way to upgrade: run it
again, then review the reported conflicts.

What lands in your repository:

| Path | What it is |
|---|---|
| `AGENTS.md`, `CLAUDE.md` | Agent guidance, with `EDIT ME` placeholders to fill in |
| `.agents/skills/` | The four canonical skills |
| `.claude/`, `.codex/` | Hook adapters, permissions, and approval rules |
| `scripts/` | The state-machine CLI and the shared hook decision core |
| `docs/agents/` | Enforcement reference, understanding ledger, retrospective template |

### 3. Fill in `AGENTS.md`

Open `AGENTS.md` and replace every `EDIT ME` placeholder, deleting the comment
around it once done:

- **mission** — what the project is, and what outcome justifies the work;
- **sources of truth** — the documents that fix outcomes, invariants, and
  design; the workflow reads this list;
- **project validation stage** — optional. Declare it if the project needs an
  extra validation step after PR review, otherwise delete the section;
- **language rule** — which language human-facing documents (Issues, PRs,
  retrospectives) use, versus code and agent guidance.

### 4. Commit the installed files

Commit everything the installer added. The hooks and skills only take effect
once they are part of the repository.

### Notes for Windows

kaizenova runs on macOS, Linux, and Windows. On native Windows two things
differ:

- if `python3` is not on `PATH`, point the hook commands in
  `.claude/settings.json` and `.codex/hooks.json` at your Python launcher
  (typically `py -3`);
- where symlinks are unavailable, the `.claude/skills` entries are copies
  instead of links to `.agents/skills`, so they do not pick up later edits on
  their own. The installer prints how to refresh them.

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
[docs/DESIGN.md](docs/DESIGN.md); individual decisions — distribution model,
language choice, what was excluded and what would reopen it — are recorded as
ADRs in [docs/adr/](docs/adr/).

## Development

```bash
python3 tests/check_task_cycle.py
```

## Acknowledgements

The confirmation interview's decision-tree questioning borrows its spirit from
mattpock's `grill-me` skill. kaizenova deliberately narrows it: instead of
grilling a plan exhaustively, the interview focuses on the decisions that
change the implementation contract or need the owner's agreement.

## License

[MIT](LICENSE)
