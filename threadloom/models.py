"""Data models for pull requests and review comments."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class PRRef:
    """A reference to a single pull request."""

    owner: str
    repo: str
    number: int

    @property
    def slug(self) -> str:
        return f"{self.owner}/{self.repo}#{self.number}"

    @property
    def url(self) -> str:
        return f"https://github.com/{self.owner}/{self.repo}/pull/{self.number}"


@dataclass(frozen=True)
class Comment:
    """A single review comment (inline, review summary, or conversation comment)."""

    id: int
    author: str
    body: str
    created_at: datetime
    kind: str = "inline"  # inline | review | issue
    path: str | None = None
    line: int | None = None
    url: str = ""
    in_reply_to: int | None = None
    state: str | None = None  # review state, e.g. APPROVED, CHANGES_REQUESTED


@dataclass
class PullRequest:
    """A pull request together with its collected comments."""

    ref: PRRef
    title: str = ""
    state: str = "open"
    author: str = ""
    comments: list[Comment] = field(default_factory=list)
