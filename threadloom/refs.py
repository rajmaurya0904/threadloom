"""Parse pull request references from user input."""

from __future__ import annotations

import re

from threadloom.models import PRRef

_URL_RE = re.compile(
    r"^(?:https?://)?(?:www\.)?github\.com/(?P<owner>[\w.-]+)/(?P<repo>[\w.-]+)/pull/(?P<num>\d+)"
    r"(?:[/?#].*)?$"
)
_SHORT_RE = re.compile(r"^(?P<owner>[\w.-]+)/(?P<repo>[\w.-]+)#(?P<num>\d+)$")


class RefError(ValueError):
    """Raised when a pull request reference cannot be parsed."""


def parse_ref(text: str, default_repo: str | None = None) -> PRRef:
    """Parse ``owner/repo#123``, a PR URL, or ``#123`` / ``123`` with ``default_repo``."""
    text = text.strip()
    for pattern in (_URL_RE, _SHORT_RE):
        m = pattern.match(text)
        if m:
            return PRRef(m["owner"], m["repo"], int(m["num"]))
    bare = re.fullmatch(r"#?(\d+)", text)
    if bare:
        if not default_repo or "/" not in default_repo:
            raise RefError(f"{text!r} needs --repo owner/name to resolve")
        owner, repo = default_repo.split("/", 1)
        return PRRef(owner, repo, int(bare.group(1)))
    raise RefError(f"cannot parse pull request reference: {text!r}")


def parse_refs(items: list[str], default_repo: str | None = None) -> list[PRRef]:
    """Parse many references, dropping duplicates while keeping order."""
    seen: set[PRRef] = set()
    out: list[PRRef] = []
    for item in items:
        ref = parse_ref(item, default_repo)
        if ref not in seen:
            seen.add(ref)
            out.append(ref)
    return out
