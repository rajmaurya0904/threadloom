"""Command line interface for threadloom."""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import click

from threadloom import __version__, config
from threadloom.aggregate import KINDS, Filters, apply_filters
from threadloom.client import GitHubClient, GitHubError
from threadloom.models import PullRequest
from threadloom.refs import RefError, parse_refs
from threadloom.render import render_summary


def parse_since(value: str) -> datetime:
    """Accept ``7d`` / ``12h`` style durations or an ISO date/datetime."""
    value = value.strip()
    if value and value[-1] in "dh" and value[:-1].isdigit():
        n = int(value[:-1])
        delta = timedelta(days=n) if value[-1] == "d" else timedelta(hours=n)
        return datetime.now(UTC) - delta
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise click.BadParameter(f"use 7d, 12h or an ISO date, got {value!r}") from exc
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def _split(values: tuple[str, ...]) -> set[str]:
    return {v.lstrip("@").lower() for item in values for v in item.split(",") if v.strip()}


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("prs", nargs=-1)
@click.option("--repo", "-r", help="Default owner/name for bare PR numbers.")
@click.option("--since", help="Only comments newer than this (7d, 12h, or 2024-05-01).")
@click.option("--author", "authors", multiple=True, help="Only these authors (repeatable).")
@click.option("--exclude-author", "excluded", multiple=True, help="Skip these authors.")
@click.option("--no-bots", is_flag=True, help="Skip accounts ending in [bot].")
@click.option(
    "--kind",
    "kinds",
    multiple=True,
    type=click.Choice(KINDS),
    help="Comment kinds to include (default: all).",
)
@click.option("--flat", is_flag=True, help="One chronological timeline instead of PR sections.")
@click.option("--max-chars", type=click.IntRange(min=1), help="Truncate long comment bodies.")
@click.option("--output", "-o", type=click.Path(dir_okay=False, path_type=Path), help="Write here.")
@click.option("--token", envvar="GITHUB_TOKEN", help="GitHub token (default: $GITHUB_TOKEN).")
@click.version_option(__version__, prog_name="threadloom")
def main(
    prs: tuple[str, ...],
    repo: str | None,
    since: str | None,
    authors: tuple[str, ...],
    excluded: tuple[str, ...],
    no_bots: bool,
    kinds: tuple[str, ...],
    flat: bool,
    max_chars: int | None,
    output: Path | None,
    token: str | None,
) -> None:
    """Aggregate review comments from PRS into one markdown summary.

    PRS are pull requests as owner/repo#123, a PR URL, or a bare number with --repo.
    """
    if not prs:
        raise click.UsageError("give at least one pull request")
    try:
        refs = parse_refs(list(prs), repo)
    except RefError as exc:
        raise click.UsageError(str(exc)) from exc

    flt = Filters(
        since=parse_since(since) if since else None,
        authors=_split(authors),
        exclude_authors=_split(excluded),
        kinds=set(kinds) if kinds else set(KINDS),
        skip_bots=no_bots,
    )
    client = GitHubClient(token=token or config.get_github_token())
    fetched: list[PullRequest] = []
    for ref in refs:
        click.echo(f"fetching {ref.slug}", err=True)
        try:
            fetched.append(client.get_pull_request(ref))
        except GitHubError as exc:
            raise click.ClickException(f"{ref.slug}: {exc}") from exc

    text = render_summary(apply_filters(fetched, flt), flat=flat, max_chars=max_chars)
    if output:
        output.write_text(text, encoding="utf-8")
        click.echo(f"wrote {output}", err=True)
    else:
        sys.stdout.buffer.write(text.encode("utf-8"))


if __name__ == "__main__":  # pragma: no cover
    main()
