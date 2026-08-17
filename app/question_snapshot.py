from __future__ import annotations

import json
import sys
from typing import Any

from . import exam_v2
from .exam_system import Question

_ORIGINAL_CREATE = exam_v2._create_attempt
_ORIGINAL_SELECTED = exam_v2._selected_questions


def _question_to_dict(q: Question) -> dict[str, Any]:
    return {
        "id": q.id,
        "kind": q.kind,
        "points": q.points,
        "zh": q.zh,
        "en": q.en,
        "options": [list(x) for x in q.options],
        "answer": list(q.answer) if isinstance(q.answer, tuple) else q.answer,
        "accepted": list(q.accepted),
        "concepts": [list(x) for x in q.concepts],
    }


def _question_from_dict(value: dict[str, Any]) -> Question:
    answer = value.get("answer")
    if value.get("kind") == "multiple" and isinstance(answer, list):
        answer = tuple(answer)
    return Question(
        id=str(value["id"]),
        kind=str(value["kind"]),
        points=float(value["points"]),
        zh=str(value["zh"]),
        en=str(value["en"]),
        options=tuple(tuple(str(y) for y in x) for x in value.get("options") or []),
        answer=answer,
        accepted=tuple(str(x) for x in value.get("accepted") or []),
        concepts=tuple(tuple(str(y) for y in x) for x in value.get("concepts") or []),
    )


def init_tables() -> None:
    with exam_v2.db.connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS exam_question_snapshots(
                attempt_id INTEGER NOT NULL,
                seq INTEGER NOT NULL,
                question_id TEXT NOT NULL,
                question_json TEXT NOT NULL,
                PRIMARY KEY(attempt_id, seq)
            );
            CREATE INDEX IF NOT EXISTS idx_exam_question_snapshots_qid
                ON exam_question_snapshots(question_id);
            """
        )


init_tables()


def _create_attempt_snapshot(*, lesson_key: str, lang: str, mode: str, scope_key: str, title_zh: str, title_en: str,
                             selected: list[tuple[str, Question]], pass_score: int, seed: int) -> int:
    attempt_id = _ORIGINAL_CREATE(
        lesson_key=lesson_key,
        lang=lang,
        mode=mode,
        scope_key=scope_key,
        title_zh=title_zh,
        title_en=title_en,
        selected=selected,
        pass_score=pass_score,
        seed=seed,
    )
    with exam_v2.db.connect() as conn:
        for seq, (_, question) in enumerate(selected, 1):
            conn.execute(
                """INSERT OR REPLACE INTO exam_question_snapshots(attempt_id,seq,question_id,question_json)
                   VALUES(?,?,?,?)""",
                (attempt_id, seq, question.id, json.dumps(_question_to_dict(question), ensure_ascii=False)),
            )
    return attempt_id


def _selected_questions_snapshot(attempt_id: int) -> list[dict[str, Any]]:
    with exam_v2.db.connect() as conn:
        rows = conn.execute(
            """SELECT aq.seq,aq.lesson_key,aq.question_id,aq.difficulty,aq.knowledge_json,s.question_json
               FROM exam_attempt_questions aq
               LEFT JOIN exam_question_snapshots s ON s.attempt_id=aq.attempt_id AND s.seq=aq.seq
               WHERE aq.attempt_id=? ORDER BY aq.seq""",
            (attempt_id,),
        ).fetchall()
    result: list[dict[str, Any]] = []
    for raw in rows:
        item = dict(raw)
        question: Question | None = None
        if item.get("question_json"):
            try:
                question = _question_from_dict(json.loads(item["question_json"]))
            except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                question = None
        if question is None:
            indexed = exam_v2.QUESTION_INDEX.get(item["question_id"])
            question = indexed[1] if indexed else None
        if question is None:
            continue
        item.pop("question_json", None)
        item["question"] = question
        try:
            item["knowledge"] = json.loads(item.pop("knowledge_json"))
        except (TypeError, json.JSONDecodeError):
            item["knowledge"] = []
        result.append(item)
    return result


def install() -> None:
    """Install snapshot-aware functions everywhere they may have been imported by name.

    Pytest and application modules may import versioned routers in different orders.
    Patching their module globals makes the behavior deterministic regardless of import order.
    """
    exam_v2._create_attempt = _create_attempt_snapshot
    exam_v2._selected_questions = _selected_questions_snapshot
    for module_name in ("app.exam_v3", "app.adaptive", "app.adaptive_v5"):
        module = sys.modules.get(module_name)
        if module is None:
            continue
        if hasattr(module, "_create_attempt"):
            setattr(module, "_create_attempt", _create_attempt_snapshot)
        if hasattr(module, "_selected_questions"):
            setattr(module, "_selected_questions", _selected_questions_snapshot)


install()
