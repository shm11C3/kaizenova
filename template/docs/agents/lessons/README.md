# Lessons

Evidence-backed, reusable lessons promoted from task retrospectives. A lesson
preserves evidence that is useful across tasks but is not itself mechanical
enforcement.

Format: one Markdown file per lesson. Optional header lines used by
`scripts/find_relevant_lessons.py`:

- `Triggers:` comma-separated terms that should surface this lesson.
- `Applies-to:` comma-separated repository paths this lesson scopes to.

Do not load this directory wholesale at task start. Retrieve bounded evidence
with `find_relevant_lessons.py` when recurrence or precedent affects a
decision.
