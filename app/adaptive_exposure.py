from __future__ import annotations

from collections import defaultdict

from . import adaptive_v5


def question_exposure_once() -> dict[str, int]:
    """Count each adaptive item once even after it is materialized as an exam attempt."""
    counts: dict[str, int] = defaultdict(int)
    with adaptive_v5.db.connect() as conn:
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        if "exam_attempt_questions" in tables:
            if "exam_v2_meta" in tables:
                rows = conn.execute(
                    """SELECT aq.question_id, COUNT(*)
                       FROM exam_attempt_questions aq
                       LEFT JOIN exam_v2_meta m ON m.attempt_id=aq.attempt_id
                       WHERE COALESCE(m.mode,'') <> 'adaptive-sequential'
                       GROUP BY aq.question_id"""
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT question_id,COUNT(*) FROM exam_attempt_questions GROUP BY question_id"
                ).fetchall()
            for row in rows:
                counts[str(row[0])] += int(row[1])
        if "adaptive_session_items" in tables:
            for row in conn.execute(
                "SELECT question_id,COUNT(*) FROM adaptive_session_items GROUP BY question_id"
            ).fetchall():
                counts[str(row[0])] += int(row[1])
    return dict(counts)


def install() -> None:
    adaptive_v5._question_exposure = question_exposure_once


install()
