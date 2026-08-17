from app.db import Database


def test_sqlite_uses_wal_and_busy_timeout(tmp_path):
    db = Database(tmp_path / "learning.db")
    with db.connect() as conn:
        mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
        timeout = conn.execute("PRAGMA busy_timeout").fetchone()[0]
        foreign_keys = conn.execute("PRAGMA foreign_keys").fetchone()[0]
    assert str(mode).lower() == "wal"
    assert int(timeout) >= 5000
    assert int(foreign_keys) == 1
