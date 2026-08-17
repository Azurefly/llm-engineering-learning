from app import adaptive, adaptive_v5, exam_v2, exam_v3
from app.current import app  # noqa: F401
from app.question_snapshot import _create_attempt_snapshot, _selected_questions_snapshot


def test_snapshot_hooks_cover_all_exam_runtime_modules():
    assert exam_v2._create_attempt is _create_attempt_snapshot
    assert exam_v2._selected_questions is _selected_questions_snapshot
    assert exam_v3._create_attempt is _create_attempt_snapshot
    assert exam_v3._selected_questions is _selected_questions_snapshot
    assert adaptive_v5._create_attempt is _create_attempt_snapshot
    assert adaptive_v5._selected_questions is _selected_questions_snapshot

    # V4 adaptive review currently delegates creation through exam_v2 helpers
    # instead of importing both functions by name. Only assert aliases that the
    # module actually owns so this test protects behavior without inventing API.
    if hasattr(adaptive, "_create_attempt"):
        assert adaptive._create_attempt is _create_attempt_snapshot
    if hasattr(adaptive, "_selected_questions"):
        assert adaptive._selected_questions is _selected_questions_snapshot
