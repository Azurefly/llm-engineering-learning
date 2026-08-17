from app import adaptive, adaptive_v5, exam_v2, exam_v3
from app.current import app  # noqa: F401
from app.question_snapshot import _create_attempt_snapshot, _selected_questions_snapshot


def test_snapshot_hooks_cover_all_exam_runtime_modules():
    assert exam_v2._create_attempt is _create_attempt_snapshot
    assert exam_v2._selected_questions is _selected_questions_snapshot
    assert exam_v3._create_attempt is _create_attempt_snapshot
    assert exam_v3._selected_questions is _selected_questions_snapshot
    assert adaptive._create_attempt is _create_attempt_snapshot
    assert adaptive._selected_questions is _selected_questions_snapshot
    assert adaptive_v5._create_attempt is _create_attempt_snapshot
    assert adaptive_v5._selected_questions is _selected_questions_snapshot
