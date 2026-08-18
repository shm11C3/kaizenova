# Design Notes

kaizenova was extracted from a private project (kaizen-agent, an ISUCON
improvement agent) where the loop ran for several weeks of daily
agent-driven development. This document records what was generalized, what
was deliberately left behind, and why the harness is built to shrink.

## What the origin taught

The origin harness worked: classification stopped speculative rewrites, the
understanding gate caught ambiguous specifications before implementation, and
the lifecycle hooks caught skipped retrospectives mechanically. It also
exhibited a failure mode worth designing against: **the harness itself
overengineered**, for three structural reasons.

1. **A one-way ratchet.** The improvement loop required a "closure" for every
   material piece of feedback, but nothing ever removed a rule. One-off
   incidents (a sandbox credential quirk, a single externally-merged PR)
   became permanent prose in always-loaded skills, violating the harness's own
   promotion criteria.
2. **Too many layers, then enforcement of the layers.** The same rule ended up
   restated in the workflow document, the always-on guidance, and the skill.
   The fix chosen for drift between the copies was a 900-line consistency
   checker — meta-enforcement — rather than deduplication. The validation
   pyramid inverted: roughly 2,500 lines of checkers guarded roughly 1,100
   lines of actual tooling.
3. **Anti-overengineering mechanisms, in triplicate.** A complexity-review
   skill, always-on engineering rules, and a CI-based PR-scope meter all
   guarded the same concern independently.

## Countermeasures built into this design

- **One canonical layer per concern.** The skill is the procedure;
  `AGENTS.md` only routes to it; `ENFORCEMENT.md` only documents hook
  behavior. Nothing restates the workflow, so there is no drift to check and
  no consistency checker to maintain.
- **Rule metadata.** Every rule, check, or guidance line added through the
  improvement loop records the evidence that triggered it and the condition
  under which it should be removed. A rule without a trigger is speculative; a
  rule without a removal condition is permanent by accident.
- **Mandatory subtraction.** The retrospective template has a required
  "Rules Reviewed for Removal" section, and `task_cycle.py reflect` rejects a
  retrospective without it. Additions and removals get the same rigor.
- **One anti-overengineering mechanism.** The `$review-design-complexity`
  skill, invoked on evidence of disproportionate growth. No thresholds, no
  meters.

## The understanding gate: retrieval vs. connection

The origin gate asked multiple-choice questions per task. Observed failure
mode: in a domain new to the human, each question is answered correctly by
locating the right paragraph in the design docs, while the system-level
picture — how components connect and why — is never exercised. The gate
measured retrieval, not understanding.

The redesigned gate (`$gate-shared-understanding`) targets connection
directly:

- when the domain is unfamiliar, the human sketches the end-to-end flow in
  their own words *first*, and questions target only the gaps in the sketch;
- at least one scenario traces a concrete input across two or more components,
  which cannot be answered from a single passage;
- open questions are the default; multiple choice is reserved for pinning down
  a specific confusion.

A persistent **understanding ledger** (`docs/agents/understanding-ledger.md`)
carries demonstrated understanding across tasks: the gate credits `current`
entries instead of re-asking them, and re-verifies entries that a contract
change marked `stale`. This turns the gate from a per-task snapshot into a
measure of the accumulated shared model and its decay.

The ledger is itself a rule and follows the rule-metadata discipline. Trigger:
per-task gates were observed re-testing settled ground while stale
understanding went undetected. Guardrails against becoming a new accumulation
point: entries live at the contract level only, the task that changes a
contract marks its entries stale, and entries are deleted with their contract,
so the ledger tracks living contracts and nothing else. Removal condition: if
gates stop consulting it, or it fills with entries no gate ever credits,
remove it.

## Deliberately excluded

| Excluded | Reason | What would reopen it |
|---|---|---|
| QA phase in the state machine | Project-specific; most repositories have no separate agent-facing QA subject | Nothing — declare a validation stage in `AGENTS.md` instead |
| State-file versioning and migration (`gate-skip`, v1/v2 compatibility) | Migration machinery for in-flight tasks of the origin repo; a fresh tool starts at one version | A future breaking state change shipped to real users |
| Multi-agent delegation reconciliation | Tied to the origin's worktree-per-subagent practice | Measured demand from users running delegated subagents |
| PR-scope and measurement-drift metering | Bound to the origin's directory layout and experiment cadence; overlapped two other mechanisms | Evidence that the complexity-review skill alone misses scope creep |
| Meta-validation of guidance consistency | The layer deduplication above removes the drift it guarded | Reintroducing duplicated guidance layers (do not) |
| Third-party skill references (`$tdd`, `$grill-me`) | A public template cannot depend on skills users do not have | Nothing — the procedures are inlined in `$execute-task-cycle` |

## What was kept fail-closed, and why

Each fixed hook behavior traces to an incident observed in the origin:

- **Ambiguous receipts block.** A receipt written in a subdirectory was
  measured silencing enforcement for the whole repository.
- **Unreadable receipts block.** Treating unreadable as absent silently
  disables every other check.
- **Old interpreters block.** A crashing hook fails open; the adapters check
  the interpreter before importing the shared core.
- **`gate-pass` advances atomically.** Keeping "pass" and "advance" as two
  successful commands allowed implementation to start against a stale gate
  receipt.
- **Mutations take an advisory lock.** Parallel tool calls could otherwise
  allocate duplicate discovery IDs or overwrite a receipt update.

These survive because their triggers were observed, not hypothesized — the
same standard every future addition must meet.
