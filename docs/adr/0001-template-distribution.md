# ADR 0001: Distribute as a template with a copying installer

- Status: Accepted (owner decision, reaffirmed against CLI packaging 2026-08-19)
- Date: 2026-08-19

## Context

The harness consists of skills (`SKILL.md`), provider configuration
(`.claude/settings.json`, `.codex/`), and Python scripts. Both Claude Code and
Codex read skills and hook configuration from files inside the target
repository; that half of the harness must be vendored no matter how the rest
is distributed.

The tool's core value is mechanical enforcement that cannot silently vanish.
At the time of the decision the tool has one maintainer and a handful of
installs, so fix propagation across many installations is not yet a live
concern.

## Decision

Distribute the whole harness as a template: `install.py` copies `template/`
into the target repository, never overwrites existing files, and reports
conflicts for manual merge. Upgrading is re-running the installer and merging
the reported conflicts by hand.

## Alternatives considered

- **CLI package (PyPI or a Go binary).** Rejected for now. Hook entries would
  reference a globally installed command, so any machine without the tool —
  a new contributor, CI, another workstation — silently loses enforcement:
  a missing hook command does not block the turn. Preventing that requires
  version-pin files and install checks, which is the compatibility machinery
  ADR 0003 deliberately excludes. Packaging also only moves the ~1,100 Python
  lines; skills and provider config stay vendored, leaving two update
  channels and a new skill-versus-CLI version-skew failure mode.
- **Claude Code plugin.** Codex still needs repository files, so the plugin
  would be a second distribution channel, not a replacement.
- **`uvx` pinned invocation** (`uvx kaizenova==X.Y hook claude`). Propagates
  fixes while pinning versions, but makes every environment depend on `uv`
  plus first-run network access, and an offline fetch failure degrades to
  fail-open with noise.

## Consequences

- A cloned target repository is self-contained: enforcement works with no
  installation step beyond `python3`.
- Vendored source is auditable by the repository owner and readable by the
  agent it constrains.
- Fixes do not propagate automatically; installed copies can drift from
  upstream. Drift is also what allows per-repository tuning of tunable
  behaviors.
- The implementation language must suit vendored interpreted source
  (ADR 0002).

## Revisit when

Any of: external users are established; rolling a fix out across multiple
repositories has been painful at least twice; a fix appears that must
propagate (security-grade). If reopened, revisit ADR 0002 in the same
decision — a CLI package makes a Go single binary the strongest candidate.
