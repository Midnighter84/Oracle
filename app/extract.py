"""Smart download + content extraction.

Primary path: trafilatura (fast, local, strong boilerplate removal).
Fallback: Jina Reader (https://r.jina.ai/<url>) for JS-heavy / paywalled pages
that trafilatura can't render — it returns clean markdown.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

import requests
import trafilatura

from . import config

log = logging.getLogger(__name__)


@dataclass
class Article:
    url: str
    title: str
    text: str
    source: str  # "trafilatura" | "jina"

    @property
    def ok(self) -> bool:
        return bool(self.text and self.text.strip())


def fetch(url: str) -> Article:
    """Return cleaned main content for a URL, with metadata when available."""
    article = _via_trafilatura(url)
    if not article.ok or len(article.text) < config.MIN_CONTENT_CHARS:
        log.info("trafilatura thin for %s (%d chars); trying Jina",
                 url, len(article.text) if article.ok else 0)
        fallback = _via_jina(url)
        if fallback.ok and len(fallback.text) > len(article.text):
            article = fallback

    if article.ok and len(article.text) > config.MAX_INPUT_CHARS:
        article.text = article.text[: config.MAX_INPUT_CHARS] + "\n\n[...truncated...]"
    return article


def _via_trafilatura(url: str) -> Article:
    try:
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            return Article(url, "", "", "trafilatura")
        text = trafilatura.extract(
            downloaded,
            include_comments=False,
            include_tables=True,
            favor_precision=True,
            url=url,
        ) or ""
        title = ""
        meta = trafilatura.extract_metadata(downloaded)
        if meta and meta.title:
            title = meta.title
        return Article(url, title, text.strip(), "trafilatura")
    except Exception as exc:  # noqa: BLE001 - never let extraction crash the loop
        log.warning("trafilatura failed for %s: %s", url, exc)
        return Article(url, "", "", "trafilatura")


def _via_jina(url: str) -> Article:
    try:
        resp = requests.get(
            f"https://r.jina.ai/{url}",
            headers={"User-Agent": config.USER_AGENT, "Accept": "text/plain"},
            timeout=config.HTTP_TIMEOUT,
        )
        resp.raise_for_status()
        text = resp.text.strip()
        # Jina prepends "Title: ...\nURL Source: ...\nMarkdown Content:\n"
        title = ""
        for line in text.splitlines()[:5]:
            if line.lower().startswith("title:"):
                title = line.split(":", 1)[1].strip()
                break
        return Article(url, title, text, "jina")
    except Exception as exc:  # noqa: BLE001
        log.warning("jina fallback failed for %s: %s", url, exc)
        return Article(url, "", "", "jina")


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)
    target = sys.argv[1] if len(sys.argv) > 1 else "https://example.com"
    art = fetch(target)
    print(f"source={art.source} title={art.title!r} chars={len(art.text)}")
    print("-" * 60)
    print(art.text[:1500])
