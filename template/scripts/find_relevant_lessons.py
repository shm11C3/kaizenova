#!/usr/bin/env python3
"""Return a bounded, deterministic set of relevant repository lessons."""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

DEFAULT_LIMIT = 5
MAX_LIMIT = 10
EXCERPT_LIMIT = 280
WORD = re.compile(
    r"[A-Za-z0-9][A-Za-z0-9_.:/-]*|[\u3040-\u30ff\u3400-\u9fffー]+"
)
SKIPPED_NAMES = frozenset({"README.md", "TEMPLATE.md"})


@dataclass(frozen=True)
class Match:
    path: str
    kind: str
    score: int
    matched_terms: tuple[str, ...]
    matched_paths: tuple[str, ...]
    excerpt: str


def terms(text: str) -> set[str]:
    return {term.lower() for term in WORD.findall(text) if len(term) >= 2}


def sources(root: Path) -> Iterable[tuple[Path, str, str]]:
    root = root.resolve()
    locations = (
        (root / "docs/agents/lessons", "lesson"),
        (root / "docs/agents/retrospectives", "retrospective"),
    )
    for directory, kind in locations:
        try:
            resolved_directory = directory.resolve(strict=True)
            resolved_directory.relative_to(root)
            if directory.is_symlink():
                continue
            directory_fd = os.open(
                directory,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
            )
        except (FileNotFoundError, NotADirectoryError, OSError, ValueError):
            continue
        try:
            for name in sorted(os.listdir(directory_fd)):
                if not name.endswith(".md") or name in SKIPPED_NAMES:
                    continue
                try:
                    source_fd = os.open(
                        name,
                        os.O_RDONLY | os.O_NOFOLLOW,
                        dir_fd=directory_fd,
                    )
                except OSError:
                    continue
                try:
                    if not stat.S_ISREG(os.fstat(source_fd).st_mode):
                        continue
                    with os.fdopen(source_fd, encoding="utf-8") as source:
                        source_fd = -1
                        text = source.read()
                except (OSError, UnicodeError):
                    continue
                finally:
                    if source_fd >= 0:
                        os.close(source_fd)
                yield directory / name, kind, text
        finally:
            os.close(directory_fd)


def bounded_excerpt(text: str, matched: set[str]) -> str:
    paragraphs = [
        " ".join(part.split())
        for part in re.split(r"\n\s*\n", text)
        if part.strip()
    ]
    selected = next(
        (
            paragraph
            for paragraph in paragraphs
            if matched & terms(paragraph)
        ),
        paragraphs[0] if paragraphs else "",
    )
    if len(selected) <= EXCERPT_LIMIT:
        return selected
    return selected[: EXCERPT_LIMIT - 1].rstrip() + "…"


def declared_scopes(text: str) -> tuple[str, ...]:
    values: list[str] = []
    for line in text.splitlines():
        if not line.lower().startswith("applies-to:"):
            continue
        values.extend(
            value.strip().removeprefix("./")
            for value in line.split(":", 1)[1].split(",")
            if value.strip()
        )
    return tuple(values)


def path_matches(target: str, scope: str) -> bool:
    target = target.replace("\\", "/").removeprefix("./")
    scope = scope.replace("\\", "/").removeprefix("./")
    return target == scope or target.startswith(scope.rstrip("/") + "/")


def rank(root: Path, query: str, target_paths: tuple[str, ...]) -> list[Match]:
    query_terms = terms(query)
    matches: list[Match] = []
    for path, kind, text in sources(root):
        matched = query_terms & terms(text)
        if not matched:
            continue
        title = text.splitlines()[0] if text.splitlines() else ""
        title_terms = terms(title)
        trigger_lines = "\n".join(
            line for line in text.splitlines() if line.lower().startswith("triggers:")
        )
        trigger_terms = terms(trigger_lines)
        matched_paths = tuple(
            sorted(
                target
                for target in target_paths
                if any(path_matches(target, scope) for scope in declared_scopes(text))
            )
        )
        score = len(matched)
        score += 4 * len(matched & title_terms)
        score += 3 * len(matched & trigger_terms)
        score += 5 * len(matched_paths)
        if kind == "lesson":
            score += 2
        matches.append(
            Match(
                path=str(path.relative_to(root)),
                kind=kind,
                score=score,
                matched_terms=tuple(sorted(matched)),
                matched_paths=matched_paths,
                excerpt=bounded_excerpt(text, matched),
            )
        )
    return sorted(matches, key=lambda item: (-item.score, item.path))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root. Defaults to the root containing this script.",
    )
    query_source = parser.add_mutually_exclusive_group(required=True)
    query_source.add_argument("--query", help="Trusted task or concept terms.")
    query_source.add_argument(
        "--query-file",
        type=Path,
        help="File containing exact review, error, or other untrusted text.",
    )
    parser.add_argument(
        "--path",
        action="append",
        default=[],
        help="Target path used to rank lessons with a matching Applies-to scope.",
    )
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not 1 <= args.limit <= MAX_LIMIT:
        raise SystemExit(f"--limit must be between 1 and {MAX_LIMIT}")
    query = (
        args.query_file.read_text(encoding="utf-8", errors="replace")
        if args.query_file is not None
        else args.query
    )
    payload = [
        {
            "path": match.path,
            "kind": match.kind,
            "score": match.score,
            "matchedTerms": list(match.matched_terms),
            "matchedPaths": list(match.matched_paths),
            "excerpt": match.excerpt,
        }
        for match in rank(args.root.resolve(), query, tuple(args.path))[: args.limit]
    ]
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
