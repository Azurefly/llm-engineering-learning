"""Coverage for the V2 exam entrypoint.

``app/current.py`` registers V3 before V2, so V3 deliberately shadows the
compatible V2 paths (random start, stage start, mistake start, take, submit).
The V2 router is still a supported entrypoint (``app/main_v2.py``), so these
tests mount it on a dedicated app to exercise that code path directly.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.exam_v2 import STAGES, _display_answer, _history_stats, db
from app.exam_v2 import router as exam_v2_router

legacy_app = FastAPI()
legacy_app.include_router(exam_v2_router)
client = TestClient(legacy_app)


def _attempt_id(location: str) -> int:
    return int(location.rsplit("/", 1)[-1])


def _cleanup(attempt_id: int) -> None:
    with db.connect() as conn:
        conn.execute("DELETE FROM exam_answers WHERE attempt_id=?", (attempt_id,))
        conn.execute("DELETE FROM exam_attempt_questions WHERE attempt_id=?", (attempt_id,))
        conn.execute("DELETE FROM exam_v2_meta WHERE attempt_id=?", (attempt_id,))
        conn.execute("DELETE FROM exam_attempts WHERE id=?", (attempt_id,))


@pytest.fixture
def weekly_attempt():
    started = client.post("/exams/week03/random-start", follow_redirects=False)
    assert started.status_code == 303
    attempt_id = _attempt_id(started.headers["location"])
    yield attempt_id
    _cleanup(attempt_id)


def test_random_weekly_exam_renders_the_v2_attempt_page(weekly_attempt):
    page = client.get(f"/exam-v2/attempt/{weekly_attempt}")
    assert page.status_code == 200
    assert "Week 3" in page.text or "Week 03" in page.text or "第 3" in page.text


def test_random_weekly_exam_rejects_unknown_lesson():
    response = client.post("/exams/week99/random-start", follow_redirects=False)
    assert response.status_code == 404


def test_submitting_a_legacy_exam_scores_and_redirects_to_result(weekly_attempt):
    submitted = client.post(f"/exam-v2/attempt/{weekly_attempt}/submit", data={}, follow_redirects=False)
    assert submitted.status_code == 303
    assert submitted.headers["location"] == f"/exam-v2/attempt/{weekly_attempt}/result"

    result = client.get(f"/exam-v2/attempt/{weekly_attempt}/result")
    assert result.status_code == 200


def test_resubmitting_a_submitted_exam_redirects_to_the_result(weekly_attempt):
    client.post(f"/exam-v2/attempt/{weekly_attempt}/submit", data={}, follow_redirects=False)

    page = client.get(f"/exam-v2/attempt/{weekly_attempt}", follow_redirects=False)
    assert page.status_code == 303
    assert page.headers["location"] == f"/exam-v2/attempt/{weekly_attempt}/result"

    again = client.post(f"/exam-v2/attempt/{weekly_attempt}/submit", data={}, follow_redirects=False)
    assert again.status_code == 303
    assert again.headers["location"] == f"/exam-v2/attempt/{weekly_attempt}/result"


def test_result_page_redirects_back_while_the_attempt_is_open(weekly_attempt):
    response = client.get(f"/exam-v2/attempt/{weekly_attempt}/result", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == f"/exam-v2/attempt/{weekly_attempt}"


def test_compatible_result_route_forwards_v2_attempts_to_the_v2_result(weekly_attempt):
    response = client.get(f"/exam-results/{weekly_attempt}", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == f"/exam-v2/attempt/{weekly_attempt}/result"


def test_compatible_result_route_rejects_unknown_attempts():
    assert client.get("/exam-results/99999999", follow_redirects=False).status_code == 404


@pytest.mark.parametrize("path", ["/exam-v2/attempt/99999999", "/exam-v2/attempt/99999999/result"])
def test_unknown_attempts_are_not_found(path):
    assert client.get(path, follow_redirects=False).status_code == 404


def test_unknown_attempt_submission_is_not_found():
    response = client.post("/exam-v2/attempt/99999999/submit", data={}, follow_redirects=False)
    assert response.status_code == 404


def test_stage_exam_can_be_started_and_is_cleaned_up():
    stage_key = STAGES[0].key
    started = client.post(f"/stage-exams/{stage_key}/start", follow_redirects=False)
    assert started.status_code == 303
    attempt_id = _attempt_id(started.headers["location"])
    try:
        assert client.get(f"/exam-v2/attempt/{attempt_id}").status_code == 200
    finally:
        _cleanup(attempt_id)


def test_stage_exam_rejects_unknown_stage():
    assert client.post("/stage-exams/no-such-stage/start", follow_redirects=False).status_code == 404


def test_mistake_practice_redirects_when_nothing_is_unresolved(monkeypatch):
    monkeypatch.setattr("app.exam_v2._latest_question_state", list)
    response = client.post("/mistakes/start", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/mistakes"


def test_mistake_practice_builds_an_attempt_from_wrong_answers(weekly_attempt):
    client.post(f"/exam-v2/attempt/{weekly_attempt}/submit", data={}, follow_redirects=False)

    started = client.post("/mistakes/start", follow_redirects=False)
    assert started.status_code == 303
    attempt_id = _attempt_id(started.headers["location"])
    try:
        assert client.get(f"/exam-v2/attempt/{attempt_id}").status_code == 200
    finally:
        _cleanup(attempt_id)


@pytest.mark.parametrize(
    "path",
    ["/exam-lab", "/stage-exams", "/mistakes", "/exam-history", "/question-bank"],
)
def test_legacy_exam_pages_render(path):
    response = client.get(path)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")


def test_display_answer_renders_multi_select_and_empty_answers():
    assert _display_answer(["a", "c"]) == "a, c"
    assert _display_answer("42") == "42"
    assert _display_answer(None) == ""


def test_history_stats_handles_an_empty_history():
    assert _history_stats([]) == {"count": 0, "passed": 0, "pass_rate": 0.0, "average": 0.0, "best": 0.0}
