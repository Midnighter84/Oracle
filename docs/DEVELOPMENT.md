# Development

## Setup

```bash
git clone https://github.com/Midnighter84/Oracle.git telegram-summarizer
cd telegram-summarizer
make setup          # .venv + runtime + dev deps (pytest, ruff)
```

No secrets are needed to run the tests (they don't touch the network or Telegram).

## Project layout

```
app/        application package (see docs/ARCHITECTURE.md for responsibilities)
tests/      pytest suite — pure logic, no network
docs/        architecture / deployment / development
systemd/     user service unit
Makefile     dev & ops helper targets (run `make help`)
```

## Everyday commands

```bash
make test                 # run pytest
make lint                 # ruff check
make run-once             # one poll cycle against the real channel (needs .env)
make dry-run              # one cycle, prints summaries instead of sending
.venv/bin/python -m app.extract https://example.com/article   # test extraction on a URL
```

## Conventions

- Python 3.12, standard library + `trafilatura` + `requests` only at runtime.
- Keep runtime dependencies minimal; config is read via `app/config.py` (no `python-dotenv`).
- Extractors must **never raise** — return an empty `Article` on failure so one bad URL
  can't crash the loop (see `app/extract.py`).
- Replies are plain text; don't introduce Markdown/HTML parse modes without escaping.
- Lint with `ruff` before committing (`make lint`).

## How to extend

### Add a content source (e.g. YouTube transcripts, PDFs)
1. Add `_via_x(url) -> Article` in `app/extract.py` (follow `_via_jina`'s shape: catch all
   exceptions, return `Article(url, title, text, "x")`).
2. Insert it into `fetch()`'s fallback chain, guarded by a cheap URL check
   (e.g. host is `youtube.com`).
3. Add the dependency to `requirements.txt` and a unit test with the network mocked.

### Swap the summarizer (e.g. Anthropic API instead of CLI)
Replace the body of `summarize()` in `app/summarize.py`. The pipeline only depends on it
returning a `str` (empty string = skip). Keep `format_reply` for the source-link footer.

### Change summary style
Edit the `_PROMPT` template in `app/summarize.py`.

## Testing notes

- `tests/test_telegram.py` — `extract_urls`, `_chunk`.
- `tests/test_state.py` — offset + dedup against a temp SQLite file.
- `tests/test_config.py` — `.env` parsing helpers, `_int`, allowlist parsing.
- `tests/test_extract.py` — truncation + fallback selection with HTTP monkeypatched.

Network is never hit in tests. When adding an extractor, monkeypatch the fetch function.

## Commit / release flow

- Branch for non-trivial work; keep `main` deployable.
- Run `make test && make lint` before committing.
- Update `CHANGELOG.md` for user-visible changes; tag releases `vX.Y.Z`.
- Deploy by `git pull` + `make service-restart` on the host (see docs/DEPLOYMENT.md).
