"""SQLite-backed state: long-poll offset + dedup of processed items."""
from __future__ import annotations

import sqlite3
from contextlib import closing

from . import config


class State:
    def __init__(self, path: str = config.STATE_DB):
        self.conn = sqlite3.connect(path)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self._init_schema()

    def _init_schema(self) -> None:
        with self.conn:
            self.conn.execute(
                "CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT)"
            )
            self.conn.execute(
                "CREATE TABLE IF NOT EXISTS processed ("
                "  chat_id INTEGER NOT NULL,"
                "  message_id INTEGER NOT NULL,"
                "  url TEXT NOT NULL,"
                "  ts TEXT NOT NULL DEFAULT (datetime('now')),"
                "  PRIMARY KEY (chat_id, message_id, url)"
                ")"
            )

    # --- long-poll offset ---
    def get_offset(self) -> int:
        with closing(self.conn.execute(
            "SELECT value FROM meta WHERE key='offset'"
        )) as cur:
            row = cur.fetchone()
        return int(row[0]) if row else 0

    def set_offset(self, offset: int) -> None:
        with self.conn:
            self.conn.execute(
                "INSERT INTO meta(key, value) VALUES('offset', ?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (str(offset),),
            )

    # --- dedup ---
    def already_processed(self, chat_id: int, message_id: int, url: str) -> bool:
        with closing(self.conn.execute(
            "SELECT 1 FROM processed WHERE chat_id=? AND message_id=? AND url=?",
            (chat_id, message_id, url),
        )) as cur:
            return cur.fetchone() is not None

    def mark_processed(self, chat_id: int, message_id: int, url: str) -> None:
        with self.conn:
            self.conn.execute(
                "INSERT OR IGNORE INTO processed(chat_id, message_id, url) "
                "VALUES(?, ?, ?)",
                (chat_id, message_id, url),
            )

    def close(self) -> None:
        self.conn.close()
