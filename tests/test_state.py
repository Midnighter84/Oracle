from app.state import State


def test_offset_roundtrip(tmp_path):
    s = State(str(tmp_path / "state.db"))
    assert s.get_offset() == 0
    s.set_offset(42)
    assert s.get_offset() == 42
    s.set_offset(43)  # upsert, not insert
    assert s.get_offset() == 43
    s.close()


def test_offset_persists_across_instances(tmp_path):
    path = str(tmp_path / "state.db")
    s = State(path)
    s.set_offset(100)
    s.close()
    s2 = State(path)
    assert s2.get_offset() == 100
    s2.close()


def test_dedup(tmp_path):
    s = State(str(tmp_path / "state.db"))
    assert not s.already_processed(-1, 2, "https://a.com")
    s.mark_processed(-1, 2, "https://a.com")
    assert s.already_processed(-1, 2, "https://a.com")
    # different url / message is independent
    assert not s.already_processed(-1, 2, "https://b.com")
    assert not s.already_processed(-1, 3, "https://a.com")
    s.close()


def test_mark_processed_idempotent(tmp_path):
    s = State(str(tmp_path / "state.db"))
    s.mark_processed(-1, 2, "https://a.com")
    s.mark_processed(-1, 2, "https://a.com")  # INSERT OR IGNORE
    assert s.already_processed(-1, 2, "https://a.com")
    s.close()
