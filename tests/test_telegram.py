from app import telegram


def test_extract_urls_text_link_and_plain():
    msg = {
        "text": "Check this https://a.com/x and more",
        "entities": [
            {"type": "url", "offset": 11, "length": 15},
            {"type": "text_link", "offset": 0, "length": 5,
             "url": "https://hidden.example/page"},
        ],
    }
    # text_link href first (from entities), then plain url from the regex
    assert telegram.extract_urls(msg) == [
        "https://hidden.example/page",
        "https://a.com/x",
    ]


def test_extract_urls_from_caption_and_trailing_punct():
    assert telegram.extract_urls({"caption": "see https://b.org/post."}) == [
        "https://b.org/post"
    ]


def test_extract_urls_dedup_preserves_order():
    msg = {"text": "https://a.com https://b.com https://a.com"}
    assert telegram.extract_urls(msg) == ["https://a.com", "https://b.com"]


def test_extract_urls_none():
    assert telegram.extract_urls({"text": "just some words"}) == []


def test_chunk_short_is_single():
    assert telegram._chunk("hello", 4096) == ["hello"]


def test_chunk_respects_size():
    chunks = telegram._chunk("x" * 5000, 4096)
    assert [len(c) for c in chunks] == [4096, 904]
    assert "".join(chunks) == "x" * 5000


def test_chunk_splits_on_lines():
    text = "a" * 3000 + "\n" + "b" * 3000
    chunks = telegram._chunk(text, 4096)
    assert all(len(c) <= 4096 for c in chunks)
    assert "".join(chunks) == text
