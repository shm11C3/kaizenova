# Claude Code Guidance

This repository's canonical guidance lives in `AGENTS.md`. Load it directly:

@AGENTS.md

The required task workflow, safety invariants, and definition of done in
`AGENTS.md` apply identically under Claude Code.

## Claude-specific bridges

- Repeatable workflows are available as Claude skills under `.claude/skills/`,
  which are symlinks to the canonical skills in `.agents/skills/`.
- Lifecycle enforcement uses `.claude/settings.json` hooks that call
  `.claude/hooks/task_cycle_hook.py`. The decision logic is shared with the
  Codex hook through `scripts/task_cycle_core.py`.
- Command approval is expressed as Claude permissions in
  `.claude/settings.json` and mirrors the Codex rules in
  `.codex/rules/default.rules`.

Do not maintain separate guidance for Claude. Edit `AGENTS.md` and the
canonical documents it routes to; this file only bridges them into Claude Code.
