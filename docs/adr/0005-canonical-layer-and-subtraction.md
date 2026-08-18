# ADR 0005: One canonical layer per concern, rule metadata, mandatory subtraction

- Status: Accepted
- Date: 2026-08-19

## Context

The origin harness identified three structural generators of its own
overengineering:

1. **A one-way ratchet.** The improvement loop required a closure for every
   material piece of feedback, and nothing ever removed a rule. One-off
   incidents became permanent prose in always-loaded skills.
2. **Duplicated layers, then enforcement of the duplication.** The same rule
   was restated across the workflow document, the always-on guidance, and the
   skill; the chosen fix for drift was a 900-line consistency checker rather
   than deduplication. Checkers ended up at roughly twice the size of the
   tooling they guarded.
3. **Anti-overengineering in triplicate.** A complexity-review skill,
   always-on rules, and a CI meter guarded the same concern independently.

## Decision

- **One canonical layer per concern.** Skills are the procedure. The target's
  `AGENTS.md` only routes to them; `ENFORCEMENT.md` only documents hook
  behavior. Nothing restates the workflow, so there is no drift to check and
  no consistency checker to maintain.
- **Rule metadata.** Every rule, check, or mechanism added through the
  improvement loop records the evidence that triggered it and the condition
  under which it should be removed. A rule without a trigger is speculative;
  a rule without a removal condition is permanent by accident.
- **Mandatory subtraction.** The retrospective template requires a "Rules
  Reviewed for Removal" section and `task_cycle.py reflect` rejects a
  retrospective without it. Removals are proposed with the same rigor as
  additions: evidence, preserved contract, validation.
- **One anti-overengineering mechanism.** `$review-design-complexity`,
  invoked on evidence of disproportionate growth. No thresholds, no meters.

These ADRs apply the discipline to the tool itself: each records its trigger
and its revisit condition.

## Consequences

- The harness can shrink, not only grow; a quiet rule that stops earning its
  keep has a scheduled exit path.
- Losing the origin's redundancy is accepted: if a rule is mis-stated in its
  single canonical home, no second copy contradicts it. Review of the one
  copy replaces reconciliation of many.

## Revisit when

Retrospectives show the removal review being answered "None" without an
actual review (the forcing heading failed), or a rule class emerges that
genuinely needs restating across layers — either would reopen how the
discipline is enforced, not whether it exists.
