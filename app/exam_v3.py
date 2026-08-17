from __future__ import annotations

import json
import os
import secrets
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from .course import LESSON_MAP
from .db import now_iso
from .exam_system import EXAMS, Question
from .exam_v2 import (
    STAGE_MAP,
    _attempt,
    _choose_balanced,
    _choose_stage,
    _create_attempt,
    _lang,
    _latest_question_state,
    _nav,
    _question_view,
    _save_submission,
    _selected_questions,
    bank_for,
    db,
    templates,
)
from .i18n import normalize_lang

router = APIRouter()


def _duration_seconds(mode: str) -> int:
    defaults = {"weekly": 30, "stage": 50, "mistakes": 20}
    env = {
        "weekly": "LLM_EXAM_WEEKLY_MINUTES",
        "stage": "LLM_EXAM_STAGE_MINUTES",
        "mistakes": "LLM_EXAM_MISTAKE_MINUTES",
    }
    try:
        minutes = int(os.getenv(env.get(mode, ""), str(defaults.get(mode, 30))))
    except ValueError:
        minutes = defaults.get(mode, 30)
    return max(5, min(minutes, 180)) * 60


def init_tables() -> None:
    with db.connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS exam_runtime(
                attempt_id INTEGER PRIMARY KEY,
                duration_seconds INTEGER NOT NULL,
                deadline_at TEXT NOT NULL,
                draft_json TEXT NOT NULL DEFAULT '{}',
                last_saved_at TEXT,
                auto_submitted INTEGER NOT NULL DEFAULT 0
            );
            """
        )


init_tables()


def _iso_now() -> datetime:
    return datetime.fromisoformat(now_iso())


def _ensure_runtime(attempt: dict[str, Any]) -> dict[str, Any]:
    with db.connect() as conn:
        row = conn.execute("SELECT * FROM exam_runtime WHERE attempt_id=?", (attempt["id"],)).fetchone()
        if row:
            return dict(row)
        started = datetime.fromisoformat(attempt["started_at"])
        duration = _duration_seconds(attempt.get("mode") or "weekly")
        deadline = (started + timedelta(seconds=duration)).isoformat(timespec="seconds")
        conn.execute(
            "INSERT INTO exam_runtime(attempt_id,duration_seconds,deadline_at,draft_json) VALUES(?,?,?,?)",
            (attempt["id"], duration, deadline, "{}"),
        )
    return {"attempt_id": attempt["id"], "duration_seconds": duration, "deadline_at": deadline, "draft_json": "{}", "last_saved_at": None, "auto_submitted": 0}


def _remaining(runtime: dict[str, Any]) -> int:
    deadline = datetime.fromisoformat(runtime["deadline_at"])
    return max(0, int((deadline - _iso_now()).total_seconds()))


def _draft(runtime: dict[str, Any]) -> dict[str, Any]:
    try:
        value = json.loads(runtime.get("draft_json") or "{}")
        return value if isinstance(value, dict) else {}
    except json.JSONDecodeError:
        return {}


def _save_draft(attempt_id: int, answers: dict[str, Any]) -> None:
    with db.connect() as conn:
        conn.execute(
            "UPDATE exam_runtime SET draft_json=?,last_saved_at=? WHERE attempt_id=?",
            (json.dumps(answers, ensure_ascii=False), now_iso(), attempt_id),
        )


def _normalise_answers(selected: list[dict[str, Any]], payload: dict[str, Any]) -> dict[str, Any]:
    answers: dict[str, Any] = {}
    for item in selected:
        q: Question = item["question"]
        value = payload.get(q.id, [] if q.kind == "multiple" else "")
        if q.kind == "multiple":
            answers[q.id] = value if isinstance(value, list) else [str(value)] if value else []
        else:
            answers[q.id] = str(value or "")
    return answers


def _auto_submit(attempt: dict[str, Any], runtime: dict[str, Any]) -> None:
    if attempt["status"] == "submitted":
        return
    selected = _selected_questions(attempt["id"])
    answers = _normalise_answers(selected, _draft(runtime))
    _save_submission(attempt, answers, selected)
    with db.connect() as conn:
        conn.execute("UPDATE exam_runtime SET auto_submitted=1 WHERE attempt_id=?", (attempt["id"],))


def _create_runtime_attempt(*, lesson_key: str, lang: str, mode: str, scope_key: str, title_zh: str, title_en: str, selected, pass_score: int, seed: int) -> int:
    attempt_id = _create_attempt(
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
    attempt = _attempt(attempt_id)
    if attempt:
        _ensure_runtime(attempt)
    return attempt_id


@router.post("/exams/{lesson_key}/random-start")
def start_random_weekly(request: Request, lesson_key: str):
    if lesson_key not in EXAMS:
        raise HTTPException(404)
    lang = _lang(request)
    lesson = LESSON_MAP[lesson_key]
    seed = secrets.randbits(31)
    pool = [(lesson_key, q) for q in bank_for(lesson_key)]
    target = 8 if lesson_key == "week00" else min(6, len(pool))
    selected = _choose_balanced(pool, target, seed)
    attempt_id = _create_runtime_attempt(
        lesson_key=lesson_key,
        lang=lang,
        mode="weekly",
        scope_key=lesson_key,
        title_zh=f"Week {lesson.week} 随机周测",
        title_en=f"Week {lesson.week} Randomized Exam",
        selected=selected,
        pass_score=EXAMS[lesson_key].pass_score,
        seed=seed,
    )
    return RedirectResponse(f"/exam-v2/attempt/{attempt_id}", status_code=303)


@router.post("/stage-exams/{stage_key}/start")
def start_stage_exam(request: Request, stage_key: str):
    stage = STAGE_MAP.get(stage_key)
    if not stage:
        raise HTTPException(404)
    lang = _lang(request)
    seed = secrets.randbits(31)
    attempt_id = _create_runtime_attempt(
        lesson_key=stage.key,
        lang=lang,
        mode="stage",
        scope_key=stage.key,
        title_zh=stage.zh,
        title_en=stage.en,
        selected=_choose_stage(stage, seed),
        pass_score=stage.pass_score,
        seed=seed,
    )
    return RedirectResponse(f"/exam-v2/attempt/{attempt_id}", status_code=303)


@router.post("/mistakes/start")
def start_mistake_practice(request: Request):
    lang = _lang(request)
    rows = _latest_question_state()[:10]
    if not rows:
        return RedirectResponse("/mistakes", status_code=303)
    seed = secrets.randbits(31)
    selected = [(x["lesson_key"], x["question"]) for x in rows]
    attempt_id = _create_runtime_attempt(
        lesson_key="mistakes",
        lang=lang,
        mode="mistakes",
        scope_key="mistakes",
        title_zh="错题专项复习",
        title_en="Mistake Review Practice",
        selected=selected,
        pass_score=80,
        seed=seed,
    )
    return RedirectResponse(f"/exam-v2/attempt/{attempt_id}", status_code=303)


@router.get("/exam-v2/attempt/{attempt_id}", response_class=HTMLResponse)
def take_timed_exam(request: Request, attempt_id: int):
    attempt = _attempt(attempt_id)
    if not attempt or not attempt.get("mode"):
        raise HTTPException(404)
    if attempt["status"] == "submitted":
        return RedirectResponse(f"/exam-v2/attempt/{attempt_id}/result", status_code=303)
    runtime = _ensure_runtime(attempt)
    if _remaining(runtime) <= 0:
        _auto_submit(attempt, runtime)
        return RedirectResponse(f"/exam-v2/attempt/{attempt_id}/result", status_code=303)
    lang = normalize_lang(attempt["language"])
    selected = _selected_questions(attempt_id)
    c = _nav(request, lang)
    c.update(
        {
            "attempt": attempt,
            "exam_title": attempt["title_en"] if lang == "en" else attempt["title_zh"],
            "questions": [_question_view(x, lang) for x in selected],
            "draft": _draft(runtime),
            "remaining_seconds": _remaining(runtime),
            "last_saved_at": runtime.get("last_saved_at"),
        }
    )
    return templates.TemplateResponse(request=request, name="exam_v3_attempt.html", context=c)


@router.post("/exam-v2/attempt/{attempt_id}/submit")
async def submit_timed_exam(request: Request, attempt_id: int):
    attempt = _attempt(attempt_id)
    if not attempt or not attempt.get("mode"):
        raise HTTPException(404)
    if attempt["status"] == "submitted":
        return RedirectResponse(f"/exam-v2/attempt/{attempt_id}/result", status_code=303)
    runtime = _ensure_runtime(attempt)
    selected = _selected_questions(attempt_id)
    if _remaining(runtime) <= 0:
        _auto_submit(attempt, runtime)
    else:
        form = await request.form()
        payload: dict[str, Any] = {}
        for item in selected:
            q: Question = item["question"]
            name = f"q_{q.id}"
            payload[q.id] = list(form.getlist(name)) if q.kind == "multiple" else str(form.get(name, ""))
        answers = _normalise_answers(selected, payload)
        _save_draft(attempt_id, answers)
        _save_submission(attempt, answers, selected)
    return RedirectResponse(f"/exam-v2/attempt/{attempt_id}/result", status_code=303)


@router.post("/exam-runtime/{attempt_id}/autosave")
async def autosave(attempt_id: int, request: Request):
    attempt = _attempt(attempt_id)
    if not attempt or attempt["status"] != "started":
        raise HTTPException(409, "Attempt is not active")
    runtime = _ensure_runtime(attempt)
    if _remaining(runtime) <= 0:
        _auto_submit(attempt, runtime)
        return JSONResponse({"status": "expired", "redirect": f"/exam-v2/attempt/{attempt_id}/result"}, status_code=409)
    try:
        body = await request.json()
    except Exception:
        body = {}
    selected = _selected_questions(attempt_id)
    answers = _normalise_answers(selected, body.get("answers", {}) if isinstance(body, dict) else {})
    _save_draft(attempt_id, answers)
    return {"status": "saved", "saved_at": now_iso(), "remaining_seconds": _remaining(runtime)}


@router.post("/exam-runtime/{attempt_id}/expire")
def expire_attempt(attempt_id: int):
    attempt = _attempt(attempt_id)
    if not attempt:
        raise HTTPException(404)
    runtime = _ensure_runtime(attempt)
    if attempt["status"] != "submitted":
        _auto_submit(attempt, runtime)
    return {"status": "submitted", "redirect": f"/exam-v2/attempt/{attempt_id}/result"}


@router.get("/exam-runtime/{attempt_id}/state")
def runtime_state(attempt_id: int):
    attempt = _attempt(attempt_id)
    if not attempt:
        raise HTTPException(404)
    runtime = _ensure_runtime(attempt)
    return {
        "status": attempt["status"],
        "remaining_seconds": _remaining(runtime),
        "last_saved_at": runtime.get("last_saved_at"),
        "auto_submitted": bool(runtime.get("auto_submitted")),
    }
