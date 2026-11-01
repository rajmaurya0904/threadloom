"""Minimal GitHub REST client with pagination and retry."""

from __future__ import annotations

import time
from collections.abc import Iterator
from datetime import datetime
from typing import Any

import requests

from threadloom import config
from threadloom.models import Comment, PRRef, PullRequest


class GitHubError(RuntimeError):
    """Raised when the GitHub API returns an error."""


def parse_time(value: str) -> datetime:
    """Parse a GitHub ISO-8601 timestamp (``2024-01-02T03:04:05Z``)."""
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class GitHubClient:
    """Thin wrapper over the GitHub REST API."""

    def __init__(
        self,
        token: str | None = None,
        api_url: str | None = None,
        per_page: int | None = None,
        session: requests.Session | None = None,
        max_retries: int = 3,
        backoff: float = 1.0,
    ) -> None:
        self.api_url = (api_url or config.get_github_api_url()).rstrip("/")
        self.per_page = per_page or config.get_github_per_page()
        self.max_retries = max_retries
        self.backoff = backoff
        self.session = session or requests.Session()
        self.session.headers["Accept"] = "application/vnd.github+json"
        self.session.headers["User-Agent"] = "threadloom"
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"

    def _get(self, url: str, params: dict[str, Any] | None = None) -> requests.Response:
        for attempt in range(self.max_retries + 1):
            resp = self.session.get(url, params=params, timeout=30)
            if resp.status_code in (429, 502, 503, 504) and attempt < self.max_retries:
                time.sleep(self._delay(resp, attempt))
                continue
            if resp.status_code == 403 and resp.headers.get("X-RateLimit-Remaining") == "0":
                raise GitHubError(
                    "GitHub rate limit exceeded; set GITHUB_TOKEN or pass --token"
                )
            if resp.status_code == 404:
                raise GitHubError(f"not found: {url}")
            if resp.status_code == 401:
                raise GitHubError("bad credentials: check GITHUB_TOKEN")
            if resp.status_code >= 400:
                raise GitHubError(f"GitHub API error {resp.status_code} for {url}")
            return resp
        raise GitHubError(f"giving up on {url}")  # pragma: no cover

    def _delay(self, resp: requests.Response, attempt: int) -> float:
        retry_after = resp.headers.get("Retry-After")
        if retry_after and retry_after.isdigit():
            return float(retry_after)
        return self.backoff * (2**attempt)

    def _paginate(self, path: str) -> Iterator[dict[str, Any]]:
        url: str | None = f"{self.api_url}{path}"
        params: dict[str, Any] | None = {"per_page": self.per_page}
        while url:
            resp = self._get(url, params)
            yield from resp.json()
            url = resp.links.get("next", {}).get("url")
            params = None

    def get_pull_request(self, ref: PRRef) -> PullRequest:
        """Fetch PR metadata and all of its comments."""
        base = f"/repos/{ref.owner}/{ref.repo}"
        data = self._get(f"{self.api_url}{base}/pulls/{ref.number}").json()
        state = "merged" if data.get("merged_at") else data.get("state", "open")
        pr = PullRequest(
            ref=ref,
            title=data.get("title", ""),
            state=state,
            author=(data.get("user") or {}).get("login", ""),
        )
        for raw in self._paginate(f"{base}/pulls/{ref.number}/comments"):
            pr.comments.append(_inline_comment(raw))
        for raw in self._paginate(f"{base}/pulls/{ref.number}/reviews"):
            if raw.get("body") and raw.get("submitted_at"):
                pr.comments.append(_review_comment(raw))
        for raw in self._paginate(f"{base}/issues/{ref.number}/comments"):
            pr.comments.append(_issue_comment(raw))
        return pr


def _login(raw: dict[str, Any]) -> str:
    return (raw.get("user") or {}).get("login") or "ghost"


def _inline_comment(raw: dict[str, Any]) -> Comment:
    return Comment(
        id=raw["id"],
        author=_login(raw),
        body=raw.get("body") or "",
        created_at=parse_time(raw["created_at"]),
        kind="inline",
        path=raw.get("path"),
        line=raw.get("line") or raw.get("original_line"),
        url=raw.get("html_url", ""),
        in_reply_to=raw.get("in_reply_to_id"),
    )


def _review_comment(raw: dict[str, Any]) -> Comment:
    return Comment(
        id=raw["id"],
        author=_login(raw),
        body=raw["body"],
        created_at=parse_time(raw["submitted_at"]),
        kind="review",
        url=raw.get("html_url", ""),
        state=raw.get("state"),
    )


def _issue_comment(raw: dict[str, Any]) -> Comment:
    return Comment(
        id=raw["id"],
        author=_login(raw),
        body=raw.get("body") or "",
        created_at=parse_time(raw["created_at"]),
        kind="issue",
        url=raw.get("html_url", ""),
    )
