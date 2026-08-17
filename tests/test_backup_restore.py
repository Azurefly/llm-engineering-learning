import json

import pytest

from app.backup import BackupError, export_all_json, parse_backup_json, restore_from_json
from app.db import Database, now_iso


def test_versioned_backup_round_trip(tmp_path):
    db = Database(tmp_path / "learning.db")
    with db.connect() as conn:
        conn.execute(
            "INSERT INTO thoughts(title,content,tags,lesson_key,language,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",
            ("before", "content", "tag", "week01", "zh-CN", now_iso(), now_iso()),
        )
    backup = export_all_json(db)
    payload = json.loads(backup)
    assert payload["_meta"]["format"] == "llm-engineering-learning-backup"
    assert payload["_meta"]["version"] >= 2
    assert len(payload["thoughts"]) == 1

    with db.connect() as conn:
        conn.execute("DELETE FROM thoughts")
    restored = restore_from_json(db, backup)
    assert restored["thoughts"] == 1
    with db.connect() as conn:
        row = conn.execute("SELECT title FROM thoughts").fetchone()
    assert row[0] == "before"
    snapshots = list((tmp_path / "backups").glob("pre-restore-*.json"))
    assert snapshots


def test_v1_backup_shape_is_still_accepted():
    tables = parse_backup_json('{"thoughts": [], "resources": []}')
    assert tables == {"thoughts": [], "resources": []}


def test_brief_envelope_format_is_still_accepted():
    tables = parse_backup_json('{"format":"llm-engineering-learning-backup","version":2,"tables":{"thoughts":[]}}')
    assert tables == {"thoughts": []}


def test_unknown_backup_table_is_rejected():
    with pytest.raises(BackupError):
        parse_backup_json('{"users": [{"admin": true}]}')


def test_unsafe_resource_url_in_backup_is_rejected():
    with pytest.raises(BackupError):
        parse_backup_json('{"resources":[{"title":"bad","url":"javascript:alert(1)"}]}')


def test_invalid_progress_and_adaptive_limits_are_rejected():
    with pytest.raises(BackupError):
        parse_backup_json('{"lesson_progress":[{"lesson_key":"week01","percent":101}]}')
    with pytest.raises(BackupError):
        parse_backup_json('{"adaptive_sessions":[{"max_items":10000}]}')
