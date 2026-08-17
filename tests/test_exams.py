from fastapi.testclient import TestClient

from app.exam_system import EXAMS, grade_exam
from app.main import app, db

client = TestClient(app)


def test_week01_perfect_score_is_system_graded():
    result = grade_exam(
        EXAMS["week01"],
        {
            "w01q1": "a",
            "w01q2": ["oscillate", "diverge", "nan"],
            "w01q3": "false",
            "w01q4": "overfitting",
            "w01q5": "training fits parameters; validation selects the model; test measures final generalization",
            "w01q6": "learning rate controls update step size; too large can diverge; too small is slow",
        },
    )
    assert result["percent"] == 100
    assert result["passed"] is True


def test_short_answer_rubric_gives_partial_credit():
    result = grade_exam(EXAMS["week01"], {"w01q5": "training fits parameters; validation selects the model"})
    detail = next(x for x in result["details"] if x["question_id"] == "w01q5")
    assert 0 < detail["earned"] < detail["max_points"]
    assert detail["missing"]


def test_exam_web_flow_updates_course_progress_and_blocks_manual_completion():
    started = client.post("/exams/week03/start", follow_redirects=False)
    assert started.status_code == 303
    attempt_url = started.headers["location"]
    attempt_id = int(attempt_url.rsplit("/", 1)[-1])

    page = client.get(attempt_url)
    assert page.status_code == 200
    assert "SYSTEM-GRADED EXAM" in page.text

    submitted = client.post(
        f"/exams/attempt/{attempt_id}/submit",
        data={
            "q_week03q1": "true",
            "q_week03q2": "false",
            "q_week03q3": "true",
            "q_week03q4": "true",
        },
        follow_redirects=False,
    )
    assert submitted.status_code == 303

    report = client.get(submitted.headers["location"])
    assert report.status_code == 200
    assert "100.0%" in report.text

    progress = db.all_progress()["week03"]
    assert progress["status"] == "completed"
    assert progress["percent"] == 100
    assert progress["score"] == 100

    # A normal progress POST cannot overwrite a completed/system-scored lesson.
    client.post("/course/week03/progress", data={"percent": 1}, follow_redirects=False)
    after = db.all_progress()["week03"]
    assert after["status"] == "completed"
    assert after["percent"] == 100
    assert after["score"] == 100


def test_failed_exam_never_marks_course_complete():
    started = client.post("/exams/week04/start", follow_redirects=False)
    attempt_id = int(started.headers["location"].rsplit("/", 1)[-1])
    client.post(
        f"/exams/attempt/{attempt_id}/submit",
        data={
            "q_week04q1": "false",
            "q_week04q2": "false",
            "q_week04q3": "true",
            "q_week04q4": "true",
        },
        follow_redirects=False,
    )
    progress = db.all_progress()["week04"]
    assert progress["status"] != "completed"
    assert progress["percent"] <= 99
