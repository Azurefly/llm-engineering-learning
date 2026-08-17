from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


class Database:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.init()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path, timeout=5.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA busy_timeout = 5000")
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def init(self) -> None:
        with self.connect() as conn:
            # WAL allows readers to continue while short autosave writes occur.
            # NORMAL synchronous is the standard durability/performance tradeoff for WAL.
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA synchronous = NORMAL")
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS lesson_progress (
                    lesson_key TEXT PRIMARY KEY,
                    status TEXT NOT NULL DEFAULT 'not_started',
                    percent INTEGER NOT NULL DEFAULT 0 CHECK(percent >= 0 AND percent <= 100),
                    score REAL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS thoughts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL DEFAULT '',
                    tags TEXT NOT NULL DEFAULT '',
                    lesson_key TEXT,
                    language TEXT NOT NULL DEFAULT 'zh-CN',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS resources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    tags TEXT NOT NULL DEFAULT '',
                    lesson_key TEXT,
                    language TEXT NOT NULL DEFAULT 'zh-CN',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_thoughts_lesson ON thoughts(lesson_key);
                CREATE INDEX IF NOT EXISTS idx_resources_lesson ON resources(lesson_key);
                """
            )

    def all_progress(self) -> dict[str, dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM lesson_progress").fetchall()
        return {row["lesson_key"]: dict(row) for row in rows}

    def set_progress(self, lesson_key: str, status: str, percent: int, score: float | None) -> None:
        percent = max(0, min(100, int(percent)))
        if status == "completed": percent = 100
        elif percent == 100: status = "completed"
        elif percent > 0 and status == "not_started": status = "in_progress"
        with self.connect() as conn:
            conn.execute(
                """INSERT INTO lesson_progress(lesson_key,status,percent,score,updated_at)
                VALUES(?,?,?,?,?) ON CONFLICT(lesson_key) DO UPDATE SET
                status=excluded.status,percent=excluded.percent,score=excluded.score,updated_at=excluded.updated_at""",
                (lesson_key, status, percent, score, now_iso()),
            )

    def list_thoughts(self, lesson_key: str | None = None) -> list[dict[str, Any]]:
        sql, params = "SELECT * FROM thoughts", ()
        if lesson_key: sql, params = sql + " WHERE lesson_key=?", (lesson_key,)
        sql += " ORDER BY updated_at DESC, id DESC"
        with self.connect() as conn: return [dict(r) for r in conn.execute(sql, params).fetchall()]

    def get_thought(self, item_id: int) -> dict[str, Any] | None:
        with self.connect() as conn: row = conn.execute("SELECT * FROM thoughts WHERE id=?", (item_id,)).fetchone()
        return dict(row) if row else None

    def save_thought(self, item_id: int | None, *, title: str, content: str, tags: str, lesson_key: str | None, language: str) -> int:
        ts = now_iso()
        with self.connect() as conn:
            if item_id:
                conn.execute("UPDATE thoughts SET title=?,content=?,tags=?,lesson_key=?,language=?,updated_at=? WHERE id=?", (title, content, tags, lesson_key or None, language, ts, item_id)); return item_id
            cur = conn.execute("INSERT INTO thoughts(title,content,tags,lesson_key,language,created_at,updated_at) VALUES(?,?,?,?,?,?,?)", (title, content, tags, lesson_key or None, language, ts, ts)); return int(cur.lastrowid)

    def delete_thought(self, item_id: int) -> None:
        with self.connect() as conn: conn.execute("DELETE FROM thoughts WHERE id=?", (item_id,))

    def list_resources(self, lesson_key: str | None = None) -> list[dict[str, Any]]:
        sql, params = "SELECT * FROM resources", ()
        if lesson_key: sql, params = sql + " WHERE lesson_key=?", (lesson_key,)
        sql += " ORDER BY updated_at DESC, id DESC"
        with self.connect() as conn: return [dict(r) for r in conn.execute(sql, params).fetchall()]

    def get_resource(self, item_id: int) -> dict[str, Any] | None:
        with self.connect() as conn: row = conn.execute("SELECT * FROM resources WHERE id=?", (item_id,)).fetchone()
        return dict(row) if row else None

    def save_resource(self, item_id: int | None, *, title: str, url: str, description: str, tags: str, lesson_key: str | None, language: str) -> int:
        ts = now_iso()
        with self.connect() as conn:
            if item_id:
                conn.execute("UPDATE resources SET title=?,url=?,description=?,tags=?,lesson_key=?,language=?,updated_at=? WHERE id=?", (title, url, description, tags, lesson_key or None, language, ts, item_id)); return item_id
            cur = conn.execute("INSERT INTO resources(title,url,description,tags,lesson_key,language,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)", (title, url, description, tags, lesson_key or None, language, ts, ts)); return int(cur.lastrowid)

    def delete_resource(self, item_id: int) -> None:
        with self.connect() as conn: conn.execute("DELETE FROM resources WHERE id=?", (item_id,))

    def stats(self) -> dict[str, Any]:
        with self.connect() as conn:
            return {
                "thought_count": conn.execute("SELECT COUNT(*) FROM thoughts").fetchone()[0],
                "resource_count": conn.execute("SELECT COUNT(*) FROM resources").fetchone()[0],
                "completed": conn.execute("SELECT COUNT(*) FROM lesson_progress WHERE status='completed'").fetchone()[0],
            }

    def export_json(self) -> str:
        payload = {}
        with self.connect() as conn:
            for table in ("lesson_progress", "thoughts", "resources"):
                payload[table] = [dict(r) for r in conn.execute(f"SELECT * FROM {table}").fetchall()]
        return json.dumps(payload, ensure_ascii=False, indent=2)
