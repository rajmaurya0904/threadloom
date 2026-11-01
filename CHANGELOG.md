# Changelog
All notable changes to this project will be documented in this file.

## [0.1.0] - 2026-11-01
### Added
- `threadloom` command: fetch inline, review and conversation comments for one or more pull
  requests and render a single markdown summary.
- Filters: `--since`, `--author`, `--exclude-author`, `--no-bots`, `--kind`.
- `--flat` chronological timeline, `--max-chars` truncation and `-o` file output.
- GitHub client with pagination, retry on 429/5xx and clear rate-limit errors.
