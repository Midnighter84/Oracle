# Changelog

All notable changes to this project are documented here.
Format loosely follows [Keep a Changelog](https://keepachangelog.com/).

## [1.0.0] — 2026-06-28

Initial release.

### Added
- Always-on long-poll service that reads links from a Telegram channel, extracts
  clean article content, summarizes via the local `claude -p` CLI, and replies in-channel.
- Smart content extraction: `trafilatura` primary, `r.jina.ai` reader fallback for
  JS-heavy / paywalled pages.
- SQLite state (`state.db`): long-poll offset + per-`(chat_id, message_id, url)` dedup.
- `ALLOWED_CHAT_IDS` allowlist; plain-text replies chunked to Telegram's 4096-char limit.
- `--once` and `--dry-run` modes for testing.
- systemd user unit with `Restart=always`.
- Documentation (`docs/ARCHITECTURE.md`, `docs/DEPLOYMENT.md`, `docs/DEVELOPMENT.md`),
  pytest suite, and a `Makefile` of helper targets.
