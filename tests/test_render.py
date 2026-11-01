"""Tests for threadloom.render."""

from datetime import UTC, datetime

from threadloom.models import Comment, PRRef, PullRequest
from threadloom.render import fmt_time, render_comment, render_summary

NOW = datetime(2024, 2, 1, 12, 0, tzinfo=UTC)


def comment(id: int = 1, body: str = "hi", **kw) -> Comment:
    kw.setdefault("kind", "inline")
    return Comment(id, "alice", body, datetime(2024, 1, 2, 3, 4, tzinfo=UTC), **kw)


def make_pr(*comments: Comment, n: int = 1) -> PullRequest:
    return PullRequest(
        PRRef("o", "r", n), title="Fix", state="open", author="bob", comments=list(comments)
    )


def test_fmt_time_is_utc() -> None:
    assert fmt_time(datetime(2024, 1, 2, 3, 4, tzinfo=UTC)) == "2024-01-02 03:04"


def test_render_comment_quotes_multiline() -> None:
    text = render_comment(comment(body="a\n\nb"))
    assert "> a" in text and ">\n" in text and "> b" in text


def test_render_comment_truncates() -> None:
    text = render_comment(comment(body="x" * 50), max_chars=10)
    assert "xxxxxxxxxx..." in text and "x" * 11 not in text


def test_render_comment_location_and_link() -> None:
    text = render_comment(comment(path="a.py", line=3, url="http://u"))
    assert "`a.py:3`" in text and "[link](http://u)" in text


def test_render_comment_review_state() -> None:
    text = render_comment(comment(kind="review", state="CHANGES_REQUESTED"))
    assert "changes requested" in text


def test_render_empty_body() -> None:
    assert "(empty)" in render_comment(comment(body="  "))


def test_summary_header_counts() -> None:
    out = render_summary([make_pr(comment(1), comment(2)), make_pr(n=2)], generated_at=NOW)
    assert "2 comments across 2 pull requests" in out
    assert "2024-02-01 12:00" in out


def test_summary_sections_per_pr() -> None:
    out = render_summary([make_pr(comment(), n=7)], generated_at=NOW)
    assert "## [o/r#7](https://github.com/o/r/pull/7) Fix" in out
    assert "State: open - author @bob - 1 comments" in out


def test_summary_empty_pr_message() -> None:
    assert "_No matching comments._" in render_summary([make_pr()], generated_at=NOW)


def test_summary_flat_timeline() -> None:
    late = Comment(2, "z", "late", datetime(2024, 1, 9, tzinfo=UTC), kind="issue")
    out = render_summary(
        [make_pr(late, n=1), make_pr(comment(1), n=2)], flat=True, generated_at=NOW
    )
    assert "## Timeline" in out
    assert out.index("o/r#2") < out.index("o/r#1")


def test_summary_flags_changes_requested() -> None:
    review = comment(kind="review", state="CHANGES_REQUESTED")
    assert "Changes requested by: @alice" in render_summary([make_pr(review)], generated_at=NOW)


def test_summary_ends_with_single_newline() -> None:
    out = render_summary([make_pr(comment())], generated_at=NOW)
    assert out.endswith("\n") and not out.endswith("\n\n")


def test_truncation_closes_open_code_fence() -> None:
    body = "```python\n" + "x = 1\n" * 20 + "```"
    text = render_comment(comment(body=body), max_chars=30)
    assert text.count("```") % 2 == 0
