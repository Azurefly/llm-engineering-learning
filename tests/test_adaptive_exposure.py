from app.adaptive_exposure import question_exposure_once
from app.current import app  # noqa: F401
from app.db import now_iso
from app.exam_v2 import db


def test_completed_cat_item_is_not_double_counted():
    qid = "exposure-policy-probe"
    with db.connect() as conn:
        adaptive_attempt = conn.execute(
            "INSERT INTO exam_attempts(lesson_key,language,status,started_at) VALUES(?,?,?,?)",
            ("adaptive-test", "en", "submitted", now_iso()),
        ).lastrowid
        conn.execute(
            "INSERT INTO exam_v2_meta(attempt_id,mode,scope_key,title_zh,title_en,seed,created_at) VALUES(?,?,?,?,?,?,?)",
            (adaptive_attempt, "adaptive-sequential", "adaptive-test", "probe", "probe", 1, now_iso()),
        )
        conn.execute(
            "INSERT INTO exam_attempt_questions(attempt_id,seq,lesson_key,question_id,difficulty,knowledge_json) VALUES(?,?,?,?,?,?)",
            (adaptive_attempt, 1, "week01", qid, "easy", "[]"),
        )
        session_id = conn.execute(
            "INSERT INTO adaptive_sessions(language,status,target_tags_json,max_items,seed,started_at,completed_at,exam_attempt_id) VALUES(?,?,?,?,?,?,?,?)",
            ("en", "completed", "[]", 1, 1, now_iso(), now_iso(), adaptive_attempt),
        ).lastrowid
        conn.execute(
            "INSERT INTO adaptive_session_items(session_id,seq,lesson_key,question_id,difficulty,knowledge_json,answer_json,score_percent,created_at,answered_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
            (session_id, 1, "week01", qid, "easy", "[]", '"x"', 0, now_iso(), now_iso()),
        )

        ordinary_attempt = conn.execute(
            "INSERT INTO exam_attempts(lesson_key,language,status,started_at) VALUES(?,?,?,?)",
            ("week01", "en", "submitted", now_iso()),
        ).lastrowid
        conn.execute(
            "INSERT INTO exam_v2_meta(attempt_id,mode,scope_key,title_zh,title_en,seed,created_at) VALUES(?,?,?,?,?,?,?)",
            (ordinary_attempt, "weekly", "week01", "probe", "probe", 2, now_iso()),
        )
        conn.execute(
            "INSERT INTO exam_attempt_questions(attempt_id,seq,lesson_key,question_id,difficulty,knowledge_json) VALUES(?,?,?,?,?,?)",
            (ordinary_attempt, 1, "week01", qid, "easy", "[]"),
        )

    try:
        # One exposure comes from the CAT session itself and one from the ordinary
        # exam. The materialized adaptive exam row must not add a third count.
        assert question_exposure_once()[qid] == 2
    finally:
        with db.connect() as conn:
            conn.execute("DELETE FROM adaptive_session_items WHERE session_id=?", (session_id,))
            conn.execute("DELETE FROM adaptive_sessions WHERE id=?", (session_id,))
            for attempt_id in (adaptive_attempt, ordinary_attempt):
                conn.execute("DELETE FROM exam_attempt_questions WHERE attempt_id=?", (attempt_id,))
                conn.execute("DELETE FROM exam_v2_meta WHERE attempt_id=?", (attempt_id,))
                conn.execute("DELETE FROM exam_attempts WHERE id=?", (attempt_id,))
