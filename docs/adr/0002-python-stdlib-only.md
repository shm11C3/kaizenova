# ADR 0002: Implement in Python, standard library only

- Status: Accepted
- Date: 2026-08-19

## Context

ADR 0001 fixes the distribution model: scripts are vendored as source into
target repositories. The hook contract is provider-agnostic — a subprocess
reading JSON on stdin and writing JSON on stdout within a 5–10 second
timeout — so performance is irrelevant, but the runtime must already exist on
the target machine.

Runtime availability on developer machines (macOS/Linux): `python3` is
near-universal (macOS Command Line Tools ship it, and users of coding agents
have CLT for git). Node is not guaranteed on `PATH`: Claude Code's native
installer bundles its runtime privately, and Codex is a Rust binary.

The state machine needs JSON, file operations, argument parsing, and an
advisory file lock. Python's standard library covers all of it, including
`fcntl.flock`. Node's standard library has no file locking; Go compiles,
which conflicts with vendored-source distribution.

## Decision

Python 3.11+, standard library only. No third-party dependency, no build
step, no lockfile.

## Consequences

- Zero-dependency vendored scripts that humans can audit and the constrained
  agent can read to understand its own enforcement.
- Interpreter-version fragmentation is a real Python cost: adapters carry a
  `MINIMUM_PYTHON` guard, duplicated before import so a syntax bump cannot
  crash the check itself. A crashed hook would fail open.
- `fcntl` makes the lock POSIX-only; Windows is unsupported. A portable
  lock-directory scheme (atomic `mkdir`) could lift this in any language if
  Windows support is ever demanded.
- Go and TypeScript were rejected on distribution fit, not on merit: Go needs
  committed binaries or a toolchain at install time; TS needs Node on `PATH`
  plus an execution step, and an external package for locking.

## Revisit when

ADR 0001 is reopened in favor of a CLI package (Go becomes the strongest
candidate: single binary, no interpreter fragmentation), or Windows support
becomes a real requirement (fix the lock mechanism first; the language may
not need to change).
