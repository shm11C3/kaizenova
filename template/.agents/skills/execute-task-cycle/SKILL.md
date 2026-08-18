---
name: execute-task-cycle
description: "Execute one implementation task by classifying its contract impact first, then using either the abbreviated contract-preserving path or the full specification, confirmation, gate, TDD, PR, retrospective path. Use whenever the user asks to implement, build, change, or fix something in a repository that uses the task cycle."
---

# Execute Task Cycle

Read `AGENTS.md` and the sources of truth it declares, plus the applicable
design document and task Issue. This skill is the canonical procedure; other
documents must not restate it.

## Start or Resume

Inspect state:

```bash
python3 scripts/task_cycle.py status
```

If no task is active, start one:

```bash
python3 scripts/task_cycle.py start --task <id> --title "<title>" --issue <url-or-number>
```

Treat the state file as a workflow receipt, not as the specification source.

## Classification

Before specification or implementation, decide whether the task is
`contract-preserving` or `contract-changing`.

Use `contract-preserving` only when all of these are established:

- the requested result is fixed by the request, the Issue, or an existing
  source of truth;
- observable behavior, safety invariants, interfaces, schemas, failure
  handling, permissions, rollout, and human/AI responsibilities do not change;
- acceptance criteria and validation can be stated before implementation; and
- no unresolved design choice can change the user or operator result.

Use `contract-changing` when any criterion is not met. Complexity, file type,
and diff size do not decide the classification. If the criteria cannot be
evaluated, record a human wait and ask the owner:

```bash
python3 scripts/task_cycle.py wait-human --reason "<classification question>"
```

Record the decision:

```bash
python3 scripts/task_cycle.py classify \
  --kind contract-preserving \
  --reason "<contract impact>" \
  --decided-by agent
```

A contract-preserving task advances directly to Development. A
contract-changing task advances to Specification. Use `--decided-by human`
after the owner decides an uncertain classification.

If a contract-preserving task turns out to change a contract, stop the
abbreviated path before making further contract-changing edits:

```bash
python3 scripts/task_cycle.py escalate --reason "<discovered contract change>"
```

## Specification

This section and the Confirmation and Gate sections apply only to a
contract-changing task. Do not edit production code during them.

Write a compact specification proposal containing outcome, invariants,
alternatives, non-goals, acceptance evidence, failure tests, and unresolved
questions.

Before Human Confirmation, explain the proposal to the human in this order:

1. why the task is needed now and what remains unverified if it is deferred;
2. how responsibilities, inputs, the main flow, and failures work;
3. what observable output or next decision the task enables; and
4. what the preceding task provides and the following task may consume without
   recomputing.

Use a diagram when there are multiple responsible roles, three or more
dependent steps, state transitions, or branches. Update the project's shared
vocabulary document in the same pull request when the task introduces a shared
term or changes its meaning.

Advance after the proposal is ready:

```bash
python3 scripts/task_cycle.py advance --phase confirmation
```

## Confirmation

Interview the human until every material branch is resolved. Do this yourself;
do not defer to an external skill:

- Ask one question per turn and wait for the answer.
- Work through the decision tree branch by branch: product outcome, interfaces,
  failure handling, rollout, and ownership boundaries. Challenge assumptions
  the specification takes for granted, including your own.
- For each open decision, present the viable options with their concrete
  consequences, then let the human choose. Do not present a menu when the
  evidence already selects an option; recommend it and say why.
- A decision may be deferred only when this task does not depend on it. Record
  each deferral with its owner, consequence, and decision deadline.
- Stop interviewing when new questions stop changing the specification.

Record durable decisions at the canonical layer the project declares (design
doc, ADR, or product doc). Update the task Issue so its outcome and completion
criteria match the confirmed contract; do not leave pre-confirmation options in
it as though they were still authoritative.

No unresolved decision that can change the implementation contract may pass
the gate. When waiting:

```bash
python3 scripts/task_cycle.py wait-human --reason "<question>"
```

Resume and advance:

```bash
python3 scripts/task_cycle.py resume
python3 scripts/task_cycle.py advance --phase gate
```

## Gate

Use `$gate-shared-understanding`. Do not reveal expected answers before the
human responds.

If the gate fails, record why the specification was ambiguous and return to
confirmation:

```bash
python3 scripts/task_cycle.py gate-fail --reason "<what was ambiguous>"
```

After the human passes, `gate-pass` rejects unresolved discoveries and
atomically advances to Development. Do not begin edits before that transition
succeeds:

```bash
python3 scripts/task_cycle.py gate-pass \
  --evidence "<Issue or design doc reference>" \
  --decision-log docs/design/NNNN-short-title.md
```

## Development

For a contract-changing task, use test-driven development and keep
red-green-refactor evidence:

1. Write one failing test for the next agreed behavior.
2. Run it and confirm it fails for the expected reason, not for a setup error.
3. Write the smallest implementation that passes.
4. Run the test and see it pass.
5. Refactor with tests green, without changing behavior.
6. Repeat until the agreed behavior is covered, then run full task-level
   validation before the PR.

Keep the red and green command outputs as validation evidence. Return to
Confirmation rather than silently changing the specification.

For a contract-preserving task, TDD is optional; run validation proportionate
to the changed surface.

## Structural Feedback Loop

Run this loop immediately when a material human correction, review finding,
test or CI failure, or provider difference appears. Do not defer it to the
retrospective.

1. Preserve the evidence and state the structural cause that allowed the
   problem and the recurrence path.
2. Clarify the canonical contract and desired invariant.
3. If the cause, invariant, or tradeoff remains unclear, record a Discovery and
   use `task_cycle.py wait-human` before editing.
4. After the decision is clear, correct the current artifact and close the
   cause through the smallest effective guidance or mechanical enforcement.
   Every added rule records the evidence that triggered it and the condition
   under which it should be removed.
5. Forward-test the selected closure against the original failure.

When tests, fixtures, mocks, fault injection, state space, exceptional paths,
or coverage-recovery work grow disproportionately to the observed outcome,
invoke `$review-design-complexity` before adding coverage-only tests, weakening
a quality gate, or expanding exceptional handling.

When recurrence or precedent would change the selected layer, write exact
external feedback to a private file without passing it through a shell, then
retrieve only bounded evidence:

```bash
python3 scripts/find_relevant_lessons.py --query-file .kaizen/lesson-query.txt --limit 5
```

## Discoveries

Record every material discovery, meaning anything that may affect acceptance,
safety, correctness, scope, or identifiable future work:

```bash
python3 scripts/task_cycle.py discover --summary "<problem>" [--blocking]
```

Do not record incidental observations. Naming quibbles and stale comments
belong in the code review; a discovery log full of them buries the findings
that matter.

When the problem is fixed in this task, record that instead of filing an Issue:

```bash
python3 scripts/task_cycle.py resolve-discovery --discovery D001 --note "<how>"
```

For deferred work, search open and closed Issues first, reuse a duplicate or
create a scoped Issue, then link it:

```bash
python3 scripts/task_cycle.py link-issue --discovery D001 --issue <url-or-number>
```

Do not expand scope silently, and do not file an Issue in place of a judgment.

## PR and Review

Advance to `pr`, create the PR, and address actionable review feedback until
required review approves and CI passes:

```bash
python3 scripts/task_cycle.py advance --phase pr
```

Run the Structural Feedback Loop for material review findings. When a finding
repeats prior feedback, inspect why the prior closure failed before adding
more prose.

For every handled review thread, reply with what changed and the validation
evidence before resolving it. For a withdrawn or no-action thread, reply with
why no change is needed before resolving it. Do not complete while an
actionable review thread remains unanswered. Do not merge unless the user
requests it or repository policy explicitly authorizes it.

For a contract-preserving task, record validation, review replies, required
review status, and CI as completion evidence; the abbreviated path ends here:

```bash
python3 scripts/task_cycle.py complete \
  --evidence "<validation, review replies, required review, and CI>"
```

## Project Validation Stage (optional)

If the project's `AGENTS.md` declares an additional validation stage (for
example, product QA against fixtures), run it now and record its evidence in
the task Issue or PR before the retrospective. When it does not apply, record
why and name the validation evidence that replaces it. There is no separate
state-machine phase for this stage.

## Retrospective

Advance and use `$reflect-and-improve-harness`:

```bash
python3 scripts/task_cycle.py advance --phase retrospective
```

The retrospective reconciles structural improvements already started when the
evidence appeared. It is not permission to postpone them.

Record it and complete:

```bash
python3 scripts/task_cycle.py reflect \
  --path docs/agents/retrospectives/YYYY-MM-DD-task.md \
  --harness-impact applied|issue-filed|none
python3 scripts/task_cycle.py complete
```

Never call a contract-changing task complete before this succeeds. Finish by
handing off the next work as described in `$reflect-and-improve-harness`.
