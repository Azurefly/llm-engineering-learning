from fastapi.testclient import TestClient

from app.adaptive_v5 import _desired_difficulty, _session_tag_state, db
from app.current import app

client = TestClient(app)


def _cleanup(session_id: int) -> None:
    with db.connect() as conn:
        row = conn.execute("SELECT exam_attempt_id FROM adaptive_sessions WHERE id=?", (session_id,)).fetchone()
        attempt_id = int(row[0]) if row and row[0] else None
        conn.execute("DELETE FROM adaptive_session_items WHERE session_id=?", (session_id,))
        conn.execute("DELETE FROM adaptive_sessions WHERE id=?", (session_id,))
        if attempt_id:
            for table in ("exam_runtime", "exam_answers", "exam_question_snapshots", "exam_attempt_questions", "exam_v2_meta"):
                conn.execute(f"DELETE FROM {table} WHERE attempt_id=?", (attempt_id,))
            conn.execute("DELETE FROM exam_attempts WHERE id=?", (attempt_id,))


def test_difficulty_moves_with_mastery():
    assert _desired_difficulty(0) == "easy"
    assert _desired_difficulty(44.9) == "easy"
    assert _desired_difficulty(45) == "medium"
    assert _desired_difficulty(74.9) == "medium"
    assert _desired_difficulty(75) == "hard"


def test_zero_mastery_is_not_replaced_by_neutral_default(monkeypatch):
    monkeypatch.setattr("app.adaptive_v5.mastery_profile", lambda: {"Guardrails": {"score": 0.0, "evidence_count": 2}})
    state = _session_tag_state({"target_tags": ["Guardrails"]}, [])
    assert state["Guardrails"]["score"] == 0.0


def test_sequential_adaptive_session_is_resumable_and_immutable():
    started = client.post("/adaptive-test/start", follow_redirects=False)
    assert started.status_code == 303
    session_id = int(started.headers["location"].rsplit("/", 1)[-1])
    try:
        with db.connect() as conn:
            conn.execute("UPDATE adaptive_sessions SET max_items=2 WHERE id=?", (session_id,))

        first = client.get(f"/adaptive-test/{session_id}")
        assert first.status_code == 200
        assert "CAT" in first.text
        resumed = client.get('/adaptive-test')
        assert resumed.status_code == 200
        assert f"#{session_id}" in resumed.text

        with db.connect() as conn:
            first_row = conn.execute(
                "SELECT question_id,question_json FROM adaptive_session_items WHERE session_id=? AND seq=1",
                (session_id,),
            ).fetchone()
        assert first_row[0]
        assert first_row[1] and 'question' not in first_row[1].lower()

        answer1 = client.post(f"/adaptive-test/{session_id}/answer", data={}, follow_redirects=False)
        assert answer1.status_code == 303
        second = client.get(answer1.headers["location"])
        assert second.status_code == 200
        with db.connect() as conn:
            second_row = conn.execute(
                "SELECT question_id,question_json FROM adaptive_session_items WHERE session_id=? AND seq=2",
                (session_id,),
            ).fetchone()
        assert second_row[0] != first_row[0]
        assert second_row[1]

        answer2 = client.post(f"/adaptive-test/{session_id}/answer", data={}, follow_redirects=False)
        assert answer2.status_code == 303
        assert answer2.headers["location"].startswith("/exam-v2/attempt/")
        assert answer2.headers["location"].endswith("/result")

        with db.connect() as conn:
            session = conn.execute("SELECT status,exam_attempt_id FROM adaptive_sessions WHERE id=?", (session_id,)).fetchone()
            assert session[0] == "completed"
            attempt_id = int(session[1])
            mode = conn.execute("SELECT mode FROM exam_v2_meta WHERE attempt_id=?", (attempt_id,)).fetchone()[0]
            answer_count = conn.execute("SELECT COUNT(*) FROM exam_answers WHERE attempt_id=?", (attempt_id,)).fetchone()[0]
            snapshots = conn.execute("SELECT COUNT(*) FROM exam_question_snapshots WHERE attempt_id=?", (attempt_id,)).fetchone()[0]
        assert mode == "adaptive-sequential"
        assert answer_count == 2
        assert snapshots == 2
    finally:
        _cleanup(session_id)
