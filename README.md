# Threadloom

**A CLI tool that aggregates review comments from multiple GitHub pull requests into a single markdown summary, streamlining async code review for teams.**

Async code review fatigue sets in when reviewers juggle dozens of pull requests, each with scattered comments across threads. Keeping track of what's been addressed, what's stale, and what needs attention becomes a mental overhead that slows down teams. Threadloom pulls all review comments into a single, chronological markdown summary so reviewers can focus on what matters.

## Example

<!-- A real command and its REAL pasted output. Run it first. -->

## Install

```bash
pip install -e ".[dev]"
```

## Usage

<!-- The 2-4 commands people actually need, one line each. -->

## How it works

- Fetches pull request data from GitHub using the provided token.
- Retrieves all review comments for each PR via the GitHub API.
- Parses comment bodies, timestamps, and author information.
- Aggregates comments across PRs, sorting them chronologically.
- Formats the aggregated data into a markdown summary with sections per PR.

## Limitations

<!-- Honest and short: what it does NOT do, known gaps. -->

## Development

```bash
pip install -e ".[dev]"
pytest -q
ruff check .
```

## License

MIT -- see [LICENSE](LICENSE).
