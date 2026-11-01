# Threadloom

**A CLI tool that aggregates review comments from multiple GitHub pull requests into a single markdown summary, streamlining async code review for teams.**

Async code review fatigue sets in when reviewers juggle dozens of pull requests, each with scattered comments across threads. Keeping track of what's been addressed, what's stale, and what needs attention becomes a mental overhead that slows down teams. Threadloom pulls all review comments into a single, chronological markdown summary so reviewers can focus on what matters.

## Example

```bash
threadloom psf/requests#6710 --kind inline --kind review --max-chars 120
```

Output (captured from a real run against the public repo; progress lines go to stderr):

```markdown
# Review comment summary

4 comments across 1 pull request (generated 2026-11-01 08:36 UTC).

Most active: @nateprewitt (2), @sethmlarson (2)

## [psf/requests#6710](https://github.com/psf/requests/pull/6710) Move _get_connection to get_connection_with_tls_context

State: merged - author @nateprewitt - 4 comments

- **@sethmlarson** - 2024-05-21 16:12 - inline - `src/requests/adapters.py:418`

  > If this method is deprecated shall we start emitting `DeprecationWarning`?

  [link](https://github.com/psf/requests/pull/6710#discussion_r1608603801)

- **@sethmlarson** - 2024-05-21 16:13 - review - approved

  > Looks good, only had one suggestion that might require a new test.

  [link](https://github.com/psf/requests/pull/6710#pullrequestreview-2069075746)

- **@nateprewitt** - 2024-05-21 16:17 - inline - `src/requests/adapters.py:418` - reply

  > I thought about that but it's not reachable in any of our code anymore and if someone is using a custom implementation i...

  [link](https://github.com/psf/requests/pull/6710#discussion_r1608609666)

- **@nateprewitt** - 2024-05-21 16:29 - inline - `src/requests/adapters.py:418` - reply

  > I guess it's better to be safe, this should be addressed in 92075b330a30b9883f466a43d3f7566ab849f91b.

  [link](https://github.com/psf/requests/pull/6710#discussion_r1608624860)
```

## Install

```bash
pip install -e ".[dev]"
```

## Usage

```bash
export GITHUB_TOKEN=ghp_...                      # optional for public repos, avoids rate limits
threadloom owner/repo#12 owner/repo#15           # several PRs, one summary
threadloom https://github.com/owner/repo/pull/12 # PR URLs work too
threadloom 12 15 --repo owner/repo               # bare numbers with a default repo
threadloom owner/repo#12 --since 7d --no-bots --flat -o review.md
```

Progress goes to stderr, markdown to stdout (or the file given with `-o`). Also runnable as
`python -m threadloom`.

### Options

| Option | Meaning |
| --- | --- |
| `-r, --repo owner/name` | Default repository for bare PR numbers |
| `--since VALUE` | Only comments newer than `7d`, `12h`, or an ISO date such as `2024-05-01` |
| `--author NAME` | Only these authors (repeatable, comma-separated allowed) |
| `--exclude-author NAME` | Drop these authors |
| `--no-bots` | Drop accounts whose login ends in `[bot]` |
| `--kind KIND` | `inline`, `review` or `issue`; repeatable, default is all three |
| `--flat` | One chronological timeline instead of a section per PR |
| `--max-chars N` | Truncate long comment bodies |
| `-o, --output FILE` | Write markdown to a file |
| `--token TOKEN` | GitHub token; defaults to `$GITHUB_TOKEN` |

Environment: `GITHUB_TOKEN`, `GITHUB_API_URL` (GitHub Enterprise), `GITHUB_PER_PAGE`.

## How it works

- Fetches pull request data from GitHub using the provided token.
- Retrieves all review comments for each PR via the GitHub API.
- Parses comment bodies, timestamps, and author information.
- Aggregates comments across PRs, sorting them chronologically.
- Formats the aggregated data into a markdown summary with sections per PR.

## Limitations

- Does not resolve or track review threads, so "addressed" vs "open" is not detected; replies are
  only marked as `reply`.
- Comments come from three endpoints (inline, review bodies, conversation); later edits or
  deletions are not tracked.
- Unauthenticated use is limited by GitHub to 60 requests per hour (about 4 requests per PR).

## Development

```bash
pip install -e ".[dev]"
pytest -q
ruff check .
```

## License

MIT -- see [LICENSE](LICENSE).
