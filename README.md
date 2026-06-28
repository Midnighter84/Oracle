# Oracle — Telegram link summarizer

Drop a web-page link into a Telegram channel → an always-on service picks it up, smartly
downloads and cleans the page (main content only, no nav/ads), summarizes it with the local
`claude` CLI, and replies with the summary under your message.

```
channel post (URL) ──> bot getUpdates (long-poll)
                            │
   reply with summary  <────┤ trafilatura → (Jina fallback) → claude -p
        (in-channel)        │ dedup + offset in state.db
```

## Quick start

```bash
cd /home/ubuntu/telegram-summarizer
make setup                       # venv + runtime + dev deps
cp .env.example .env             # then add BOT_TOKEN, chmod 600 .env
make discover-chat               # post in the channel first; prints the chat id
# put the id into ALLOWED_CHAT_IDS in .env
make dry-run                     # prints a summary without sending
make service-install             # enable the always-on systemd service
```

Then just drop article links into the channel — within seconds the bot replies with a
TL;DR + key points. Multiple links in one post are each summarized.

## Documentation

| Doc | What's in it |
| --- | --- |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design, data flow, module responsibilities, design decisions, extension points, failure modes |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Install/operate runbook, full config reference, troubleshooting, backup, security |
| [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) | Dev setup, testing, how to extend the pipeline |
| [CHANGELOG.md](CHANGELOG.md) | Release notes |

## Layout

```
app/            application package
  config.py     env/.env config
  telegram.py   Bot API client + URL extraction
  extract.py    trafilatura → Jina fallback
  summarize.py  wraps `claude -p`
  state.py      SQLite: offset + dedup
  main.py       the long-poll loop (--once / --dry-run)
tests/          pytest suite (no network)
docs/           architecture / deployment / development
systemd/        user service unit
Makefile        helper targets (see: make help)
```

## Requirements

- Python 3.12, `python3-venv`
- The `claude` CLI, already authenticated (used via `claude -p`; no API key needed)
- Network access to `api.telegram.org` and `r.jina.ai`

## Known limitations

- Targets HTML articles. YouTube/X/PDF links aren't specially handled yet (Jina covers some).
- Long-poll only (no public webhook), so no inbound firewall changes needed.
