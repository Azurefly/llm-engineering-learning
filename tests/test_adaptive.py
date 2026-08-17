from fastapi.testclient import TestClient

from app.adaptive import DOMAINS, _mastery_from_evidence, domain_profile, mastery_profile
from app.exam_v2 import db
from app.main_v4 import app

client = TestClient(app)


def _cleanup_attempt(attempt_id: int) -> None:
    with db.connect() as conn:
        for table in ("exam_runtime", "exam_answers", "exam_attempt_questions", "exam_v2_meta"):
            conn.execute(f"DELETE FROM {table} WHERE attempt_id=?", (attempt_id,))
        conn.execute("DELETE FROM exam_attempts WHERE id=?", (attempt_id,))


def test_mastery_uses_recency_and_reports_confidence():
    summary = _mastery_from_evidence([
        {"score": 100, "source_weight": 1.0},
        {"score": 0, "source_weight": 1.0},
        {"score": 0, "source_weight": 1.0},
    ])
    assert 30 < summary["score"] < 50
    assert summary["evidence_count"] == 3
    assert summary["confidence"] == 0.6
    assert summary["status"] in {"weak", "developing"}


def test_domain_plan_covers_six_capability_areas():
    assert len(DOMAINS) == 6
    covered = {week for domain in DOMAINS for week in domain.weeks}
    assert covered == {f"week{i:02d}" for i in range(19)}
    assert len(domain_profile({}, "zh-CN")) == 6


def test_adaptive_dashboard_is_available():
    response = client.get("/adaptive")
    assert response.status_code == 200
    assert "V4" in response.text
    assert "masteryRadar" in response.text


def test_failed_exam_creates_weakness_renders_recommendation_and_builds_review_exam():
    started = client.post("/exams/week03/random-start", follow_redirects=False)
    assert started.status_code == 303
    failed_attempt = int(started.headers["location"].rsplit("/", 1)[-1])
    review_attempt = None
    try:
        submitted = client.post(
            f"/exam-v2/attempt/{failed_attempt}/submit",
            data={},
            follow_redirects=False,
        )
        assert submitted.status_code == 303
        profile = mastery_profile()
        assert any(item["status"] in {"weak", "developing"} for item in profile.values())

        page = client.get("/adaptive")
        assert page.status_code == 200
        assert "Week 3" in page.text
        assert "week03" in page.text

        review = client.post("/adaptive/review/start", follow_redirects=False)
        assert review.status_code == 303
        assert review.headers["location"].startswith("/exam-v2/attempt/")
        review_attempt = int(review.headers["location"].rsplit("/", 1)[-1])
        with db.connect() as conn:
            row = conn.execute("SELECT mode FROM exam_v2_meta WHERE attempt_id=?", (review_attempt,)).fetchone()
            count = conn.execute("SELECT COUNT(*) FROM exam_attempt_questions WHERE attempt_id=?", (review_attempt,)).fetchone()[0]
        assert row[0] == "adaptive"
        assert count > 0
    finally:
        if review_attempt is not None:
            _cleanup_attempt(review_attempt)
        _cleanup_attempt(failed_attempt)
