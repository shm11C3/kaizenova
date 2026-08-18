# Project Agent Guidance

<!-- EDIT ME: one short paragraph. What this project is, and what outcome
     justifies the work. Delete every EDIT ME comment once filled in. -->

## Required Task Workflow

Use `$execute-task-cycle` for every implementation task. It classifies the
task as **contract-preserving** or **contract-changing** before any
implementation, then runs the abbreviated or full path. The skill is the
canonical procedure; do not restate it here.

Do not implement a contract-changing task before the human passes the
understanding gate (`$gate-shared-understanding`). Track the active stage in
`.kaizenova/task-cycle.json` using `scripts/task_cycle.py`; lifecycle hooks
enforce it at turn boundaries (see `docs/agents/ENFORCEMENT.md`).

## Sources of Truth

<!-- EDIT ME: list the documents that fix outcomes, invariants, and design for
     this project. The workflow reads this list. Examples: -->

- Product outcomes: `docs/PRODUCT.md`
- Fixed safety invariants: `docs/INVARIANTS.md`
- Current design: `docs/design/`
- Shared vocabulary: `CONTEXT.md`

## Project Validation Stage (optional)

<!-- EDIT ME or delete this section. If this project needs an extra validation
     stage after PR review (for example, product QA against fixtures or an
     end-to-end scenario run), declare here: when it applies, what evidence it
     must produce, and where that evidence is recorded. The task cycle records
     the evidence before the retrospective; there is no separate state-machine
     phase for it. -->

## Engineering Rules

- Use TDD for contract-changing tasks; run validation proportionate to the
  changed surface for contract-preserving ones.
- Do not mix unrelated cleanup with the task's hypothesis.
- Add abstractions only after two concrete uses or measured friction.
- Every new rule, check, or mechanism records the evidence that triggered it
  and the condition under which it should be removed.
- Let production code show how, tests state what, commit messages explain why,
  and code comments explain why the obvious alternative was not chosen.
- <!-- EDIT ME: language rule. Example: "Write human-facing documents
  (Issues, PRs, retrospectives) in Japanese; write code, identifiers,
  comments, and agent guidance in English." -->

## Definition of Done

A task is not complete until:

- acceptance criteria and relevant failure cases pass;
- a PR exists, required review is approved, and CI passes;
- every handled review thread has a reply stating what changed and its
  validation evidence, and every no-action thread has a reply explaining why,
  before the thread is resolved;
- every discovery is resolved in this task or has an Issue reference; and
- the evidence required by the selected path is recorded: completion evidence
  for contract-preserving; retrospective, rule-removal review, and next-work
  handoff for contract-changing.
