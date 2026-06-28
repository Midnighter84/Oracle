from app import config


def test_load_dotenv_parsing(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "# a comment\n"
        "\n"
        "BOT_TOKEN=abc123\n"
        'QUOTED="hello world"\n'
        "SINGLE='single'\n"
        "WITH_EQ=a=b=c\n"
        "NOT_A_LINE\n"
    )
    for k in ("BOT_TOKEN", "QUOTED", "SINGLE", "WITH_EQ"):
        monkeypatch.delenv(k, raising=False)

    config._load_dotenv(env_file)

    assert config.os.environ["BOT_TOKEN"] == "abc123"
    assert config.os.environ["QUOTED"] == "hello world"
    assert config.os.environ["SINGLE"] == "single"
    assert config.os.environ["WITH_EQ"] == "a=b=c"
    assert "NOT_A_LINE" not in config.os.environ


def test_load_dotenv_does_not_override(tmp_path, monkeypatch):
    monkeypatch.setenv("BOT_TOKEN", "real")
    env_file = tmp_path / ".env"
    env_file.write_text("BOT_TOKEN=fromfile\n")
    config._load_dotenv(env_file)
    assert config.os.environ["BOT_TOKEN"] == "real"


def test_load_dotenv_missing_file_is_noop(tmp_path):
    config._load_dotenv(tmp_path / "nope.env")  # should not raise


def test_int_helper(monkeypatch):
    monkeypatch.setenv("MY_INT", "7")
    assert config._int("MY_INT", 1) == 7
    monkeypatch.setenv("MY_INT", "notanint")
    assert config._int("MY_INT", 5) == 5
    monkeypatch.delenv("MY_INT", raising=False)
    assert config._int("MY_INT", 9) == 9


def test_allowed_chat_ids_parsing():
    # mirrors the module-level parsing logic
    raw = " -100123 , 456 ,, 789 "
    parsed = {int(x) for x in raw.replace(" ", "").split(",") if x}
    assert parsed == {-100123, 456, 789}
