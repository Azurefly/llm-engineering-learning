"""Progress state transitions and JSON export on a throwaway database."""

import json

from app.db import Database


def _db(tmp_path) -> Database:
    return Database(tmp_path / "learning.db")


def test_percent_100_promotes_status_to_completed(tmp_path):
    db = _db(tmp_path)

    db.set_progress("week01", "in_progress", 100, 80.0)

    stored = db.all_progress()["week01"]
    assert stored["status"] == "completed"
    assert stored["percent"] == 100


def test_positive_percent_promotes_not_started_to_in_progress(tmp_path):
    db = _db(tmp_path)

    db.set_progress("week02", "not_started", 40, None)

    assert db.all_progress()["week02"]["status"] == "in_progress"


def test_completed_status_forces_full_percent(tmp_path):
    db = _db(tmp_path)

    db.set_progress("week03", "completed", 10, 91.5)

    stored = db.all_progress()["week03"]
    assert stored["status"] == "completed"
    assert stored["percent"] == 100
    assert stored["score"] == 91.5


def test_percent_is_clamped_to_the_valid_range(tmp_path):
    db = _db(tmp_path)

    db.set_progress("week04", "in_progress", -5, None)
    assert db.all_progress()["week04"]["percent"] == 0

    db.set_progress("week05", "in_progress", 1000, None)
    assert db.all_progress()["week05"]["percent"] == 100


def test_export_json_contains_the_learning_tables(tmp_path):
    db = _db(tmp_path)
    db.set_progress("week01", "in_progress", 30, None)
    db.save_thought(None, title="note", content="body", tags="t", lesson_key="week01", language="zh-CN")

    payload = json.loads(db.export_json())

    assert set(payload) == {"lesson_progress", "thoughts", "resources"}
    assert payload["lesson_progress"][0]["lesson_key"] == "week01"
    assert payload["thoughts"][0]["title"] == "note"
