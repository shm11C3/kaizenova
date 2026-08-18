# ADR 0003: Keep mechanical enforcement thin and fail-closed

- Status: Accepted
- Date: 2026-08-19

## Context

kaizenova was extracted from the kaizen-agent harness, where lifecycle hooks
demonstrably caught skipped workflow steps — and where enforcement machinery
also accumulated far beyond its value (see `../DESIGN.md`). The extraction had
to decide, mechanism by mechanism, what earns a place in a generic tool.

The standard applied: a mechanism is kept only when its trigger was an
observed incident, not a hypothesis.

## Decision

Ship a small state machine (`classification → [specification → confirmation →
gate →] development → pr → [retrospective →] completed`) with lifecycle hooks
for both providers sharing one decision core. Behaviors and their fixed or
tunable class are documented in the installed `docs/agents/ENFORCEMENT.md`.

Kept fail-closed, each traced to an observed incident in the origin:

- **Ambiguous receipts block** — a nested receipt was measured silencing
  enforcement for the whole repository.
- **Unreadable receipts block** — treating unreadable as absent silently
  disables every other check.
- **Old interpreters block** — a crashing hook fails open, so adapters check
  the interpreter before importing the core.
- **`gate-pass` advances atomically** — pass and advance as two commands let
  implementation start against a stale gate receipt.
- **Mutations take an advisory lock** — parallel tool calls could allocate
  duplicate discovery IDs or overwrite a receipt update.

Excluded, with what would reopen each:

| Excluded | Reason | What would reopen it |
|---|---|---|
| QA phase in the state machine | Project-specific; declared instead as an optional validation stage in the target's `AGENTS.md` | Nothing — the extension point covers it |
| State-file versioning and migration (`gate-skip`, v1/v2) | Migration machinery for the origin's in-flight tasks; a fresh tool starts at one version | A breaking state change shipped to real users |
| Multi-agent delegation reconciliation | Tied to the origin's worktree-per-subagent practice | Measured demand from users running delegated subagents |
| PR-scope and measurement-drift metering | Bound to the origin's layout; overlapped two other mechanisms guarding the same concern | Evidence that `$review-design-complexity` alone misses scope creep |
| Meta-validation of guidance consistency | ADR 0005 removes the duplicated layers whose drift it guarded | Reintroducing duplicated guidance layers (do not) |

## Consequences

- Enforcement is trustworthy without being heavy: ~1,100 lines of tooling,
  one behavior-test file, no meta-checkers.
- Anything a hook cannot confirm blocks rather than passes, so a broken
  harness is visible instead of silently permissive.
- Projects needing excluded machinery must show the reopening evidence first.

## Revisit when

A listed reopening condition occurs, or a fixed behavior causes recurring
friction that its incident history no longer justifies — that discussion
belongs in a recorded decision, per `ENFORCEMENT.md`.
