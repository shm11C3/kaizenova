# ADR 0006: Skills are self-contained; the confirmation interview is decision-focused

- Status: Accepted
- Date: 2026-08-19

## Context

The origin workflow delegated two steps to third-party skills from the
owner's personal environment: `$tdd` for red-green-refactor development and
`$grill-me` for the confirmation interview. A public template cannot
reference skills its users do not have, and copying their text is not an
option.

On interview style specifically, the owner's experience was that exhaustive
plan-grilling is too heavy for this loop: most of a specification does not
need interrogation, only its contract-relevant decisions do.

## Decision

Inline both procedures into `$execute-task-cycle`, written from scratch:

- **Development** carries a traditional TDD procedure: one failing test,
  confirm it fails for the expected reason, smallest passing change,
  refactor green, keep red-green evidence.
- **Confirmation** carries an interview procedure that targets decisions, not
  coverage. Open points are sorted into three kinds: decisions that change
  the contract or need the owner's agreement (interviewed, one question per
  turn); decisions the agent can make (stated as proposals the human can
  veto); settled facts (not questioned). The interview stops when remaining
  questions can no longer change the contract.

The interview's decision-tree questioning borrows its spirit from Matt Pocock's
`grill-me` skill, credited in the README, and deliberately narrows it as
described above.

## Consequences

- The template has zero skill dependencies; the acknowledgements section in
  the README records the intellectual debt.
- Interview cost scales with the number of open contract decisions, not with
  specification size.
- The narrowing trades exhaustiveness for focus: an assumption misclassified
  as a settled fact will not be interviewed. The understanding gate
  (ADR 0004) is the backstop that catches a contract misunderstanding before
  implementation.

## Revisit when

Gate failures or review findings repeatedly trace back to decisions the
interview classified as settled facts or agent-decidable — evidence the
narrowing cut too deep.
