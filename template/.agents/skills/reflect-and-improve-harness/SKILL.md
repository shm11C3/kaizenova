---
name: reflect-and-improve-harness
description: Run the mandatory post-task retrospective for a contract-changing task, classify friction and failures, improve the smallest appropriate harness layer, and review existing rules for removal. Use after PR review and any project validation stage, before completing the full workflow.
---

# Reflect and Improve Harness

Read the retrospective template at `docs/agents/retrospectives/TEMPLATE.md`,
task-cycle state, and the task Issue, PR, review comments, CI, and test
evidence.

This skill reconciles an improvement loop that should already have run when
material evidence appeared. It must not turn a missing behavioral change into
a write-only retrospective.

## Collect Evidence

Identify:

- what accelerated the task;
- repeated confusion or review feedback;
- missing or excessive context;
- workflow steps that were skipped or manually recovered;
- hook, rule, or skill failures;
- discovered implementation problems and Issue references.

Separate repository defects from environment noise. For each material item,
name the structural cause, current-task correction, selected closure, and
forward-test evidence.

If recurrence or precedent affects a decision, write exact external feedback
to a private file without passing it through a shell, then use bounded
retrieval rather than loading all history:

```bash
python3 scripts/find_relevant_lessons.py --query-file .kaizenova/lesson-query.txt --limit 5
```

## Classify Each Lesson

Choose the smallest layer that reliably prevents recurrence:

| Cause | Primary closure |
|---|---|
| Incorrect implementation or missing failure handling | Code plus a regression test |
| Repeated multi-step judgment or procedure | A skill plus a forward test |
| Cheap deterministic invariant | Hook, CI, linter, or schema check |
| Always-on repository boundary or ownership rule | Concise `AGENTS.md` guidance |
| Product, safety, or architecture ambiguity | Canonical document clarification before enforcement |
| Provider divergence (Claude vs Codex) | Shared hook core or canonical skill |
| Evidence useful across tasks but not itself preventive | `docs/agents/lessons/` |

Do not copy the same rule into multiple layers. Do not add speculative
guidance. A one-off environment failure or transient state never lands in
always-loaded guidance. A lesson entry preserves evidence but is not
mechanical enforcement and does not count as closing a preventable failure by
itself.

If the structural cause or desired invariant is unclear, return to the human
with the evidence, options, and consequences. Do not hide the ambiguity in the
retrospective.

## Rule Metadata

Every rule, check, or guidance line this task adds must record, at its own
layer or in the retrospective:

- the observed evidence that triggered it; and
- the removal condition: what future observation would show it is no longer
  earning its keep.

A rule without a trigger is speculative; a rule without a removal condition is
permanent by accident.

## Rules Reviewed for Removal

Additions have a mandatory counterpart: on every retrospective, review the
harness for subtraction. This is a required section of the retrospective, and
`task_cycle.py reflect` rejects a retrospective without it.

1. List the rules, checks, and guidance that were exercised this task and note
   which ones changed behavior versus which only added reading cost.
2. Check existing rules whose removal condition is now met, whose triggering
   evidence no longer applies, or that duplicate another layer.
3. Propose each removal with the same rigor as an addition: evidence, the
   contract that must remain protected, and the validation that proves the
   removal is safe. Apply small safe removals in this task; file an Issue for
   larger ones.
4. `None` is an acceptable answer only after the review actually ran; say what
   was reviewed.

Repeated feedback is evidence that the existing closure was absent or
insufficient. Do not append the same prose again; inspect why the prior
mechanism was not selected, not loaded, not understood, or not enforced, then
strengthen or replace that layer.

## Apply and Validate

Apply small, safe, evidence-backed harness changes in the current task. For
larger work, search for an existing Issue, create or reuse a scoped one, and
record the link.

For every behavioral change — a new rule, a changed hook, a changed skill —
forward-test the original failure or an equivalent negative path. The presence
of new prose is not behavioral evidence. For changed hooks, test the valid,
invalid, missing-state, human-wait, unresolved-discovery,
retrospective-required, and completed states.

## Record

Create `docs/agents/retrospectives/YYYY-MM-DD-task.md` from the template.
State why each harness change belongs at its chosen layer, with its trigger
and removal condition. Fill the Rules Reviewed for Removal section from the
review above.

## Hand Off the Next Work

Close the task by reporting the open Issues, grouped so the owner can pick the
next task without re-reading the tracker:

- **ready to start**: scope and approach are settled. Give a suggested order
  and the reason, and name anything this task left partial or known-broken;
- **needs a decision first**: state the decision, the options, and the cost of
  each;
- **blocked or waiting**: name what they wait on.

Keep it to one pass of reading. Do not restate the retrospective.

Record the retrospective with `scripts/task_cycle.py reflect`, then complete
the cycle.
