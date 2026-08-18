# ADR 0007: Repository self-guidance and its working rules

- Status: Accepted
- Date: 2026-08-19

## Context

The tool repository had no guidance governing work on kaizenova itself, and
the founding sessions produced observable failures that guidance would have
prevented. A root `AGENTS.md` (imported by `CLAUDE.md`) now carries that
guidance. Its invariants section introduces no new rules — it routes to
decisions already recorded with their triggers (ADR 0002, 0003, 0005) — but
its working rules are new, and this repository's own discipline (ADR 0005)
requires each to record an observed trigger and a removal condition.

## Decision

Adopt the root guidance with the following working rules. Each rule's trigger
was observed in the founding sessions; each carries the condition that would
remove it.

| Rule | Observed trigger | Removal condition |
|---|---|---|
| Run `tests/check_task_cycle.py` before every commit | The Windows lock and installer rewrites landed before CI existed; the local suite was the only validation that ran before those commits | The suite outgrows a quick local run, or a mechanical pre-commit gate makes the manual run redundant — then scope to the changed surface |
| `README.md` and `README.ja.md` state the same facts, edited in the same change | PR #1 exists because `README.ja.md` had drifted behind `README.md` | `README.ja.md` is retired or generated from `README.md` |
| Commit in semantic units, message explains why | Owner correction after three unrelated changes (understanding ledger, interview narrowing, MIT license) landed as one commit; history was rewritten to split them | The repository adopts squash-merge-only practice where the PR, not the commit, is the reviewed unit |
| Never commit `/.claude/` | A session worktree under `.claude/worktrees/` was staged by a broad `git add -A` and committed as an embedded repository; two commits had to be redone | Agent sessions stop writing session state into the repository, making the ignore rule dead |
| Everything public is English, including commit messages, Issues, and PRs | This guidance's own pull request was first described in Japanese out of chat habit and corrected by the owner | The project adopts a different public-language policy by recorded decision |
| Changing a decided behavior amends its ADR in the same change | The grill-me attribution error had to be hunted across the READMEs, `DESIGN.md`, and ADR 0006; decisions whose record lags their change repeat this cost for every future correction | Never, while ADRs remain the decision record; retiring the ADR practice itself would need its own recorded decision |

## Consequences

- The subtraction review this guidance demands is now possible: a maintainer
  can test each rule against its trigger and strike it when its removal
  condition holds.
- `AGENTS.md` stays short by carrying only the rules; this ADR carries their
  evidence.

## Revisit when

A removal condition in the table holds, or a working rule accumulates
exceptions in practice — either is evidence the rule no longer matches how
the repository is actually maintained.
