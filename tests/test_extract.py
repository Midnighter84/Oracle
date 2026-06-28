from app import extract
from app.extract import Article


def test_truncation_to_max_input_chars(monkeypatch):
    long_text = "y" * (extract.config.MAX_INPUT_CHARS + 1000)
    monkeypatch.setattr(
        extract, "_via_trafilatura",
        lambda url: Article(url, "T", long_text, "trafilatura"),
    )
    art = extract.fetch("https://example.com")
    assert len(art.text) <= extract.config.MAX_INPUT_CHARS + len("\n\n[...truncated...]")
    assert art.text.endswith("[...truncated...]")
    assert art.source == "trafilatura"


def test_jina_fallback_when_trafilatura_thin(monkeypatch):
    monkeypatch.setattr(
        extract, "_via_trafilatura",
        lambda url: Article(url, "", "short", "trafilatura"),  # below MIN_CONTENT_CHARS
    )
    rich = "z" * (extract.config.MIN_CONTENT_CHARS + 100)
    monkeypatch.setattr(
        extract, "_via_jina",
        lambda url: Article(url, "JT", rich, "jina"),
    )
    art = extract.fetch("https://example.com")
    assert art.source == "jina"
    assert art.text == rich


def test_no_fallback_when_trafilatura_rich(monkeypatch):
    rich = "a" * (extract.config.MIN_CONTENT_CHARS + 100)
    monkeypatch.setattr(
        extract, "_via_trafilatura",
        lambda url: Article(url, "T", rich, "trafilatura"),
    )

    def _boom(url):
        raise AssertionError("jina should not be called")

    monkeypatch.setattr(extract, "_via_jina", _boom)
    art = extract.fetch("https://example.com")
    assert art.source == "trafilatura"


def test_article_ok():
    assert not Article("u", "", "", "trafilatura").ok
    assert not Article("u", "", "   ", "trafilatura").ok
    assert Article("u", "", "content", "trafilatura").ok
