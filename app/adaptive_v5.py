from __future__ import annotations

import json
import random
import secrets
from collections import defaultdict
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from .adaptive import mastery_profile, recommendations
from .course import LESSONS
from .db import now_iso
from .exam_system import Question, grade_question
from .exam_v2 import (
    QUESTION_INDEX,
    _attempt,
    _create_attempt,
    _lang,
    _nav,
    _question_view,
    _save_submission,
    _selected_questions,
    bank_for,
    db,
    difficulty_for,
    knowledge_for,
    templates,
)

router = APIRouter()


def init_tables() -> None:
    with db.connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS adaptive_sessions(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                language TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'started',
                target_tags_json TEXT NOT NULL DEFAULT '[]',
                max_items INTEGER NOT NULL DEFAULT 12,
                seed INTEGER NOT NULL,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                exam_attempt_id INTEGER
            );
            CREATE TABLE IF NOT EXISTS adaptive_session_items(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                seq INTEGER NOT NULL,
                lesson_key TEXT NOT NULL,
                question_id TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                knowledge_json TEXT NOT NULL DEFAULT '[]',
                answer_json TEXT,
                score_percent REAL,
                created_at TEXT NOT NULL,
                answered_at TEXT,
                UNIQUE(session_id, seq),
                UNIQUE(session_id, question_id)
            );
            CREATE INDEX IF NOT EXISTS idx_adaptive_items_session
                ON adaptive_session_items(session_id, seq);
            """
        )


init_tables()


def _loads(value: str | None, fallback: Any) -> Any:
    try:
        return json.loads(value or "")
    except (TypeError, json.JSONDecodeError):
        return fallback


def _session(session_id: int) -> dict[str, Any] | None:
    with db.connect() as conn:
        row = conn.execute("SELECT * FROM adaptive_sessions WHERE id=?", (session_id,)).fetchone()
    if not row:
        return None
    item = dict(row)
    item["target_tags"] = _loads(item.pop("target_tags_json"), [])
    return item


def _items(session_id: int) -> list[dict[str, Any]]:
    with db.connect() as conn:
        rows = conn.execute("SELECT * FROM adaptive_session_items WHERE session_id=? ORDER BY seq", (session_id,)).fetchall()
    result: list[dict[str, Any]] = []
    for raw in rows:
        item = dict(raw)
        item["knowledge"] = _loads(item.pop("knowledge_json"), [])
        item["answer"] = _loads(item.get("answer_json"), None) if item.get("answer_json") is not None else None
        indexed = QUESTION_INDEX.get(item["question_id"])
        item["question"] = indexed[1] if indexed else None
        result.append(item)
    return result


def _question_exposure() -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    with db.connect() as conn:
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        if "exam_attempt_questions" in tables:
            for row in conn.execute("SELECT question_id,COUNT(*) FROM exam_attempt_questions GROUP BY question_id").fetchall():
                counts[str(row[0])] += int(row[1])
        if "adaptive_session_items" in tables:
            for row in conn.execute("SELECT question_id,COUNT(*) FROM adaptive_session_items GROUP BY question_id").fetchall():
                counts[str(row[0])] += int(row[1])
    return dict(counts)


def _default_targets(profile: dict[str, dict[str, Any]], limit: int = 5) -> list[str]:
    recs = recommendations(profile, limit=limit)
    if recs:
        return [str(x["tag"]) for x in recs]
    candidates = list(profile.values())
    candidates.sort(key=lambda x: (int(x.get("evidence_count") or 0), float(x.get("score") or 0), str(x.get("tag") or "")))
    return [str(x["tag"]) for x in candidates[:limit] if x.get("tag")]


def _session_tag_state(session: dict[str, Any], items: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    profile = mastery_profile()
    state: dict[str, dict[str, float]] = {}
    for tag in list(session.get("target_tags") or []):
        base = profile.get(tag, {})
        evidence = int(base.get("evidence_count") or 0)
        score = float(base.get("score")) if evidence and base.get("score") is not None else 50.0
        state[tag] = {"score": score, "evidence": float(evidence)}
    for item in items:
        if item.get("score_percent") is None:
            continue
        for tag in item.get("knowledge") or []:
            if tag not in state:
                continue
            old = state[tag]
            weight = min(4.0, 1.0 + old["evidence"] * 0.20)
            old["score"] = round((old["score"] * weight + float(item["score_percent"]) * 1.6) / (weight + 1.6), 2)
            old["evidence"] += 1
    return state


def _desired_difficulty(score: float) -> str:
    if score < 45:
        return "easy"
    if score < 75:
        return "medium"
    return "hard"


def _candidate_score(lesson_key: str, question: Question, state: dict[str, dict[str, float]], exposure: dict[str, int], used: set[str], rng: random.Random) -> float:
    if question.id in used:
        return -1e9
    tags = knowledge_for(lesson_key, question)
    matched = [state[tag] for tag in tags if tag in state]
    if not matched:
        return -1000 + rng.random()
    weakest = min(float(x["score"]) for x in matched)
    target_difficulty = _desired_difficulty(weakest)
    actual = difficulty_for(question)
    difficulty_bonus = 28.0 if actual == target_difficulty else 10.0
    weakness_bonus = 100.0 - weakest
    novelty_bonus = 28.0 / (1.0 + float(exposure.get(question.id, 0)))
    coverage_bonus = 8.0 * len(matched)
    return weakness_bonus + novelty_bonus + difficulty_bonus + coverage_bonus + rng.random() * 3.0


def _pick_next(session: dict[str, Any], items: list[dict[str, Any]]) -> tuple[str, Question] | None:
    state = _session_tag_state(session, items)
    used = {str(x["question_id"]) for x in items}
    exposure = _question_exposure()
    rng = random.Random(int(session["seed"]) + len(items) * 7919)
    candidates: list[tuple[float, str, Question]] = []
    for lesson in LESSONS:
        for question in bank_for(lesson.key):
            score = _candidate_score(lesson.key, question, state, exposure, used, rng)
            if score > -500:
                candidates.append((score, lesson.key, question))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0], reverse=True)
    head = candidates[: min(4, len(candidates))]
    _, lesson_key, question = rng.choice(head)
    return lesson_key, question


def _ensure_pending(session: dict[str, Any]) -> dict[str, Any] | None:
    items = _items(int(session["id"]))
    pending = next((x for x in items if x.get("answer_json") is None), None)
    if pending:
        return pending
    answered = [x for x in items if x.get("answer_json") is not None]
    if len(answered) >= int(session["max_items"]):
        return None
    picked = _pick_next(session, items)
    if not picked:
        return None
    lesson_key, question = picked
    seq = len(items) + 1
    knowledge = list(knowledge_for(lesson_key, question))
    with db.connect() as conn:
        conn.execute(
            """INSERT INTO adaptive_session_items(session_id,seq,lesson_key,question_id,difficulty,knowledge_json,created_at)
               VALUES(?,?,?,?,?,?,?)""",
            (session["id"], seq, lesson_key, question.id, difficulty_for(question), json.dumps(knowledge, ensure_ascii=False), now_iso()),
        )
    return _items(int(session["id"]))[-1]


def _finish_session(session: dict[str, Any]) -> int:
    if session.get("exam_attempt_id"):
        return int(session["exam_attempt_id"])
    items = [x for x in _items(int(session["id"])) if x.get("answer_json") is not None and x.get("question")]
    if not items:
        raise HTTPException(409, "Adaptive session has no answered items")
    selected = [(str(x["lesson_key"]), x["question"]) for x in items]
    attempt_id = _create_attempt(
        lesson_key="adaptive-test", lang=str(session["language"]), mode="adaptive-sequential", scope_key="adaptive-test",
        title_zh="逐题自适应能力测试", title_en="Sequential Adaptive Assessment", selected=selected,
        pass_score=80, seed=int(session["seed"]),
    )
    answers = {str(x["question_id"]): x["answer"] for x in items}
    attempt = _attempt(attempt_id)
    if not attempt:
        raise HTTPException(500, "Failed to create assessment attempt")
    _save_submission(attempt, answers, _selected_questions(attempt_id))
    with db.connect() as conn:
        conn.execute("UPDATE adaptive_sessions SET status='completed',completed_at=?,exam_attempt_id=? WHERE id=?", (now_iso(), attempt_id, session["id"]))
    return attempt_id


@router.get("/adaptive-test", response_class=HTMLResponse)
def adaptive_test_home(request: Request):
    lang = _lang(request)
    profile = mastery_profile()
    c = _nav(request, lang)
    c.update({"targets": _default_targets(profile), "profile": profile})
    return templates.TemplateResponse(request=request, name="adaptive_test_home.html", context=c)


@router.post("/adaptive-test/start")
def start_adaptive_test(request: Request):
    lang = _lang(request)
    targets = _default_targets(mastery_profile())
    if not targets:
        raise HTTPException(409, "Question bank has no target knowledge tags")
    seed = secrets.randbits(31)
    with db.connect() as conn:
        cur = conn.execute(
            """INSERT INTO adaptive_sessions(language,status,target_tags_json,max_items,seed,started_at)
               VALUES(?,?,?,?,?,?)""",
            (lang, "started", json.dumps(targets, ensure_ascii=False), 12, seed, now_iso()),
        )
        session_id = int(cur.lastrowid)
    return RedirectResponse(f"/adaptive-test/{session_id}", status_code=303)


@router.get("/adaptive-test/{session_id}", response_class=HTMLResponse)
def adaptive_test_take(request: Request, session_id: int):
    session = _session(session_id)
    if not session:
        raise HTTPException(404)
    if session["status"] == "completed" and session.get("exam_attempt_id"):
        return RedirectResponse(f"/exam-v2/attempt/{session['exam_attempt_id']}/result", status_code=303)
    pending = _ensure_pending(session)
    if not pending:
        attempt_id = _finish_session(session)
        return RedirectResponse(f"/exam-v2/attempt/{attempt_id}/result", status_code=303)
    question = pending.get("question")
    if not question:
        raise HTTPException(500, "Question is missing from bank")
    lang = str(session["language"])
    items = _items(session_id)
    c = _nav(request, lang)
    c.update({
        "session": session,
        "item": pending,
        "question": _question_view({**pending, "question": question}, lang),
        "answered_count": sum(1 for x in items if x.get("answer_json") is not None),
        "tag_state": _session_tag_state(session, items),
    })
    return templates.TemplateResponse(request=request, name="adaptive_test.html", context=c)


@router.post("/adaptive-test/{session_id}/answer")
async def adaptive_test_answer(request: Request, session_id: int):
    session = _session(session_id)
    if not session or session["status"] != "started":
        raise HTTPException(409, "Adaptive session is not active")
    pending = next((x for x in _items(session_id) if x.get("answer_json") is None), None)
    if not pending or not pending.get("question"):
        raise HTTPException(409, "No active adaptive item")
    q: Question = pending["question"]
    form = await request.form()
    name = f"q_{q.id}"
    answer: Any = list(form.getlist(name)) if q.kind == "multiple" else str(form.get(name, ""))
    detail = grade_question(q, answer)
    max_points = float(detail.get("max_points") or q.points or 0)
    score_percent = round(float(detail.get("earned") or 0) / max_points * 100, 2) if max_points else 0.0
    with db.connect() as conn:
        conn.execute(
            "UPDATE adaptive_session_items SET answer_json=?,score_percent=?,answered_at=? WHERE id=?",
            (json.dumps(answer, ensure_ascii=False), score_percent, now_iso(), pending["id"]),
        )
    session = _session(session_id)
    answered = [x for x in _items(session_id) if x.get("answer_json") is not None]
    if len(answered) >= int(session["max_items"]):
        attempt_id = _finish_session(session)
        return RedirectResponse(f"/exam-v2/attempt/{attempt_id}/result", status_code=303)
    return RedirectResponse(f"/adaptive-test/{session_id}", status_code=303)
