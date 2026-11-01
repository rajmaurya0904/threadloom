"""Render aggregated pull request comments as markdown."""

from __future__ import annotations

from datetime import UTC, datetime

from threadloom.aggregate import flatten, pending_changes, reviewer_counts
from threadloom.models import Comment, PullRequest

_LABELS = {"inline": "inline", "review": "review", "issue": "comment"}
_STATES = {
    "APPROVED": "approved",
    "CHANGES_REQUESTED": "changes requested",
    "COMMENTED": "commented",
    "DISMISSED": "dismissed",
}


def fmt_time(value: datetime) -> str:
    return value.astimezone(UTC).strftime("%Y-%m-%d %H:%M")


def _quote(body: str, max_chars: int | None) -> str:
    body = body.strip().replace("\r\n", "\n")
    if max_chars and len(body) > max_chars:
        body = body[:max_chars].rstrip() + "..."
    if not body:
        body = "(empty)"
    return "\n".join(f"> {line}" if line else ">" for line in body.split("\n"))


def _heading(comment: Comment) -> str:
    parts = [f"**@{comment.author}**", fmt_time(comment.created_at), _LABELS[comment.kind]]
    if comment.kind == "review" and comment.state:
        parts.append(_STATES.get(comment.state, comment.state.lower()))
    if comment.path:
        loc = f"`{comment.path}:{comment.line}`" if comment.line else f"`{comment.path}`"
        parts.append(loc)
    if comment.in_reply_to:
        parts.append("reply")
    return " - ".join(parts)


def render_comment(comment: Comment, max_chars: int | None = None) -> str:
    text = f"- {_heading(comment)}\n\n{_indent(_quote(comment.body, max_chars))}"
    if comment.url:
        text += f"\n\n  [link]({comment.url})"
    return text


def _indent(block: str) -> str:
    return "\n".join("  " + line for line in block.split("\n"))


def render_summary(
    prs: list[PullRequest],
    flat: bool = False,
    max_chars: int | None = None,
    generated_at: datetime | None = None,
) -> str:
    """Build the full markdown document."""
    total = sum(len(pr.comments) for pr in prs)
    lines = ["# Review comment summary", ""]
    stamp = fmt_time(generated_at or datetime.now(UTC))
    lines.append(f"{total} comments across {len(prs)} pull requests (generated {stamp} UTC).")
    lines.append("")
    counts = reviewer_counts(prs)
    if counts:
        top = ", ".join(f"@{a} ({n})" for a, n in list(counts.items())[:5])
        lines.append(f"Most active: {top}")
        lines.append("")
    if flat:
        lines.append("## Timeline")
        lines.append("")
        for pr, comment in flatten(prs):
            lines.append(f"### {pr.ref.slug}")
            lines.append("")
            lines.append(render_comment(comment, max_chars))
            lines.append("")
    else:
        for pr in prs:
            lines.extend(_render_pr(pr, max_chars))
    return "\n".join(lines).rstrip() + "\n"


def _render_pr(pr: PullRequest, max_chars: int | None) -> list[str]:
    title = f"[{pr.ref.slug}]({pr.ref.url})"
    if pr.title:
        title += f" {pr.title}"
    lines = [f"## {title}", ""]
    meta = f"State: {pr.state}"
    if pr.author:
        meta += f" - author @{pr.author}"
    meta += f" - {len(pr.comments)} comments"
    lines.append(meta)
    blocking = pending_changes(pr)
    if blocking:
        lines.append("")
        lines.append("Changes requested by: " + ", ".join(f"@{a}" for a in blocking))
    lines.append("")
    if not pr.comments:
        lines.append("_No matching comments._")
        lines.append("")
    for comment in pr.comments:
        lines.append(render_comment(comment, max_chars))
        lines.append("")
    return lines
