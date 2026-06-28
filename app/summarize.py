"""Summarize cleaned article text via the authenticated `claude -p` CLI."""
from __future__ import annotations

import logging
import subprocess

from . import config
from .extract import Article

log = logging.getLogger(__name__)

_PROMPT = """You are summarizing a web article for a Telegram channel.
Produce a concise, skimmable summary in PLAIN TEXT (no markdown symbols like # or *).

Format exactly:
<title line>
TL;DR: <one sentence>

- <key point>
- <key point>
- <key point>
(3 to 6 bullets, each one short line)

Keep the whole thing under 1200 characters. Do not invent facts not in the text.
Article title: {title}
Source URL: {url}

ARTICLE TEXT FOLLOWS:
"""


def summarize(article: Article) -> str:
    prompt = _PROMPT.format(title=article.title or "(unknown)", url=article.url)
    stdin_data = prompt + "\n" + article.text

    try:
        proc = subprocess.run(
            [
                config.CLAUDE_BIN,
                "-p",
                "--model", config.MODEL,
                "--max-turns", "1",
            ],
            input=stdin_data,
            capture_output=True,
            text=True,
            timeout=config.CLAUDE_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        log.error("claude -p timed out for %s", article.url)
        return ""
    except FileNotFoundError:
        log.error("claude binary not found at %r", config.CLAUDE_BIN)
        return ""

    if proc.returncode != 0:
        log.error("claude -p failed (%s): %s", proc.returncode, proc.stderr.strip()[:500])
        return ""

    summary = proc.stdout.strip()
    if not summary:
        log.error("claude -p returned empty output for %s", article.url)
    return summary


def format_reply(article: Article, summary: str) -> str:
    """Combine summary + source attribution into the message body."""
    footer = f"\n\n🔗 {article.url}"
    if article.source == "jina":
        footer += " (via reader)"
    return summary + footer
