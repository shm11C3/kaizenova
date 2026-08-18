# ADR 0004: Gate connected understanding, not retrieval; keep a persistent understanding ledger

- Status: Accepted (ledger adopted by owner decision after initial deferral)
- Date: 2026-08-19

## Context

The origin's understanding gate asked multiple-choice questions per task.
Observed failure mode: in a domain new to the human, every question was
answered correctly by locating the right paragraph in the design docs, while
the system-level picture — how components connect and why — was never
exercised. The gate measured retrieval ("point" understanding), not the
connected ("line") understanding it existed for. The effect was strongest
exactly where the gate mattered most: unfamiliar territory.

A second gap: crediting prior understanding only within the current
conversation meant every task re-tested settled ground, while understanding
invalidated by later contract changes decayed undetected.

## Decision

Two layers, both in `$gate-shared-understanding`:

**Question design.** When the domain is unfamiliar, the human sketches the
end-to-end flow first and questions target only the sketch's gaps. At least
one scenario traces a concrete input across two or more components — not
answerable from a single passage. Open questions are the default; multiple
choice only pins down a specific confusion.

**Understanding ledger** (`docs/agents/understanding-ledger.md`, committed).
One entry per living contract records what causal understanding the human
demonstrated and when. The gate credits `current` entries instead of
re-asking, and re-verifies entries a contract change marked `stale`. The task
that changes a contract marks dependents stale (via
`$reflect-and-improve-harness`); entries are deleted with their contract. The
gate thereby measures the accumulated shared model and its decay, not a
per-task snapshot.

The ledger is a skill-level procedure, deliberately not enforced by the CLI or
hooks: its content is judgment, and mechanizing judgment is how the origin
overengineered (ADR 0005).

## Consequences

- Gates get cheaper over time on stable territory and re-focus automatically
  where contracts changed.
- The ledger is a memory aid, not an audit record: it stores what
  understanding was demonstrated, never who approved what.
- Guardrails against the ledger becoming its own accumulation point: entries
  live at contract level only, staleness is marked at the task that causes
  it, and deletion follows the contract.

## Revisit when

Gates stop consulting the ledger, or it fills with entries no gate ever
credits — remove it. If skill-level discipline proves insufficient (ledger
updates skipped repeatedly), that evidence — not anticipation — would justify
mechanical enforcement.
