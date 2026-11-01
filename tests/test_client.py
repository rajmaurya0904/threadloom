"""Tests for threadloom.client using a fake HTTP session."""

from __future__ import annotations

from typing import Any

import pytest

from threadloom.client import GitHubClient, GitHubError, parse_time
from threadloom.models import PRRef


class FakeResponse:
    def __init__(
        self,
        payload: Any = None,
        status: int = 200,
        headers: dict[str, str] | None = None,
        links: dict[str, dict[str, str]] | None = None,
    ) -> None:
        self.payload = payload
        self.status_code = status
        self.headers = headers or {}
        self.links = links or {}

    def json(self) -> Any:
        return self.payload


class FakeSession:
    def __init__(self, routes: dict[str, list[FakeResponse]]) -> None:
        self.routes = routes
        self.headers: dict[str, str] = {}
        self.calls: list[str] = []

    def get(self, url: str, params: Any = None, timeout: int = 0) -> FakeResponse:
        self.calls.append(url)
        queue = self.routes[url]
        return queue.pop(0) if len(queue) > 1 else queue[0]


API = "https://api.test"
REF = PRRef("o", "r", 5)


def make(routes: dict[str, list[FakeResponse]]) -> tuple[GitHubClient, FakeSession]:
    session = FakeSession(routes)
    client = GitHubClient(api_url=API, per_page=2, session=session, backoff=0)  # type: ignore[arg-type]
    return client, session


def user(name: str) -> dict[str, str]:
    return {"login": name}


def base_routes() -> dict[str, list[FakeResponse]]:
    pr = "/repos/o/r/pulls/5"
    return {
        f"{API}{pr}": [FakeResponse({"title": "T", "state": "open", "user": user("alice")})],
        f"{API}{pr}/comments": [
            FakeResponse(
                [
                    {
                        "id": 1,
                        "user": user("bob"),
                        "body": "nit",
                        "created_at": "2024-01-02T00:00:00Z",
                        "path": "a.py",
                        "line": 10,
                        "html_url": "u1",
                    }
                ]
            )
        ],
        f"{API}{pr}/reviews": [
            FakeResponse(
                [
                    {
                        "id": 2,
                        "user": user("carol"),
                        "body": "LGTM",
                        "submitted_at": "2024-01-03T00:00:00Z",
                        "state": "APPROVED",
                    },
                    {
                        "id": 3,
                        "user": user("x"),
                        "body": "",
                        "submitted_at": "2024-01-04T00:00:00Z",
                    },
                ]
            )
        ],
        f"{API}/repos/o/r/issues/5/comments": [
            FakeResponse(
                [{"id": 4, "user": None, "body": "bot", "created_at": "2024-01-01T00:00:00Z"}]
            )
        ],
    }


def test_parse_time() -> None:
    assert parse_time("2024-01-02T03:04:05Z").year == 2024


def test_get_pull_request_collects_all_kinds() -> None:
    client, _ = make(base_routes())
    pr = client.get_pull_request(REF)
    assert pr.title == "T" and pr.author == "alice"
    kinds = sorted(c.kind for c in pr.comments)
    assert kinds == ["inline", "issue", "review"]


def test_empty_review_body_skipped() -> None:
    client, _ = make(base_routes())
    pr = client.get_pull_request(REF)
    assert all(c.id != 3 for c in pr.comments)


def test_deleted_user_becomes_ghost() -> None:
    client, _ = make(base_routes())
    pr = client.get_pull_request(REF)
    assert next(c for c in pr.comments if c.id == 4).author == "ghost"


def test_inline_fields_mapped() -> None:
    client, _ = make(base_routes())
    c = next(c for c in client.get_pull_request(REF).comments if c.id == 1)
    assert (c.path, c.line, c.url) == ("a.py", 10, "u1")


def test_review_state_mapped() -> None:
    client, _ = make(base_routes())
    c = next(c for c in client.get_pull_request(REF).comments if c.id == 2)
    assert c.state == "APPROVED"


def test_merged_state() -> None:
    routes = base_routes()
    routes[f"{API}/repos/o/r/pulls/5"] = [
        FakeResponse({"title": "T", "state": "closed", "merged_at": "2024-01-01T00:00:00Z"})
    ]
    client, _ = make(routes)
    assert client.get_pull_request(REF).state == "merged"


def test_pagination_follows_next_link() -> None:
    routes = base_routes()
    key = f"{API}/repos/o/r/pulls/5/comments"
    page2 = "https://api.test/page2"
    routes[key] = [
        FakeResponse(
            [{"id": 10, "user": user("a"), "body": "x", "created_at": "2024-01-01T00:00:00Z"}],
            links={"next": {"url": page2}},
        )
    ]
    routes[page2] = [
        FakeResponse(
            [{"id": 11, "user": user("a"), "body": "y", "created_at": "2024-01-02T00:00:00Z"}]
        )
    ]
    client, session = make(routes)
    pr = client.get_pull_request(REF)
    assert {10, 11} <= {c.id for c in pr.comments}
    assert page2 in session.calls


def test_retry_on_503_then_success() -> None:
    routes = base_routes()
    key = f"{API}/repos/o/r/pulls/5"
    routes[key] = [FakeResponse(status=503), FakeResponse({"title": "OK"})]
    client, session = make(routes)
    assert client.get_pull_request(REF).title == "OK"
    assert session.calls.count(key) == 2


def test_404_raises() -> None:
    routes = base_routes()
    routes[f"{API}/repos/o/r/pulls/5"] = [FakeResponse(status=404)]
    client, _ = make(routes)
    with pytest.raises(GitHubError, match="not found"):
        client.get_pull_request(REF)


def test_rate_limit_message() -> None:
    routes = base_routes()
    routes[f"{API}/repos/o/r/pulls/5"] = [
        FakeResponse(status=403, headers={"X-RateLimit-Remaining": "0"})
    ]
    client, _ = make(routes)
    with pytest.raises(GitHubError, match="rate limit"):
        client.get_pull_request(REF)


def test_401_raises() -> None:
    routes = base_routes()
    routes[f"{API}/repos/o/r/pulls/5"] = [FakeResponse(status=401)]
    client, _ = make(routes)
    with pytest.raises(GitHubError, match="credentials"):
        client.get_pull_request(REF)


def test_token_sets_auth_header() -> None:
    session = FakeSession({})
    GitHubClient(token="abc", api_url=API, session=session)  # type: ignore[arg-type]
    assert session.headers["Authorization"] == "Bearer abc"
