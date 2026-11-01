import pytest
from fastapi.testclient import TestClient

from app import exam_v3
from app.exam_v2 import STAGES, db
from app.main_v3 import app

client = TestClient(app)


def _cleanup_attempt(attempt_id: int) -> None:
    with db.connect() as conn:
        conn.execute("DELETE FROM exam_runtime WHERE attempt_id=?", (attempt_id,))
        conn.execute("DELETE FROM exam_answers WHERE attempt_id=?", (attempt_id,))
        conn.execute("DELETE FROM exam_attempt_questions WHERE attempt_id=?", (attempt_id,))
        conn.execute("DELETE FROM exam_v2_meta WHERE attempt_id=?", (attempt_id,))
        conn.execute("DELETE FROM exam_attempts WHERE id=?", (attempt_id,))


def _start_weekly(lesson_key: str = "week03") -> int:
    started = client.post(f"/exams/{lesson_key}/random-start", follow_redirects=False)
    assert started.status_code == 303
    return int(started.headers["location"].rsplit("/", 1)[-1])


def _force_deadline_into_the_past(attempt_id: int) -> None:
    # Deadlines are written as timezone-aware ISO strings, so the override must
    # be aware too, otherwise the remaining-time arithmetic is not comparable.
    with db.connect() as conn:
        conn.execute(
            "UPDATE exam_runtime SET deadline_at=? WHERE attempt_id=?",
            ("2000-01-01T00:00:00+00:00", attempt_id),
        )


def _attempt_status(attempt_id: int) -> tuple[str, int]:
    with db.connect() as conn:
        status = conn.execute("SELECT status FROM exam_attempts WHERE id=?", (attempt_id,)).fetchone()["status"]
        auto = conn.execute("SELECT auto_submitted FROM exam_runtime WHERE attempt_id=?", (attempt_id,)).fetchone()["auto_submitted"]
    return status, auto


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


def test_stage_exam_start_creates_a_timed_attempt():
    stage_key = STAGES[0].key
    started = client.post(f"/stage-exams/{stage_key}/start", follow_redirects=False)
    assert started.status_code == 303
    attempt_id = int(started.headers["location"].rsplit("/", 1)[-1])
    try:
        page = client.get(f"/exam-v2/attempt/{attempt_id}")
        assert page.status_code == 200
        assert "V3" in page.text
        state = client.get(f"/exam-runtime/{attempt_id}/state").json()
        assert state["status"] == "started"
        assert state["remaining_seconds"] > 0
    finally:
        _cleanup_attempt(attempt_id)


def test_exam_starts_reject_unknown_targets():
    assert client.post("/stage-exams/no-such-stage/start", follow_redirects=False).status_code == 404
    assert client.post("/exams/week99/random-start", follow_redirects=False).status_code == 404


def test_unknown_attempts_are_rejected_everywhere():
    assert client.get("/exam-v2/attempt/99999999", follow_redirects=False).status_code == 404
    assert client.post("/exam-v2/attempt/99999999/submit", data={}, follow_redirects=False).status_code == 404
    assert client.get("/exam-runtime/99999999/state", follow_redirects=False).status_code == 404
    assert client.post("/exam-runtime/99999999/expire", follow_redirects=False).status_code == 404


def test_submitted_attempt_redirects_instead_of_reopening():
    attempt_id = _start_weekly()
    try:
        assert client.post(f"/exam-v2/attempt/{attempt_id}/submit", data={}, follow_redirects=False).status_code == 303

        reopened = client.get(f"/exam-v2/attempt/{attempt_id}", follow_redirects=False)
        assert reopened.status_code == 303
        assert reopened.headers["location"] == f"/exam-v2/attempt/{attempt_id}/result"

        resubmitted = client.post(f"/exam-v2/attempt/{attempt_id}/submit", data={}, follow_redirects=False)
        assert resubmitted.status_code == 303
        assert resubmitted.headers["location"] == f"/exam-v2/attempt/{attempt_id}/result"
    finally:
        _cleanup_attempt(attempt_id)


def test_opening_an_expired_attempt_auto_submits_it():
    attempt_id = _start_weekly()
    try:
        _force_deadline_into_the_past(attempt_id)

        response = client.get(f"/exam-v2/attempt/{attempt_id}", follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"] == f"/exam-v2/attempt/{attempt_id}/result"
        assert _attempt_status(attempt_id) == ("submitted", 1)
    finally:
        _cleanup_attempt(attempt_id)


def test_submitting_after_the_deadline_auto_submits_instead_of_grading_form_data():
    attempt_id = _start_weekly()
    try:
        _force_deadline_into_the_past(attempt_id)

        response = client.post(f"/exam-v2/attempt/{attempt_id}/submit", data={}, follow_redirects=False)
        assert response.status_code == 303
        assert _attempt_status(attempt_id) == ("submitted", 1)
    finally:
        _cleanup_attempt(attempt_id)


def test_autosave_rejects_attempts_that_are_no_longer_active():
    attempt_id = _start_weekly()
    try:
        client.post(f"/exam-v2/attempt/{attempt_id}/submit", data={}, follow_redirects=False)

        response = client.post(f"/exam-runtime/{attempt_id}/autosave", json={"answers": {}})
        assert response.status_code == 409
        assert "not active" in response.text.lower()
    finally:
        _cleanup_attempt(attempt_id)


def test_autosave_reports_expiry_and_submits_the_attempt():
    attempt_id = _start_weekly()
    try:
        _force_deadline_into_the_past(attempt_id)

        response = client.post(f"/exam-runtime/{attempt_id}/autosave", json={"answers": {}})
        assert response.status_code == 409
        payload = response.json()
        assert payload["status"] == "expired"
        assert payload["redirect"] == f"/exam-v2/attempt/{attempt_id}/result"
        assert _attempt_status(attempt_id) == ("submitted", 1)
    finally:
        _cleanup_attempt(attempt_id)


def test_autosave_tolerates_a_non_json_body():
    attempt_id = _start_weekly()
    try:
        response = client.post(
            f"/exam-runtime/{attempt_id}/autosave",
            content="this is not json",
            headers={"content-type": "text/plain"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "saved"
    finally:
        _cleanup_attempt(attempt_id)


def test_expire_endpoint_submits_an_open_attempt_once():
    attempt_id = _start_weekly()
    try:
        first = client.post(f"/exam-runtime/{attempt_id}/expire")
        assert first.status_code == 200
        assert first.json() == {"status": "submitted", "redirect": f"/exam-v2/attempt/{attempt_id}/result"}
        assert _attempt_status(attempt_id)[0] == "submitted"

        again = client.post(f"/exam-runtime/{attempt_id}/expire")
        assert again.status_code == 200
        assert again.json()["status"] == "submitted"
    finally:
        _cleanup_attempt(attempt_id)


def test_mistake_practice_builds_an_attempt_from_unresolved_questions():
    weekly_id = _start_weekly()
    mistake_id = None
    try:
        client.post(f"/exam-v2/attempt/{weekly_id}/submit", data={}, follow_redirects=False)

        started = client.post("/mistakes/start", follow_redirects=False)
        assert started.status_code == 303
        mistake_id = int(started.headers["location"].rsplit("/", 1)[-1])
        assert client.get(f"/exam-v2/attempt/{mistake_id}").status_code == 200
    finally:
        if mistake_id is not None:
            _cleanup_attempt(mistake_id)
        _cleanup_attempt(weekly_id)


def test_mistake_practice_redirects_when_nothing_is_unresolved(monkeypatch):
    monkeypatch.setattr(exam_v3, "_latest_question_state", list)
    response = client.post("/mistakes/start", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/mistakes"


@pytest.mark.parametrize(
    ("mode", "configured", "expected_seconds"),
    [
        ("weekly", None, 30 * 60),
        ("stage", None, 50 * 60),
        ("mistakes", None, 20 * 60),
        ("weekly", "not-a-number", 30 * 60),
        ("weekly", "1", 5 * 60),
        ("weekly", "9999", 180 * 60),
        ("weekly", "45", 45 * 60),
    ],
)
def test_exam_duration_is_configurable_and_clamped(monkeypatch, mode, configured, expected_seconds):
    variable = {"weekly": "LLM_EXAM_WEEKLY_MINUTES", "stage": "LLM_EXAM_STAGE_MINUTES", "mistakes": "LLM_EXAM_MISTAKE_MINUTES"}[mode]
    if configured is None:
        monkeypatch.delenv(variable, raising=False)
    else:
        monkeypatch.setenv(variable, configured)
    assert exam_v3._duration_seconds(mode) == expected_seconds


def test_draft_falls_back_to_empty_mapping_on_corrupt_json():
    assert exam_v3._draft({"draft_json": "{not json"}) == {}
    assert exam_v3._draft({"draft_json": '["a"]'}) == {}
    assert exam_v3._draft({"draft_json": '{"q1": "a"}'}) == {"q1": "a"}
