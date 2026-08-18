# Harness Enforcement Rules

How the lifecycle hooks behave when they cannot confirm the state of a task
cycle. The hooks enforce the development workflow only; they are not a product
safety gate, and nothing here may be cited to relax one.

## Hook Behavior

| Condition | Behavior | Class |
|---|---|---|
| Task-cycle state is unreadable | block | Fixed |
| Interpreter is older than `MINIMUM_PYTHON` | block | Fixed |
| No task-cycle state above the working directory | silent | Fixed |
| More than one task-cycle state is visible | block | Fixed |
| Task is `completed` | silent | Fixed |
| A discovery is neither resolved with `resolve-discovery` nor linked to an Issue | block | Fixed |
| Phase is `retrospective` with no recorded retrospective | block | Fixed |
| Any other unfinished phase at the end of a turn | block | Tunable |
| Explicit human wait during `classification`, or during any active phase of a `contract-changing` task | silent | Fixed |
| `stage` is `confirmation` after a failed gate | silent | Tunable |
| `SessionStart` | never blocks | Fixed |

**Fixed** means the behavior may only change with a recorded decision
explaining why the harness can still be trusted without it.
**Tunable** means the behavior is an ergonomics choice and may be adjusted
from task evidence through the retrospective loop.

## Why These Are Fixed

- **Unreadable state blocks.** An unreadable receipt is not an absent one.
  Treating it as absent would silently disable every other check.
- **An old interpreter blocks.** The decision core is shared; if it cannot be
  trusted to run, no hook output can be trusted either. A crashing hook fails
  open, so the adapters check the interpreter before importing the core and
  block deliberately instead.
- **More than one visible state blocks.** Nothing entitles a nearer receipt to
  decide whether the repository's task cycle is enforced.
- **Missing state stays silent.** A repository with no task cycle is a normal
  state, not an unknown one.
- **`SessionStart` never blocks.** A session that cannot start cannot be
  repaired from inside itself.

## State Resolution

The search walks from the working directory towards the filesystem root
looking for `.kaizen/task-cycle.json`. One match is used; more than one
blocks. `.git` deliberately does not bound the search: a linked worktree
stores `.git` as a file, so bounding on it would make the enforced range
depend on a file-versus-directory check.

## Workflow Selection

Receipts start in `classification`. Ending a turn with an unresolved
classification is blocked like any other incomplete phase; an explicit human
wait may be recorded there when the agent cannot determine the contract
impact.

`contract-preserving` uses the abbreviated `development`, `pr`, `completed`
path. The CLI rejects completion from `pr` without validation and review
evidence. `contract-changing` uses the full path and cannot skip the
understanding gate: `gate-pass` rejects unresolved discoveries and atomically
moves the receipt from `gate` to `development`, so implementation cannot start
against a stale gate receipt.

All mutating commands take a repository-local advisory lock around their
read-modify-write operation, so parallel tool execution cannot allocate
duplicate discovery IDs or silently overwrite another receipt update.

A failed understanding gate is recorded with `gate-fail --reason` and sets
`stage` to `confirmation`; the phase sequence stays monotonic. A failed gate
signals that the specification is ambiguous. It is not a record of human
error.
