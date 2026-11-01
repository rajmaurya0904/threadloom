"""Tests for threadloom.aggregate."""

from datetime import UTC, datetime

from threadloom.aggregate import (
    Filters,
    apply_filters,
    flatten,
    is_bot,
    keep,
    pending_changes,
    reviewer_counts,
)
from threadloom.models import Comment, PRRef, PullRequest


def c(id: int, author: str = "a", day: int = 1, kind: str = "inline", **kw) -> Comment:
    return Comment(id, author, f"body {id}", datetime(2024, 1, day, tzinfo=UTC), kind=kind, **kw)


def pr(n: int, comments: list[Comment]) -> PullRequest:
    return PullRequest(PRRef("o", "r", n), title=f"PR {n}", comments=comments)


def test_is_bot() -> None:
    assert is_bot("dependabot[bot]")
    assert not is_bot("alice")


def test_keep_since() -> None:
    flt = Filters(since=datetime(2024, 1, 5, tzinfo=UTC))
    assert not keep(c(1, day=2), flt)
    assert keep(c(2, day=9), flt)


def test_keep_author_filters_case_insensitive() -> None:
    assert keep(c(1, "Alice"), Filters(authors={"alice"}))
    assert not keep(c(1, "bob"), Filters(authors={"alice"}))
    assert not keep(c(1, "Bob"), Filters(exclude_authors={"bob"}))


def test_keep_kind_filter() -> None:
    assert not keep(c(1, kind="issue"), Filters(kinds={"inline"}))


def test_keep_skip_bots() -> None:
    assert not keep(c(1, "ci[bot]"), Filters(skip_bots=True))
    assert keep(c(1, "ci[bot]"), Filters())


def test_apply_filters_sorts_and_does_not_mutate() -> None:
    original = pr(1, [c(2, day=5), c(1, day=2)])
    out = apply_filters([original], Filters())
    assert [x.id for x in out[0].comments] == [1, 2]
    assert [x.id for x in original.comments] == [2, 1]


def test_apply_filters_keeps_empty_prs() -> None:
    out = apply_filters([pr(1, [c(1, "bot[bot]")])], Filters(skip_bots=True))
    assert len(out) == 1 and out[0].comments == []


def test_flatten_orders_across_prs() -> None:
    prs = [pr(1, [c(1, day=3)]), pr(2, [c(2, day=1)])]
    assert [cm.id for _, cm in flatten(prs)] == [2, 1]


def test_reviewer_counts_sorted() -> None:
    prs = [pr(1, [c(1, "b"), c(2, "a"), c(3, "a")]), pr(2, [c(4, "c"), c(5, "b")])]
    assert list(reviewer_counts(prs).items()) == [("a", 2), ("b", 2), ("c", 1)]


def test_pending_changes_uses_latest_review() -> None:
    comments = [
        c(1, "x", day=1, kind="review", state="CHANGES_REQUESTED"),
        c(2, "y", day=1, kind="review", state="CHANGES_REQUESTED"),
        c(3, "y", day=2, kind="review", state="APPROVED"),
    ]
    assert pending_changes(pr(1, comments)) == ["x"]
