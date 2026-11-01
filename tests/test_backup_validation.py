"""Backup payload validation and restore failure handling."""

import json
import sqlite3

import pytest

from app.backup import BackupError, parse_backup_json, restore_from_json
from app.db import Database


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ("not json at all", "Invalid JSON"),
        ("[]", "root must be a JSON object"),
        (
            json.dumps({"format": "llm-engineering-learning-backup", "version": 99, "tables": {}}),
            "Unsupported backup version",
        ),
        (
            json.dumps({"format": "llm-engineering-learning-backup", "version": 1, "tables": []}),
            "tables must be a JSON object",
        ),
        (json.dumps({"_meta": {"format": "something-else"}, "thoughts": []}), "Invalid backup metadata"),
        (
            json.dumps({"_meta": {"format": "llm-engineering-learning-backup", "version": 0}}),
            "Unsupported backup version",
        ),
        (json.dumps({"thoughts": {}}), "must contain a list of objects"),
        (json.dumps({"thoughts": ["not-an-object"]}), "must contain a list of objects"),
        (json.dumps({"lesson_progress": [{"lesson_key": "week01", "percent": "abc"}]}), "invalid percent"),
        (json.dumps({"adaptive_sessions": [{"max_items": "abc"}]}), "invalid max_items"),
        (json.dumps({"adaptive_sessions": [{"max_items": 0}]}), "outside the safe range"),
        (json.dumps({"lesson_progress": [{"lesson_key": "week01", "percent": -1}]}), "between 0 and 100"),
    ],
)
def test_malformed_backups_are_rejected_with_a_clear_message(payload, message):
    with pytest.raises(BackupError) as excinfo:
        parse_backup_json(payload)
    assert message in str(excinfo.value)


def test_brief_envelope_tables_are_normalised():
    tables = parse_backup_json(
        json.dumps({"format": "llm-engineering-learning-backup", "version": 2, "tables": {"thoughts": []}})
    )
    assert tables == {"thoughts": []}


def test_meta_envelope_drops_the_metadata_key():
    tables = parse_backup_json(
        json.dumps({"_meta": {"format": "llm-engineering-learning-backup", "version": 2}, "thoughts": []})
    )
    assert tables == {"thoughts": []}


def test_a_failed_restore_rolls_back_and_leaves_the_database_usable(tmp_path):
    db = Database(tmp_path / "learning.db")
    db.save_thought(None, title="keep me", content="body", tags="", lesson_key="week01", language="en")
    # A nested object cannot be bound as a SQLite value, so the insert fails
    # mid-transaction and the restore must roll back.
    payload = json.dumps({"thoughts": [{"title": {"nested": 1}, "content": "boom"}]})

    with pytest.raises(sqlite3.ProgrammingError):
        restore_from_json(db, payload, replace=True)

    with db.connect() as conn:
        assert conn.execute("SELECT COUNT(*) FROM thoughts").fetchone()[0] == 1
