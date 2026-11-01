"""Filter and order comments collected from pull requests."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from threadloom.models import Comment, PullRequest

KINDS = ("inline", "review", "issue")


@dataclass
class Filters:
    """Which comments to keep."""

    since: datetime | None = None
    authors: set[str] = field(default_factory=set)
    exclude_authors: set[str] = field(default_factory=set)
    kinds: set[str] = field(default_factory=lambda: set(KINDS))
    skip_bots: bool = False


def is_bot(author: str) -> bool:
    """Heuristic: GitHub bot accounts end in ``[bot]``."""
    return author.lower().endswith("[bot]")


def keep(comment: Comment, flt: Filters) -> bool:
    """Return True if ``comment`` passes every filter."""
    author = comment.author.lower()
    if flt.since and comment.created_at < flt.since:
        return False
    if comment.kind not in flt.kinds:
        return False
    if flt.authors and author not in flt.authors:
        return False
    if author in flt.exclude_authors:
        return False
    return not (flt.skip_bots and is_bot(comment.author))


def apply_filters(prs: list[PullRequest], flt: Filters) -> list[PullRequest]:
    """Return copies of ``prs`` holding only matching comments, sorted oldest first."""
    out: list[PullRequest] = []
    for pr in prs:
        kept = sorted(
            (c for c in pr.comments if keep(c, flt)), key=lambda c: (c.created_at, c.id)
        )
        out.append(
            PullRequest(pr.ref, title=pr.title, state=pr.state, author=pr.author, comments=kept)
        )
    return out


def flatten(prs: list[PullRequest]) -> list[tuple[PullRequest, Comment]]:
    """All comments across PRs in one chronological list."""
    pairs = [(pr, c) for pr in prs for c in pr.comments]
    pairs.sort(key=lambda p: (p[1].created_at, p[1].id))
    return pairs


def reviewer_counts(prs: list[PullRequest]) -> dict[str, int]:
    """Comments per author, most active first (ties alphabetical)."""
    counts: dict[str, int] = {}
    for pr in prs:
        for c in pr.comments:
            counts[c.author] = counts.get(c.author, 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: (-kv[1], kv[0].lower())))


def pending_changes(pr: PullRequest) -> list[str]:
    """Reviewers whose latest review state is CHANGES_REQUESTED."""
    latest: dict[str, str] = {}
    for c in sorted(pr.comments, key=lambda c: c.created_at):
        if c.kind == "review" and c.state:
            latest[c.author] = c.state
    return sorted(a for a, s in latest.items() if s == "CHANGES_REQUESTED")
