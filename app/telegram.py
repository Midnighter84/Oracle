"""Thin Telegram Bot API client + URL extraction from messages."""
from __future__ import annotations

import logging
import re
from typing import Any

import requests

from . import config

log = logging.getLogger(__name__)

_API = "https://api.telegram.org/bot{token}/{method}"
_URL_RE = re.compile(r"https?://[^\s<>()\[\]{}\"']+")


def _api(method: str) -> str:
    return _API.format(token=config.require_token(), method=method)


def get_updates(offset: int, timeout: int = config.POLL_TIMEOUT) -> list[dict[str, Any]]:
    """Long-poll for new updates. Returns the raw update list."""
    resp = requests.post(
        _api("getUpdates"),
        json={
            "offset": offset,
            "timeout": timeout,
            "allowed_updates": ["channel_post", "message"],
        },
        # network read must outlast the server-side long-poll
        timeout=timeout + 15,
    )
    resp.raise_for_status()
    data = resp.json()
    if not data.get("ok"):
        raise RuntimeError(f"getUpdates failed: {data}")
    return data.get("result", [])


def send_message(
    chat_id: int,
    text: str,
    reply_to_message_id: int | None = None,
    disable_preview: bool = True,
) -> None:
    """Send a plain-text message, splitting to respect Telegram's length limit."""
    for i, chunk in enumerate(_chunk(text, config.TELEGRAM_MAX_CHARS)):
        payload: dict[str, Any] = {
            "chat_id": chat_id,
            "text": chunk,
            "disable_web_page_preview": disable_preview,
        }
        # Only anchor the first chunk to the original post.
        if reply_to_message_id is not None and i == 0:
            payload["reply_to_message_id"] = reply_to_message_id
            payload["allow_sending_without_reply"] = True
        resp = requests.post(_api("sendMessage"), json=payload, timeout=config.HTTP_TIMEOUT)
        if resp.status_code != 200:
            log.error("sendMessage failed (%s): %s", resp.status_code, resp.text)
        resp.raise_for_status()


def extract_urls(message: dict[str, Any]) -> list[str]:
    """Pull URLs from a message: hidden hrefs from entities + a regex over text.

    `text_link` entities carry the real URL in their `url` field, so we read it
    directly. Plain `url` entities only give UTF-16 offsets (which don't line up
    with Python str slicing once non-BMP chars are present), so we let the regex
    pick those up from the text instead. We dedup while preserving order.
    """
    text = message.get("text") or message.get("caption") or ""
    entities = message.get("entities") or message.get("caption_entities") or []
    found: list[str] = []

    for ent in entities:
        if ent.get("type") == "text_link" and ent.get("url"):
            found.append(ent["url"])

    found.extend(_URL_RE.findall(text))

    seen: set[str] = set()
    out: list[str] = []
    for url in found:
        url = url.rstrip(".,);]")
        if url and url not in seen:
            seen.add(url)
            out.append(url)
    return out


def _chunk(text: str, size: int) -> list[str]:
    if len(text) <= size:
        return [text]
    chunks, buf = [], ""
    for line in text.splitlines(keepends=True):
        if len(buf) + len(line) > size:
            if buf:
                chunks.append(buf)
            # a single over-long line: hard-split it
            while len(line) > size:
                chunks.append(line[:size])
                line = line[size:]
            buf = line
        else:
            buf += line
    if buf:
        chunks.append(buf)
    return chunks
