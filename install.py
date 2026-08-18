#!/usr/bin/env python3
"""Install the kaizenova task-cycle harness into a target repository.

Copies the contents of ``template/`` into the target, preserving symlinks
(``.claude/skills/*`` link to the canonical ``.agents/skills/*``). Existing
files are never overwritten; conflicts are reported so the owner can merge by
hand. The installer is intentionally dumb: the template is the source of
truth, and an upgrade is a re-run plus a review of the reported conflicts.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent / "template"
MINIMUM_PYTHON = (3, 11)


def iter_template_files() -> list[Path]:
    entries: list[Path] = []
    for directory, dirnames, filenames in os.walk(TEMPLATE, followlinks=False):
        if "__pycache__" in dirnames:
            dirnames.remove("__pycache__")
        base = Path(directory)
        entries.extend(
            base / name for name in filenames if not name.endswith(".pyc")
        )
        # Symlinked directories (.claude/skills/*) appear in dirnames but are
        # not descended into; copy them as links rather than as trees.
        entries.extend(
            base / name for name in dirnames if (base / name).is_symlink()
        )
    return sorted(entries)


def install(target: Path) -> int:
    if not (target / ".git").exists():
        print(f"error: {target} is not a git repository root", file=sys.stderr)
        return 1

    copied: list[Path] = []
    skipped: list[Path] = []
    for source in iter_template_files():
        relative = source.relative_to(TEMPLATE)
        destination = target / relative
        if destination.exists() or destination.is_symlink():
            skipped.append(relative)
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        if source.is_symlink():
            os.symlink(os.readlink(source), destination)
        else:
            destination.write_bytes(source.read_bytes())
            destination.chmod(source.stat().st_mode)
        copied.append(relative)

    for path in copied:
        print(f"installed {path}")
    if skipped:
        print("\nleft in place (already exist — merge by hand if upgrading):")
        for path in skipped:
            print(f"  {path}")

    print(
        "\nnext steps:\n"
        "  1. Edit AGENTS.md: fill in every EDIT ME placeholder\n"
        "     (mission, sources of truth, validation stage, language rule).\n"
        "  2. Confirm `python3 --version` is "
        f"{MINIMUM_PYTHON[0]}.{MINIMUM_PYTHON[1]}+ for the hooks.\n"
        "  3. Commit the installed files.\n"
        "  4. Start a task: python3 scripts/task_cycle.py start --task <id> --title '<t>'"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", type=Path, help="Target repository root")
    args = parser.parse_args()
    target = args.target.resolve()
    if not target.is_dir():
        print(f"error: {target} is not a directory", file=sys.stderr)
        return 1
    try:
        toplevel = subprocess.run(
            ["git", "-C", str(target), "rev-parse", "--show-toplevel"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        print(f"error: {target} is not inside a git repository", file=sys.stderr)
        return 1
    if Path(toplevel).resolve() != target:
        print(
            f"error: {target} is not the repository root ({toplevel})",
            file=sys.stderr,
        )
        return 1
    return install(target)


if __name__ == "__main__":
    raise SystemExit(main())
