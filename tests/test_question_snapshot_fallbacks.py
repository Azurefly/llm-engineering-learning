"""Snapshot fallback behaviour: corrupt snapshots must degrade, never crash."""

import sys

from fastapi.testclient import TestClient

from app import question_snapshot
from app.current import app
from app.exam_v2 import db

client = TestClient(app)


def _start_attempt() -> int:
    started = client.post("/exams/week03/random-start", follow_redirects=False)
    assert started.status_code == 303
    return int(started.headers["location"].rsplit("/", 1)[-1])


def _cleanup(attempt_id: int) -> None:
    with db.connect() as conn:
        conn.execute("DELETE FROM exam_question_snapshots WHERE attempt_id=?", (attempt_id,))
        conn.execute("DELETE FROM exam_runtime WHERE attempt_id=?", (attempt_id,))
        conn.execute("DELETE FROM exam_answers WHERE attempt_id=?", (attempt_id,))
        conn.execute("DELETE FROM exam_attempt_questions WHERE attempt_id=?", (attempt_id,))
        conn.execute("DELETE FROM exam_v2_meta WHERE attempt_id=?", (attempt_id,))
        conn.execute("DELETE FROM exam_attempts WHERE id=?", (attempt_id,))


def test_corrupt_snapshot_json_falls_back_to_the_live_question_index():
    attempt_id = _start_attempt()
    try:
        with db.connect() as conn:
            conn.execute(
                """UPDATE exam_question_snapshots SET question_json='{not json'
                   WHERE attempt_id=? AND seq=(SELECT MIN(seq) FROM exam_question_snapshots WHERE attempt_id=?)""",
                (attempt_id, attempt_id),
            )

        items = question_snapshot._selected_questions_snapshot(attempt_id)

        assert items
        assert all(item["question"] is not None for item in items)
        assert all("question_json" not in item for item in items)
    finally:
        _cleanup(attempt_id)


def test_unknown_question_ids_are_skipped_instead_of_crashing():
    attempt_id = _start_attempt()
    try:
        with db.connect() as conn:
            conn.execute(
                "UPDATE exam_attempt_questions SET question_id='no-such-question' WHERE attempt_id=?",
                (attempt_id,),
            )
            conn.execute(
                "UPDATE exam_question_snapshots SET question_json='{broken', question_id='no-such-question' WHERE attempt_id=?",
                (attempt_id,),
            )

        assert question_snapshot._selected_questions_snapshot(attempt_id) == []
    finally:
        _cleanup(attempt_id)


def test_invalid_knowledge_payload_degrades_to_an_empty_list():
    attempt_id = _start_attempt()
    try:
        with db.connect() as conn:
            conn.execute(
                "UPDATE exam_attempt_questions SET knowledge_json='not-json' WHERE attempt_id=?",
                (attempt_id,),
            )

        items = question_snapshot._selected_questions_snapshot(attempt_id)

        assert items
        assert all(item["knowledge"] == [] for item in items)
    finally:
        _cleanup(attempt_id)


def test_install_skips_modules_that_are_not_imported(monkeypatch):
    monkeypatch.setitem(sys.modules, "app.exam_v3", None)

    question_snapshot.install()

    assert question_snapshot.exam_v2._create_attempt is question_snapshot._create_attempt_snapshot
    assert question_snapshot.exam_v2._selected_questions is question_snapshot._selected_questions_snapshot
