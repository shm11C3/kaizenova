# Design Notes

kaizenova was extracted from a private project (kaizen-agent, an ISUCON
improvement agent) where the loop ran for several weeks of daily agent-driven
development. This document is the narrative behind the extraction; the
individual decisions it produced are recorded as ADRs in [adr/](adr/), each
with the evidence that triggered it and the conditions that would reopen it.

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

A second lesson concerned the understanding gate: per-task multiple-choice
questions were being answered by locating the right paragraph in the design
docs. In unfamiliar domains — exactly where the gate mattered most — it
measured retrieval, not the connected understanding it existed for.

## Where each decision lives

| Decision | ADR |
|---|---|
| Template distribution with a copying installer; CLI packaging rejected with recorded reopening triggers | [0001](adr/0001-template-distribution.md) |
| Python, standard library only; Go/TS rejected on distribution fit | [0002](adr/0002-python-stdlib-only.md) |
| Thin, fail-closed enforcement; what was excluded from the origin and what would reopen each piece | [0003](adr/0003-thin-fail-closed-enforcement.md) |
| Gate tests connection over retrieval; persistent understanding ledger with a stale lifecycle | [0004](adr/0004-understanding-gate-and-ledger.md) |
| One canonical layer per concern, rule trigger+removal metadata, mandatory subtraction at retrospective | [0005](adr/0005-canonical-layer-and-subtraction.md) |
| Self-contained skills (inlined TDD and interview); interview narrowed to contract decisions, crediting grill-me | [0006](adr/0006-self-contained-skills.md) |

## The standard this repository holds itself to

Every mechanism in kaizenova must name the observed incident that justifies
it, and every rule must name the observation that would remove it. The ADRs
above apply that standard to the tool's own design decisions; the
retrospective's mandatory "Rules Reviewed for Removal" section applies it to
everything added later. A harness that can only grow becomes the thing it was
built to prevent.
