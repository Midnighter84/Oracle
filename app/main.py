"""Long-poll loop: read channel links, summarize, reply in-channel."""
from __future__ import annotations

import argparse
import logging
import time
from typing import Any

import requests

from . import config, telegram
from .extract import fetch
from .state import State
from .summarize import format_reply, summarize

log = logging.getLogger("telegram-summarizer")


def _setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(config.LOG_FILE),
        ],
    )


def _post_from_update(update: dict[str, Any]) -> dict[str, Any] | None:
    """Return the message object carrying user content, if any."""
    return update.get("channel_post") or update.get("message")


def process_post(post: dict[str, Any], state: State, dry_run: bool) -> None:
    chat = post.get("chat", {})
    chat_id = chat.get("id")
    message_id = post.get("message_id")
    if chat_id is None or message_id is None:
        return

    if config.ALLOWED_CHAT_IDS and chat_id not in config.ALLOWED_CHAT_IDS:
        log.info("Skipping chat %s (not in allowlist)", chat_id)
        return

    urls = telegram.extract_urls(post)
    if not urls:
        return

    log.info("Post %s in chat %s has %d url(s)", message_id, chat_id, len(urls))
    for url in urls:
        if state.already_processed(chat_id, message_id, url):
            log.info("Already processed, skipping: %s", url)
            continue
        try:
            _handle_url(chat_id, message_id, url, state, dry_run)
        except Exception:  # noqa: BLE001 - one bad link must not kill the loop
            log.exception("Failed handling %s", url)


def _handle_url(chat_id: int, message_id: int, url: str, state: State, dry_run: bool) -> None:
    log.info("Fetching %s", url)
    article = fetch(url)
    if not article.ok:
        log.warning("No content extracted for %s; skipping", url)
        return

    log.info("Extracted %d chars (%s); summarizing", len(article.text), article.source)
    summary = summarize(article)
    if not summary:
        log.warning("Empty summary for %s; skipping", url)
        return

    reply = format_reply(article, summary)
    if dry_run:
        print("=" * 70)
        print(f"WOULD REPLY in chat {chat_id} to msg {message_id} for {url}:\n")
        print(reply)
        print("=" * 70)
        return

    telegram.send_message(chat_id, reply, reply_to_message_id=message_id)
    state.mark_processed(chat_id, message_id, url)
    log.info("Replied for %s", url)


def poll_once(state: State, dry_run: bool) -> int:
    offset = state.get_offset()
    updates = telegram.get_updates(offset, timeout=config.POLL_TIMEOUT)
    for update in updates:
        update_id = update.get("update_id", 0)
        post = _post_from_update(update)
        if post:
            process_post(post, state, dry_run)
        # advance offset regardless so we never re-fetch this update
        state.set_offset(update_id + 1)
    return len(updates)


def run_forever(state: State, dry_run: bool) -> None:
    log.info("Starting long-poll loop (dry_run=%s)", dry_run)
    backoff = 1
    while True:
        try:
            poll_once(state, dry_run)
            backoff = 1
        except requests.RequestException as exc:
            log.warning("Network error: %s; retrying in %ss", exc, backoff)
            time.sleep(backoff)
            backoff = min(backoff * 2, 60)
        except Exception:  # noqa: BLE001
            log.exception("Unexpected error; retrying in %ss", backoff)
            time.sleep(backoff)
            backoff = min(backoff * 2, 60)


def main() -> None:
    parser = argparse.ArgumentParser(description="Telegram link summarizer")
    parser.add_argument("--once", action="store_true", help="run a single poll cycle then exit")
    parser.add_argument("--dry-run", action="store_true", help="print summaries instead of sending")
    args = parser.parse_args()

    _setup_logging()
    config.require_token()
    state = State()
    try:
        if args.once:
            n = poll_once(state, args.dry_run)
            log.info("Processed %d update(s)", n)
        else:
            run_forever(state, args.dry_run)
    finally:
        state.close()


if __name__ == "__main__":
    main()
