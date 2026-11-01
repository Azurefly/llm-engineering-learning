"""The V1 weekly exam flow (exam centre, attempt, submit, result)."""

import pytest
from fastapi.testclient import TestClient

from app.current import app
from app.exam_system import Question, attempts, correct_text, exam_summary, grade_question
from app.exam_v2 import db

client = TestClient(app)

LESSON_KEY = "week00"


def _cleanup(attempt_id: int) -> None:
    with db.connect() as conn:
        conn.execute("DELETE FROM exam_answers WHERE attempt_id=?", (attempt_id,))
        conn.execute("DELETE FROM exam_attempts WHERE id=?", (attempt_id,))


def _start() -> int:
    started = client.post(f"/exams/{LESSON_KEY}/start", follow_redirects=False)
    assert started.status_code == 303
    return int(started.headers["location"].rsplit("/", 1)[-1])


def test_exam_centre_lists_the_weekly_exams():
    response = client.get("/exams")
    assert response.status_code == 200
    assert f"/exams/{LESSON_KEY}/start" in response.text


def test_starting_an_exam_creates_an_attempt():
    attempt_id = _start()
    try:
        page = client.get(f"/exams/attempt/{attempt_id}")
        assert page.status_code == 200
    finally:
        _cleanup(attempt_id)


def test_starting_an_unknown_exam_is_not_found():
    assert client.post("/exams/week99/start", follow_redirects=False).status_code == 404


def test_unknown_attempts_are_not_found():
    assert client.get("/exams/attempt/99999999", follow_redirects=False).status_code == 404
    assert client.post("/exams/attempt/99999999/submit", data={}, follow_redirects=False).status_code == 404
    assert client.get("/exams/attempt/99999999/result", follow_redirects=False).status_code == 404


def test_submitting_grades_the_attempt_and_reveals_the_result():
    attempt_id = _start()
    try:
        submitted = client.post(f"/exams/attempt/{attempt_id}/submit", data={}, follow_redirects=False)
        assert submitted.status_code == 303
        assert submitted.headers["location"] == f"/exams/attempt/{attempt_id}/result"

        result = client.get(f"/exams/attempt/{attempt_id}/result")
        assert result.status_code == 200

        reopened = client.get(f"/exams/attempt/{attempt_id}", follow_redirects=False)
        assert reopened.status_code == 303
        assert reopened.headers["location"] == f"/exams/attempt/{attempt_id}/result"

        resubmitted = client.post(f"/exams/attempt/{attempt_id}/submit", data={}, follow_redirects=False)
        assert resubmitted.status_code == 303
    finally:
        _cleanup(attempt_id)


def test_result_redirects_while_the_attempt_is_still_open():
    attempt_id = _start()
    try:
        response = client.get(f"/exams/attempt/{attempt_id}/result", follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"] == f"/exams/attempt/{attempt_id}"
    finally:
        _cleanup(attempt_id)


def test_exam_summary_is_none_for_lessons_without_an_exam():
    assert exam_summary("week99") is None
    assert exam_summary(LESSON_KEY) is not None


def test_attempts_can_be_listed_without_a_lesson_filter():
    rows = attempts()
    assert isinstance(rows, list)
    assert all("lesson_key" in row for row in rows)


def test_boolean_questions_are_graded_and_rendered():
    question = Question(id="bool-1", kind="boolean", points=2.0, zh="对还是错", en="true or false", answer=True)

    correct = grade_question(question, "true")
    wrong = grade_question(question, "false")

    assert correct["earned"] == 2.0
    assert correct["correct"] is True
    assert wrong["earned"] == 0
    assert correct_text(question, "en") == "True"
    assert correct_text(question, "zh-CN") == "正确"


def test_short_answer_questions_are_graded_by_rubric_concepts():
    question = Question(
        id="short-1",
        kind="short",
        points=4.0,
        zh="简述注意力",
        en="explain attention",
        concepts=(("query", "q"), ("key", "k"), ("value", "v")),
    )

    partial = grade_question(question, "query and key")
    full = grade_question(question, "query key value")

    assert partial["earned"] == pytest.approx(2.67)
    assert partial["correct"] is False
    assert full["earned"] == 4.0
    assert full["correct"] is True
    assert correct_text(question, "en") == "query, key, value"
