# kaizenova Repository Guidance

This repository is the tool itself. `template/` is the product: `install.py`
copies it verbatim into target repositories. Everything else exists to design,
test, and explain that template. Guidance for repositories that *use*
kaizenova lives in `template/AGENTS.md`, not here.

## Decisions Are Recorded, Not Remembered

`docs/adr/` holds every design decision with its trigger evidence and revisit
conditions; `docs/DESIGN.md` is the narrative and index. Before changing
behavior a decision covers, read its ADR. Changing a decided behavior means
amending that ADR (or adding one) in the same change, stating the new evidence
and the new revisit condition — no silent reversals.

No new mechanism, rule, or dependency without an observed trigger. A
hypothesis is not a trigger. This repository holds itself to the same
standard its template imposes on users (ADR 0005): every addition names what
observation would remove it, and a rule that stops earning its keep is
removed with the same rigor that added it.

## Invariants

- Standard library only; no third-party dependency, no build step (ADR 0002).
- Codex and Claude Code share `template/scripts/task_cycle_core.py`. Adapters
  own only provider I/O; never fork workflow logic per provider.
- One canonical layer per concern: skills are the procedure, the template
  `AGENTS.md` only routes to them, `ENFORCEMENT.md` only documents hook
  behavior. Never restate one layer's content in another.
- Relaxing or removing a fail-closed hook behavior requires a recorded
  decision (`template/docs/agents/ENFORCEMENT.md`).
- Template code runs on macOS, Linux, and Windows; CI enforces the matrix.
  No committed symlinks in `template/` — the installer generates the
  `.claude/skills` bridges.

## Working Rules

- Run `python3 tests/check_task_cycle.py` before every commit. Keep the tests
  framework-free.
- `README.md` and `README.ja.md` state the same facts. Editing one means
  editing the other in the same change. `README.ja.md` uses です・ます調.
- Commit in semantic units: one meaning per commit, and the message explains
  why, not what.
- `/.claude/` is session-local and gitignored; never commit it.
- Repository text is English, except `README.ja.md`. Match the user's
  language in chat.
