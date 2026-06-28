# Deployment & operations

## Prerequisites

- Python 3.12 + `python3-venv` (`sudo apt-get install -y python3.12-venv`)
- The `claude` CLI on `PATH` (in `~/.local/bin`), already logged in
- A Telegram bot (via [@BotFather](https://t.me/BotFather)) added as **admin** of the channel
- Outbound network to `api.telegram.org` and `r.jina.ai`

## Install

```bash
cd /home/ubuntu/telegram-summarizer
make setup                       # create .venv + install runtime & dev deps

cp .env.example .env             # fill BOT_TOKEN
chmod 600 .env

# Discover the channel id: post any message in the channel first, then:
make discover-chat               # prints "... in chat <id>"
# put that id into ALLOWED_CHAT_IDS in .env

make dry-run                     # verify a summary is produced (nothing sent)
make service-install             # install + enable + start the systemd user service
loginctl enable-linger ubuntu    # keep it running without an active login (one-time)
```

`make service-install` copies `systemd/telegram-summarizer.service` to
`~/.config/systemd/user/`, runs `daemon-reload`, then `enable --now`.

## Configuration reference

All settings come from environment / `.env` (see `app/config.py`).

| Variable | Default | Purpose |
| --- | --- | --- |
| `BOT_TOKEN` | — (required) | Telegram bot token from BotFather. |
| `ALLOWED_CHAT_IDS` | empty (all) | Comma-separated chat ids the bot may act in. Empty = any chat it sees. |
| `CLAUDE_BIN` | `claude` | Path/name of the Claude CLI. |
| `MODEL` | `claude-sonnet-4-6` | Summarizer model. Use `claude-haiku-4-5-20251001` to cut cost. |
| `CLAUDE_TIMEOUT` | `180` | Seconds before a `claude -p` call is killed. |
| `MIN_CONTENT_CHARS` | `500` | Below this, the Jina fallback is attempted. |
| `MAX_INPUT_CHARS` | `24000` | Cap on characters fed to the summarizer. |
| `HTTP_TIMEOUT` | `30` | Timeout for HTTP fetches / sendMessage. |
| `POLL_TIMEOUT` | `30` | Long-poll seconds per `getUpdates`. |
| `USER_AGENT` | (browser-ish) | UA for the Jina fetch. |
| `STATE_DB` | `./state.db` | SQLite state path. |
| `LOG_FILE` | `./telegram-summarizer.log` | Log file path. |

After changing `.env`: `make service-restart`.

## Operating

```bash
make service-status                       # health
make logs                                 # tail the log file
journalctl --user -u telegram-summarizer -f   # or via journald
make service-restart                      # after editing .env or code
systemctl --user stop telegram-summarizer # stop
```

## Updating

```bash
cd /home/ubuntu/telegram-summarizer
git pull
make setup            # refresh deps if requirements changed
make test             # confirm green
make service-restart
```

## Backup & restore

State is just `state.db` (offset + dedup history). Back it up while the service is stopped
(or rely on WAL consistency):

```bash
make service-restart   # ensure WAL is checkpointed by a clean start, or stop first
cp state.db /backup/state.db.$(date +%F)
```

Restore by stopping the service, copying the file back, and restarting. Losing `state.db`
only means the offset resets and previously summarized links *may* be re-summarized.

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| No replies appear | Bot not channel admin, or wrong `ALLOWED_CHAT_IDS` | Re-add bot as admin; re-run `make discover-chat`; check id. |
| `BOT_TOKEN is not set` | Missing/empty `.env` | `cp .env.example .env`; set token; `make service-restart`. |
| Replies are empty/skipped | `claude -p` failing or timing out | Check `claude -p` works manually; raise `CLAUDE_TIMEOUT`; check logs. |
| Thin/odd summaries | Extractor got little content | Confirm Jina fallback ran (log says `source=jina`); raise `MIN_CONTENT_CHARS`. |
| Duplicate replies | `state.db` deleted/reset | Expected after state loss; dedup resumes going forward. |
| Service not running after reboot | Linger not enabled | `loginctl enable-linger ubuntu`. |

## Security

- Keep `.env` at mode `600`; it holds the bot token. It is git-ignored.
- `state.db` and `*.log` are git-ignored (logs/URLs may be sensitive).
- Rotate the bot token in BotFather if it leaks; update `.env`; `make service-restart`.
