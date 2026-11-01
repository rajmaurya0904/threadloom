"""Tests for threadloom.cli."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import click
import pytest
from click.testing import CliRunner

from threadloom import cli
from threadloom.client import GitHubError
from threadloom.models import Comment, PRRef, PullRequest


class StubClient:
    last_token: str | None = None

    def __init__(self, token: str | None = None, **_: object) -> None:
        StubClient.last_token = token

    def get_pull_request(self, ref: PRRef) -> PullRequest:
        if ref.number == 404:
            raise GitHubError("not found")
        comments = [
            Comment(1, "alice", "please rename", datetime(2024, 1, 2, tzinfo=UTC), path="a.py"),
            Comment(2, "bot[bot]", "coverage", datetime(2024, 1, 3, tzinfo=UTC), kind="issue"),
        ]
        return PullRequest(ref, title="Title", state="open", author="bob", comments=comments)


@pytest.fixture(autouse=True)
def stub(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli, "GitHubClient", StubClient)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)


def run(*args: str):
    return CliRunner().invoke(cli.main, list(args))


def test_help_lists_options() -> None:
    result = run("--help")
    assert result.exit_code == 0
    assert "--since" in result.output and "--flat" in result.output


def test_version() -> None:
    assert "threadloom, version" in run("--version").output


def test_no_args_is_usage_error() -> None:
    result = run()
    assert result.exit_code == 2 and "at least one" in result.output


def test_bad_ref_is_usage_error() -> None:
    result = run("nonsense")
    assert result.exit_code == 2 and "cannot parse" in result.output


def test_prints_markdown() -> None:
    result = run("o/r#1")
    assert result.exit_code == 0
    assert "please rename" in result.output and "# Review comment summary" in result.output


def test_repo_option_resolves_bare_number() -> None:
    assert "o/r#3" in run("3", "--repo", "o/r").output


def test_no_bots_filters() -> None:
    out = run("o/r#1", "--no-bots").output
    assert "coverage" not in out and "please rename" in out


def test_author_filter_accepts_at_and_commas() -> None:
    out = run("o/r#1", "--author", "@bot[bot],zed").output
    assert "coverage" in out and "please rename" not in out


def test_exclude_author() -> None:
    assert "please rename" not in run("o/r#1", "--exclude-author", "alice").output


def test_kind_filter() -> None:
    out = run("o/r#1", "--kind", "issue").output
    assert "coverage" in out and "please rename" not in out


def test_since_filters_old_comments() -> None:
    assert "No matching comments" in run("o/r#1", "--since", "2030-01-01").output


def test_api_error_reports_pr() -> None:
    result = run("o/r#404")
    assert result.exit_code == 1 and "o/r#404: not found" in result.output


def test_output_file(tmp_path) -> None:
    target = tmp_path / "out.md"
    result = run("o/r#1", "-o", str(target))
    assert result.exit_code == 0
    assert "please rename" in target.read_text(encoding="utf-8")


def test_token_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "secret")
    run("o/r#1")
    assert StubClient.last_token == "secret"


def test_parse_since_relative() -> None:
    dt = cli.parse_since("7d")
    assert timedelta(days=6, hours=23) < datetime.now(UTC) - dt < timedelta(days=7, minutes=1)
    assert cli.parse_since("12h") < datetime.now(UTC)


def test_parse_since_date_is_utc() -> None:
    assert cli.parse_since("2024-05-01") == datetime(2024, 5, 1, tzinfo=UTC)


def test_parse_since_invalid() -> None:
    with pytest.raises(click.BadParameter):
        cli.parse_since("yesterday")
