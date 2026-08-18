---
name: gate-shared-understanding
description: Verify the human's connected, system-level understanding of an agreed specification before coding, crediting causal explanations already given and testing synthesis across components rather than document retrieval. Use during the mandatory understanding gate after specification decisions are settled and before implementation.
---

# Gate Shared Understanding

Read the task's outcome, the agreed specification, decision log, acceptance
criteria, safety invariants, alternatives, non-goals, and the project's shared
vocabulary.

## When the Gate Applies

Task classification decides gate applicability before this skill runs. A
`contract-changing` task always runs the gate. A `contract-preserving` task
uses the abbreviated workflow and never reaches the gate.

Before building the gate, check that no unresolved decision can still change
the implementation contract. Deferred decisions are acceptable only when this
task does not depend on them; anything else returns to confirmation.

## Purpose

The gate keeps the developer's intent reflected in the codebase and keeps
their understanding of it current. Its subject is cognitive debt and intent
debt.

The gate is not an audit, not a compliance record, and not a control over the
human. Do not add or ask for proof of passage such as an attestation field or
signature. Intent belongs in the decision log, because what a future reader
needs is why the design is this way, not who approved it.

Seek the minimum shared model needed to implement intentionally: why the task
exists, its overall shape, how it connects to the rest of the system, and the
reasoning behind its safety boundary. Do not test comprehensive recall of the
specification. Details that can be recovered from the design doc during
implementation do not need to be memorized.

A failed gate means the specification is ambiguous. It is not a score.

## Test Connected Understanding, Not Retrieval

A question whose answer sits in one identifiable paragraph of one document
measures the ability to find that paragraph, not understanding. This failure
mode is strongest when the human is working in a domain new to them: they
answer each question correctly by lookup while the system-level picture — how
the parts connect and why — is never exercised. Design every gate against it.

**Sketch first when the domain is unfamiliar.** When the task touches a domain
or subsystem the human has not implemented in before, open the gate by asking
the human to explain, in their own words and without consulting documents
mid-answer, the end-to-end flow the change touches: what enters, which
components handle it in what order, and where this task's change sits. Then
compare the sketch against the actual specification and code. Material gaps in
the sketch are what the remaining questions target; do not ask about parts the
sketch already got right. Teaching the gap and then probing it with a new
scenario is the gate working, not the gate failing.

**Require at least one trace scenario.** One question must follow a concrete
input, request, or event across two or more components or contracts: what
happens at each boundary, and what changes when a failure occurs partway. A
trace cannot be answered by locating a single passage; assembling it from
several documents is itself the connected understanding the gate seeks.

**Prefer open questions; use multiple choice only to pin down a specific
confusion.** Recognition is easier than recall, and options can be
pattern-matched back to document phrases. When multiple choice is warranted,
build distractors from real details of the repository: a reading a nearby file
would plausibly support, a confusion between two mechanisms that genuinely
resemble each other, or an answer that was true before this change.

**Weight intent at least as heavily as behavior.** Good questions ask which
invariant governs a decision, what tradeoff a choice buys, and what consequence
follows. Do not ask about implementation trivia: interpreter behavior, exact
API semantics, or which exception a call raises. Prefer observable
consequences over internal result names.

## Reuse Existing Understanding

Before writing a question, inspect the current conversation for explanations
and decisions already provided by the human. Credit a statement when it
demonstrates the same causal understanding a scenario would test: why the task
exists, what responsibility boundary applies, what consequence follows, or why
an alternative was rejected.

Do not ask the human to restate an already-demonstrated boundary to satisfy a
question count. The gate still runs: it inventories the existing evidence,
identifies material gaps, asks only about those gaps, and records the
resulting decision. If the minimum shared model and every safety-critical
point are already demonstrated, pass without a new question.

## Build the Gate

Across the sketch, existing evidence, and new questions, cover:

- why this task is needed now, what evidence or next decision it enables, and
  what would remain unsafe or unmeasurable if it were skipped;
- the end-to-end flow the change participates in (the trace scenario);
- expected behavior and at least one failure or recovery path;
- at least one rejected alternative and its tradeoff;
- safety-critical invariants;
- current task boundaries: what the preceding work provides and what the
  following work may consume.

One scenario may cover multiple items. Ask up to three new questions by
default; add another only for a distinct safety-critical gap that cannot be
combined clearly. Do not sample every documented decision merely because it is
documented.

Name the documents and implementation paths to consult when unsure, next to
each question. The gate should leave the human better able to find the
authority, not only able to answer once. Mark safety-critical questions.

## Run the Gate

Ask **one question per turn** and wait for the answer before writing the next.
Do not issue a batch. Do not show answers or hints.

Evaluate each answer as: correct; partially correct; incorrect; specification
ambiguous; or question unfair.

Pass only when the sketch, existing evidence, and any new answers show that
every safety-critical answer is correct and the remaining answers demonstrate
sufficient connected understanding for implementation decisions.

## Failure Handling

If an answer is insufficient:

1. identify the misunderstood concept or the missing connection;
2. explain it with reference to the agreed specification, using measured
   evidence when available;
3. record the attempt with
   `python3 scripts/task_cycle.py gate-fail --reason "<what was ambiguous>"`;
4. update the specification if ambiguity caused the miss;
5. create a new scenario rather than accepting memorized repetition.

Do not fail the human when the fault is not theirs:

- if the specification itself is ambiguous, fix the specification first;
- if the repository's own code, comments, or an earlier review already taught
  the opposite reading, the question was unfair; withdraw it and fix the
  source of the contradiction;
- if the gate author's own framing turns out to be wrong, the human correcting
  it is intent alignment succeeding, not a failed answer.

## Evidence

Record, when present:

- the human's system sketch and the gap inventory derived from it;
- credited existing evidence mapped to every required point;
- questions asked for remaining gaps, the answers, and their evaluation;
- the evaluation of each safety-critical point;
- clarifications, and the final pass or return-to-confirmation decision.

Store the final gate result and the implementation-relevant judgments in the
task Issue or decision log. Keep the question-and-answer detail in task-cycle
state and PR evidence; do not retain a full attempt transcript in the design
doc. Record the reasoning, not an attestation.
