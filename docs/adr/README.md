# Architecture Decision Records

One record per decision that shaped kaizenova. Each ADR follows the same
rule-metadata discipline the tool imposes on its users: it records the
evidence that triggered the decision and the conditions that would reopen it.
A decision without a trigger is speculation; a decision without a revisit
condition is permanent by accident.

Format: Status, Date, Context, Decision, Consequences, Revisit when.

| ADR | Decision |
|---|---|
| [0001](0001-template-distribution.md) | Distribute as a template with a copying installer, not a CLI package |
| [0002](0002-python-stdlib-only.md) | Implement in Python, standard library only |
| [0003](0003-thin-fail-closed-enforcement.md) | Keep mechanical enforcement thin and fail-closed; excluded machinery |
| [0004](0004-understanding-gate-and-ledger.md) | Gate connected understanding, not retrieval; persistent understanding ledger |
| [0005](0005-canonical-layer-and-subtraction.md) | One canonical layer per concern; rule metadata; mandatory subtraction |
| [0006](0006-self-contained-skills.md) | Skills are self-contained; the confirmation interview is decision-focused |

The narrative these decisions were extracted from — what the origin project
taught — is in [../DESIGN.md](../DESIGN.md).
