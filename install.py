#!/usr/bin/env python3
"""Install the kaizenova task-cycle harness into a target repository.

Copies the contents of ``template/`` into the target, then bridges each
canonical skill in ``.agents/skills/`` into ``.claude/skills/`` — a relative
symlink where the platform supports it, a directory copy otherwise (Windows
without developer mode). The bridges are generated here rather than stored in
the template because git materializes committed symlinks as plain text files
on Windows checkouts.

Existing files are never overwritten; conflicts are reported so the owner can
merge by hand. The installer is intentionally dumb: the template is the source
of truth, and an upgrade is a re-run plus a review of the reported conflicts.
"""

from __future__ import annotations

import argparse
import os
import shutil
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
    return sorted(entries)


def bridge_skills(target: Path) -> tuple[list[str], list[str], bool]:
    """Make each canonical skill reachable at ``.claude/skills/<name>``."""

    linked: list[str] = []
    skipped: list[str] = []
    copied_any = False
    skills_root = target / ".agents" / "skills"
    link_dir = target / ".claude" / "skills"
    if not skills_root.is_dir():
        return linked, skipped, copied_any
    link_dir.mkdir(parents=True, exist_ok=True)
    for skill in sorted(path for path in skills_root.iterdir() if path.is_dir()):
        destination = link_dir / skill.name
        if destination.exists() or destination.is_symlink():
            skipped.append(f".claude/skills/{skill.name}")
            continue
        relative_source = Path("..") / ".." / ".agents" / "skills" / skill.name
        try:
            os.symlink(relative_source, destination, target_is_directory=True)
        except OSError:
            shutil.copytree(skill, destination)
            copied_any = True
        linked.append(f".claude/skills/{skill.name}")
    return linked, skipped, copied_any


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

    linked, links_skipped, links_copied = bridge_skills(target)

    for path in copied:
        print(f"installed {path}")
    for entry in linked:
        print(f"installed {entry}")
    all_skipped = [str(path) for path in skipped] + links_skipped
    if all_skipped:
        print("\nleft in place (already exist — merge by hand if upgrading):")
        for entry in all_skipped:
            print(f"  {entry}")
    if links_copied:
        print(
            "\nnote: symlinks are unavailable here, so .claude/skills entries are\n"
            "copies. After editing a skill in .agents/skills, delete its copy under\n"
            ".claude/skills and re-run this installer to refresh it."
        )

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
