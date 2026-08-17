from app.current import app  # noqa: F401 - installs the expanded bank
from app.bank_quality import MIN_QUESTIONS_PER_WEEK, validate_question_bank


def test_question_bank_quality_gate():
    report = validate_question_bank()
    assert report["ok"], "\n".join(report["errors"])
    assert report["total"] >= 180
    assert all(item["count"] >= MIN_QUESTIONS_PER_WEEK for item in report["weeks"])
