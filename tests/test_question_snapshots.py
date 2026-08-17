from dataclasses import replace

from fastapi.testclient import TestClient

from app.current import app
from app import exam_v2

client = TestClient(app)


def _cleanup(attempt_id: int) -> None:
    with exam_v2.db.connect() as conn:
        for table in ("exam_runtime", "exam_answers", "exam_question_snapshots", "exam_attempt_questions", "exam_v2_meta"):
            conn.execute(f"DELETE FROM {table} WHERE attempt_id=?", (attempt_id,))
        conn.execute("DELETE FROM exam_attempts WHERE id=?", (attempt_id,))


def test_new_exam_freezes_question_content():
    started = client.post("/exams/week03/random-start", follow_redirects=False)
    assert started.status_code == 303
    attempt_id = int(started.headers["location"].rsplit("/", 1)[-1])
    try:
        with exam_v2.db.connect() as conn:
            snapshots = conn.execute("SELECT COUNT(*) FROM exam_question_snapshots WHERE attempt_id=?", (attempt_id,)).fetchone()[0]
            first = conn.execute(
                "SELECT question_id FROM exam_attempt_questions WHERE attempt_id=? ORDER BY seq LIMIT 1",
                (attempt_id,),
            ).fetchone()[0]
        assert snapshots > 0

        lesson_key, original = exam_v2.QUESTION_INDEX[first]
        exam_v2.QUESTION_INDEX[first] = (lesson_key, replace(original, zh="CHANGED AFTER EXAM", en="CHANGED AFTER EXAM"))
        try:
            selected = exam_v2._selected_questions(attempt_id)
            frozen = next(x["question"] for x in selected if x["question_id"] == first)
            assert frozen.zh == original.zh
            assert frozen.en == original.en
        finally:
            exam_v2.QUESTION_INDEX[first] = (lesson_key, original)
    finally:
        _cleanup(attempt_id)
