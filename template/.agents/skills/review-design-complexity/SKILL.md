---
name: review-design-complexity
description: "Audit suspected overengineering when tests, fixtures, mocks, fault injection, failure paths, state transitions, abstractions, review follow-ups, or coverage-recovery work grow disproportionately. Use this signal to distinguish required validation from accidental or speculative design before adding coverage-only tests, weakening a quality gate, or adding more exceptional handling."
---

# Review Design Complexity

Treat growth in validation and state space as a reason to inspect the design,
not as proof that the design is excessive.

## Scope and Authority

Determine whether the user requested diagnosis only or authorized a change.
When the request is diagnostic, inspect read-only evidence and return a
diagnosis. Do not edit code, specifications, quality gates, Issues, or pull
requests.

Keep this review inside the current task's scope and phase. This skill does
not classify the task, advance its workflow, or authorize implementation. If a
recommended change is contract-changing, return it to `$execute-task-cycle`
for classification, confirmation, and the understanding gate before
implementation.

Treat the project's declared sources of truth — the current Issue, design
docs, shared vocabulary, and fixed safety requirements — as authorities. Do
not weaken a stated contract or safety invariant because it is expensive to
test. Stop with `human-decision` when the evidence does not settle a product
or safety tradeoff.

## Gather Evidence

Read the applicable source of truth before measuring the change. Use existing
repository commands and artifacts; do not create a permanent collection script
for this review.

Collect only evidence that can affect the diagnosis:

- the requested outcome, accepted contract, non-goals, and safety requirements;
- the relevant baseline and current diff, including changed production and
  test surfaces rather than absolute line counts alone;
- failing tests, coverage reports, uncovered branches, review findings, and
  repeated implementation friction;
- public call paths and state transitions needed to establish reachability;
- existing invariants or higher-level tests that may already cover the risk;
- measured failures, users, or threat actors that justify an exceptional path.

Use `git diff --stat`, focused test output, and an existing coverage report
when available. Do not invent a ratio threshold for test lines, fixture size,
branch count, or coverage. If no comparison or failure evidence is available,
report the missing evidence and stop before recommending deletion.

## Review Workflow

Review each observed signal independently. Do not turn one large diff into one
large diagnosis.

1. Record the **Observation** as a comparison, failure, repeated addition, or
   concrete state-space expansion.
2. State the suspected pressure: duplication, coupling, state explosion,
   speculative generality, exceptional-path growth, or missing validation.
3. Fill **Required by** with the Issue, design doc, safety requirement,
   observed failure, concrete second use, or `None`.
4. Record **Counterevidence** that could show the complexity is necessary.
5. Establish whether the path is reachable and whether its impact is material.
6. Check whether an existing invariant, public contract test, or higher-level
   owner already covers the same fact.
7. Classify the signal and choose one recommendation with a validation plan.

Use these classifications:

- **essential**: a current outcome, fixed safety requirement, reachable
  material failure, or concrete repeated use requires the complexity.
- **accidental**: duplicate ownership, representation, checks, or state make
  the required behavior harder without adding a distinct contract.
- **speculative**: a future backend, threat, recovery mode, edge case, or
  second use is implemented without measured need or a current requirement.
- **validation-gap**: the behavior is required and the design is not shown to
  be redundant, but its contract lacks meaningful validation.

## Recommendations

Choose the smallest recommendation supported by the evidence:

- **keep-and-test**: retain essential behavior and retain or add the smallest
  public contract or failure test that demonstrates why it exists.
- **simplify**: remove or collapse accidental or speculative behavior while
  preserving the stated contract.
- **merge**: give one owner responsibility that is duplicated across records,
  states, checks, adapters, or fallback paths.
- **defer**: postpone speculative behavior until a named observation or
  concrete second use appears; state what evidence would reopen it.
- **human-decision**: stop when choosing an option would change product
  intent, fixed safety requirements, threat boundaries, or a quality policy.

For every simplification, merge, or deferral, name the contract that must
remain unchanged and the validation that will prove it. Re-run the original
failing test, coverage measurement, or review scenario only after the design
decision; do not optimize the metric before deciding which branches should
exist.

## False-positive Controls

Check these counterexamples before recommending reduction:

- Parser, protocol, schema migration, and security-boundary tests may validly
  outnumber production cases because they cover a large input space.
- Property tests, table-driven tests, and golden files may be long while still
  having low maintenance cost and broad behavioral coverage.
- A fail-closed branch may be rare but essential when its impact is high and
  its safety requirement is fixed.
- Characterization test growth may be a temporary safety net before an agreed
  design change.
- Direct tests of error messages or platform-specific behavior are valid when
  those details are a public contract or a supported platform requirement.
- A second concrete adapter, backend, caller, or measured recovery cost can
  justify an abstraction that would otherwise look speculative.

## Output

Return a short scope statement followed by one row per material signal:

| Field | Required content |
|---|---|
| Observation | Comparable fact, failure, or repeated growth |
| Suspected pressure | State space, coupling, duplication, speculation, or validation gap |
| Required by | Source of truth, observed failure, concrete use, or `None` |
| Counterevidence | Evidence that supports keeping the complexity |
| Classification | `essential`, `accidental`, `speculative`, or `validation-gap` |
| Recommended action | `keep-and-test`, `simplify`, `merge`, `defer`, or `human-decision` |
| Preserved contract | Behavior or safety boundary that must not change |
| Validation | Public or failure-path check to run after the decision |

End with the recommended order of action and any missing evidence or human
decision. Separate diagnosis from implementation. If the user authorized a
change, hand the selected action back to `$execute-task-cycle` instead of
treating this review as implementation permission.
