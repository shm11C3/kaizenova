# Understanding Ledger

Demonstrated understanding carried across tasks, so the understanding gate
measures the accumulated shared model and its decay instead of re-testing the
same ground every task.

- One entry per living contract or subsystem, at the contract level — not one
  per task, and not implementation detail.
- The gate credits `current` entries instead of re-asking them, and re-verifies
  `stale` entries the task depends on.
- The task that changes a contract marks its entries `stale`, naming what
  changed. Delete an entry when its contract no longer exists.
- This is a memory aid for the gate, not an audit record: it records what
  causal understanding was demonstrated, never who approved what.

Entry format (delete this example when adding the first real entry):

## Example: request pipeline

- status: current
- demonstrated: can trace a request from ingress through validation to the
  store, including what the retry layer does on a downstream timeout
  (task example-task, 2026-01-01)
