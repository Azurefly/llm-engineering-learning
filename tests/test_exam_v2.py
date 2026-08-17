from fastapi.testclient import TestClient

from app.code_runner import CodeRunRequest, DisabledCodeRunner
from app.exam_v2 import STAGES, _choose_balanced, bank_for, db, difficulty_for
from app.main_v2 import app

client = TestClient(app)


def test_question_bank_is_expanded_for_advanced_weeks():
    bank = bank_for("week03")
    assert len(bank) >= 7
    levels = {difficulty_for(q) for q in bank}
    assert {"easy", "medium", "hard"}.issubset(levels)


def test_balanced_random_selection_has_multiple_difficulty_levels():
    pool = [("week03", q) for q in bank_for("week03")]
    selected = _choose_balanced(pool, 6, seed=20260817)
    assert len(selected) == 6
    levels = [difficulty_for(q) for _, q in selected]
    assert "hard" in levels
    assert "medium" in levels
    assert "easy" in levels


def test_stage_exam_plan_covers_full_curriculum():
    covered = {week for stage in STAGES for week in stage.weeks}
    assert covered == {f"week{i:02d}" for i in range(19)}


def test_exam_v2_pages_are_available():
    assert client.get("/exam-lab").status_code == 200
    assert client.get("/mistakes").status_code == 200
    assert client.get("/exam-history").status_code == 200
    assert client.get("/stage-exams").status_code == 200
    assert client.get("/question-bank").status_code == 200


def test_random_exam_creates_snapshot_and_can_be_opened():
    response = client.post("/exams/week03/random-start", follow_redirects=False)
    assert response.status_code == 303
    location = response.headers["location"]
    assert location.startswith("/exam-v2/attempt/")
    attempt_id = int(location.rsplit("/", 1)[-1])
    try:
        page = client.get(location)
        assert page.status_code == 200
        with db.connect() as conn:
            count = conn.execute(
                "SELECT COUNT(*) FROM exam_attempt_questions WHERE attempt_id=?",
                (attempt_id,),
            ).fetchone()[0]
        assert count == 6
    finally:
        with db.connect() as conn:
            conn.execute("DELETE FROM exam_answers WHERE attempt_id=?", (attempt_id,))
            conn.execute("DELETE FROM exam_attempt_questions WHERE attempt_id=?", (attempt_id,))
            conn.execute("DELETE FROM exam_v2_meta WHERE attempt_id=?", (attempt_id,))
            conn.execute("DELETE FROM exam_attempts WHERE id=?", (attempt_id,))


def test_code_runner_is_safe_by_default(tmp_path):
    result = DisabledCodeRunner().run(CodeRunRequest("print('hello')"), tmp_path)
    assert result.enabled is False
    assert result.passed is False
    assert result.exit_code is None
