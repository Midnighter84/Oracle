"""Configuration loaded from environment / .env file.

No external dependency: we parse a simple KEY=VALUE .env ourselves so the
service has one less thing to install.
"""
from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _load_dotenv(path: Path) -> None:
    """Populate os.environ from a .env file without overriding real env vars."""
    if not path.exists():
        return
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_dotenv(BASE_DIR / ".env")


def _int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


# --- Telegram ---
BOT_TOKEN: str = os.environ.get("BOT_TOKEN", "").strip()
# Comma-separated list of chat ids the bot is allowed to act in. Empty = allow all.
_allowed = os.environ.get("ALLOWED_CHAT_IDS", "").strip()
ALLOWED_CHAT_IDS: set[int] = {
    int(x) for x in _allowed.replace(" ", "").split(",") if x
}

# --- Summarizer (claude CLI) ---
CLAUDE_BIN: str = os.environ.get("CLAUDE_BIN", "claude")
MODEL: str = os.environ.get("MODEL", "claude-sonnet-4-6")
CLAUDE_TIMEOUT: int = _int("CLAUDE_TIMEOUT", 180)

# --- Extraction ---
# If the primary extractor yields fewer than this many chars, try the Jina fallback.
MIN_CONTENT_CHARS: int = _int("MIN_CONTENT_CHARS", 500)
# Hard cap on characters fed to the summarizer (keeps cost/latency bounded).
MAX_INPUT_CHARS: int = _int("MAX_INPUT_CHARS", 24000)
HTTP_TIMEOUT: int = _int("HTTP_TIMEOUT", 30)
USER_AGENT: str = os.environ.get(
    "USER_AGENT",
    "Mozilla/5.0 (compatible; TelegramSummarizer/1.0; +https://t.me)",
)

# --- Poller ---
POLL_TIMEOUT: int = _int("POLL_TIMEOUT", 30)  # long-poll seconds
STATE_DB: str = os.environ.get("STATE_DB", str(BASE_DIR / "state.db"))
LOG_FILE: str = os.environ.get("LOG_FILE", str(BASE_DIR / "telegram-summarizer.log"))

# Telegram message hard limit.
TELEGRAM_MAX_CHARS = 4096


def require_token() -> str:
    if not BOT_TOKEN:
        raise SystemExit(
            "BOT_TOKEN is not set. Add it to telegram-summarizer/.env "
            "(see .env.example)."
        )
    return BOT_TOKEN
