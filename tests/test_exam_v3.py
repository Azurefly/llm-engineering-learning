from fastapi.testclient import TestClient

from app.exam_v2 import db
from app.main_v3 import app

client = TestClient(app)


def _cleanup_attempt(attempt_id: int) -> None:
    with db.connect() as conn:
        conn.execute("DELETE FROM exam_runtime WHERE attempt_id=?", (attempt_id,))
        conn.execute("DELETE FROM exam_answers WHERE attempt_id=?", (attempt_id,))
        conn.execute("DELETE FROM exam_attempt_questions WHERE attempt_id=?", (attempt_id,))
        conn.execute("DELETE FROM exam_v2_meta WHERE attempt_id=?", (attempt_id,))
        conn.execute("DELETE FROM exam_attempts WHERE id=?", (attempt_id,))


def test_exam_autosave_and_restore():
    started = client.post("/exams/week03/random-start", follow_redirects=False)
    attempt_id = int(started.headers["location"].rsplit("/", 1)[-1])
    try:
        with db.connect() as conn:
            row = conn.execute("SELECT question_id FROM exam_attempt_questions WHERE attempt_id=? ORDER BY seq LIMIT 1", (attempt_id,)).fetchone()
        assert row is not None
        qid = row["question_id"]
        saved = client.post(f"/exam-runtime/{attempt_id}/autosave", json={"answers": {qid: "true"}})
        assert saved.status_code == 200
        assert saved.json()["status"] == "saved"

        state = client.get(f"/exam-runtime/{attempt_id}/state")
        assert state.status_code == 200
        assert state.json()["remaining_seconds"] > 0

        page = client.get(f"/exam-v2/attempt/{attempt_id}")
        assert page.status_code == 200
        assert "V3" in page.text
    finally:
        _cleanup_attempt(attempt_id)


def test_code_lab_records_disabled_runner_result():
    before = None
    with db.connect() as conn:
        before = conn.execute("SELECT COALESCE(MAX(id),0) FROM code_attempts").fetchone()[0]
    response = client.post(
        "/coding-labs/week02/run",
        data={"source_code": "def stable_softmax(logits):\n    return [1/len(logits)]*len(logits)"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    location = response.headers["location"]
    page = client.get(location)
    assert page.status_code == 200
    assert "disabled" in page.text.lower() or "关闭" in page.text
    with db.connect() as conn:
        conn.execute("DELETE FROM code_attempts WHERE id>?", (before,))


def test_backup_contains_v3_tables():
    response = client.get("/backup.json")
    assert response.status_code == 200
    data = response.json()
    assert "exam_runtime" in data
    assert "code_attempts" in data
